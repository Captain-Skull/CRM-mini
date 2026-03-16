#!/usr/bin/env python3
from pathlib import Path
import csv
from datetime import datetime, timezone
import sys
import re


def parse_dt(s):
    if s is None:
        return None
    s = s.strip()
    if s == "" or s.lower() == 'null':
        return None
    try:
        if s.endswith('Z'):
            return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(s)
    except Exception:
        return None


def load_csv(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # normalize keys and strip values
            norm = {k.strip(): (v.strip() if v is not None else v) for k, v in r.items()}
            rows.append(norm)
    return rows


def check_leads(path):
    errors = []
    leads = load_csv(path)
    ids = set()
    for i, r in enumerate(leads, start=2):
        lid = r.get('id')
        if not lid or not lid.isdigit() or len(lid) != 16:
            errors.append(f"ERROR leads.csv L{i}: id '{lid}' is not 16 digits")
        else:
            if lid in ids:
                errors.append(f"ERROR leads.csv L{i}: duplicate id {lid}")
            ids.add(lid)

        fn = r.get('firstname','')
        ln = r.get('lastname','')
        if not fn:
            errors.append(f"ERROR leads.csv L{i}: empty firstname for id {lid}")
        if not ln:
            errors.append(f"ERROR leads.csv L{i}: empty lastname for id {lid}")

        phone = r.get('phoneNumber','')
        if not re.match(r'^\+7\d{10}$', phone):
            errors.append(f"ERROR leads.csv L{i}: phone '{phone}' not match +7XXXXXXXXXX")

        email = r.get('email','')
        if '@' not in email or ' ' in email:
            errors.append(f"ERROR leads.csv L{i}: email '{email}' appears invalid")

        stage = r.get('stage','')
        if stage not in ('new','qualified','proposal','won','lost'):
            errors.append(f"ERROR leads.csv L{i}: stage '{stage}' is invalid")

        sid = r.get('sourceId','')
        if not sid.isdigit() or len(sid) != 8:
            errors.append(f"ERROR leads.csv L{i}: sourceId '{sid}' not 8 digits")

        mid = r.get('managerId','')
        if not mid.isdigit() or len(mid) != 8:
            errors.append(f"ERROR leads.csv L{i}: managerId '{mid}' not 8 digits")

        created = parse_dt(r.get('createdAt'))
        entered = parse_dt(r.get('enteredAt'))
        if created is None:
            errors.append(f"ERROR leads.csv L{i}: createdAt '{r.get('createdAt')}' not parseable")
        if entered is None:
            errors.append(f"ERROR leads.csv L{i}: enteredAt '{r.get('enteredAt')}' not parseable")
        if created and entered and entered < created:
            errors.append(f"ERROR leads.csv L{i}: enteredAt < createdAt for id {lid}")
        if created and entered and r.get('stage','') == 'new':
            delta = (entered - created).total_seconds()
            if abs(delta) > 120:  # allow up to 2 minutes
                errors.append(f"WARN leads.csv L{i}: for 'new' enteredAt differs from createdAt by {delta} seconds (id {lid})")

    return errors, leads


def check_lead_stages(path, leads_by_id):
    errors = []
    rows = load_csv(path)
    by_lead = {}
    for i, r in enumerate(rows, start=2):
        lid = r.get('leadId')
        if lid not in leads_by_id:
            errors.append(f"ERROR lead_stages.csv L{i}: leadId '{lid}' not found in leads.csv")
        stage = r.get('stage','')
        if stage not in ('new','qualified','proposal','won','lost'):
            errors.append(f"ERROR lead_stages.csv L{i}: invalid stage '{stage}' for lead {lid}")
        ent = parse_dt(r.get('enteredAt'))
        left = parse_dt(r.get('leftAt'))
        if ent is None:
            errors.append(f"ERROR lead_stages.csv L{i}: enteredAt '{r.get('enteredAt')}' not parseable for lead {lid}")
        if left is not None and ent is not None and left < ent:
            errors.append(f"ERROR lead_stages.csv L{i}: leftAt < enteredAt for lead {lid}")

        by_lead.setdefault(lid, []).append({'stage': stage, 'entered': ent, 'left': left, 'line': i})

    # Validate sequences per lead
    for lid, events in by_lead.items():
        # sort by entered time (None last)
        events.sort(key=lambda e: (e['entered'] is None, e['entered']))
        # check first is new
        if events:
            if events[0]['stage'] != 'new':
                errors.append(f"ERROR lead_stages: lead {lid} first stage is '{events[0]['stage']}' not 'new' (line {events[0]['line']})")

        # expected progression
        order = ['new', 'qualified', 'proposal', 'won_or_lost']
        stages = [e['stage'] for e in events]
        # map final stage if present
        for idx in range(len(events)-1):
            cur = events[idx]
            nex = events[idx+1]
            if cur['entered'] is None or nex['entered'] is None:
                continue
            # chronological check
            if nex['entered'] < cur['entered']:
                errors.append(f"ERROR lead_stages: lead {lid} has non-chronological enteredAt (line {cur['line']} -> {nex['line']})")
            # leftAt should be >= entered and <= next.entered
            if cur['left'] is None:
                errors.append(f"WARN lead_stages: lead {lid} stage '{cur['stage']}' at line {cur['line']} has null leftAt but next stage exists")
            else:
                if cur['left'] < cur['entered']:
                    errors.append(f"ERROR lead_stages: lead {lid} leftAt < enteredAt at line {cur['line']}")
                if cur['left'] > nex['entered']:
                    errors.append(f"ERROR lead_stages: lead {lid} leftAt ({cur['left']}) after next.entered ({nex['entered']}) lines {cur['line']}->{nex['line']}")
                gap = (nex['entered'] - cur['left']).total_seconds()
                if gap > 0 and gap > 7*24*3600:
                    errors.append(f"WARN lead_stages: lead {lid} gap between stages is >7 days ({gap} seconds) lines {cur['line']}->{nex['line']}")

        # last event should have left==None (current) or be final
        if events:
            last = events[-1]
            if last['left'] is not None:
                errors.append(f"WARN lead_stages: lead {lid} last stage '{last['stage']}' at line {last['line']} has leftAt set")

        # validate progression order roughly: stages should not go backwards
        seq = []
        for s in stages:
            if s == 'won' or s == 'lost':
                seq.append('won_or_lost')
            else:
                seq.append(s)
        # check non-decreasing index
        idx_map = {'new':0,'qualified':1,'proposal':2,'won_or_lost':3}
        prev_idx = -1
        for k, s in enumerate(seq):
            if s not in idx_map:
                continue
            if idx_map[s] < prev_idx:
                errors.append(f"ERROR lead_stages: lead {lid} stage order regression at position {k} ('{stages[k]}')")
            prev_idx = max(prev_idx, idx_map[s])

    return errors


def main():
    base = Path(__file__).parent
    leads_path = base / 'leads2.csv'
    stages_path = base / 'lead_stages2.csv'
    all_errors = []

    if not leads_path.exists():
        print(f"ERROR: {leads_path} not found")
        sys.exit(2)
    if not stages_path.exists():
        print(f"ERROR: {stages_path} not found")
        sys.exit(2)

    errs, leads = check_leads(leads_path)
    all_errors.extend(errs)
    leads_by_id = {r.get('id'): r for r in leads}

    errs2 = check_lead_stages(stages_path, leads_by_id)
    all_errors.extend(errs2)

    if all_errors:
        for e in all_errors:
            print(e)
        print(f"\nFound {len(all_errors)} issues")
        sys.exit(1)
    else:
        print("OK: no issues found")
        sys.exit(0)


if __name__ == '__main__':
    main()
