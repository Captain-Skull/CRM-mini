#!/usr/bin/env python3
import csv
from datetime import datetime, timedelta

def parse_iso_z(s):
    s = s.strip()
    if not s:
        return None
    # normalize Z -> +00:00 and fix common invalid minute '60' to '59'
    s_mod = s.replace('Z', '+00:00')
    s_mod = s_mod.replace(':60', ':59')
    try:
        return datetime.fromisoformat(s_mod)
    except Exception:
        # as a last resort, strip timezone and parse naive, then set tzinfo implicitly
        if s_mod.endswith('+00:00'):
            s_base = s_mod[:-6]
            try:
                return datetime.fromisoformat(s_base)
            except Exception:
                return None
        return None

in_path = 'data/T2/leads2.csv'
out_path = 'data/T2/lead_stages2.csv'

with open(in_path, newline='', encoding='utf-8') as inf:
    reader = csv.reader(inf)
    header = next(reader, None)
    rows = list(reader)

with open(out_path, 'w', newline='', encoding='utf-8') as outf:
    writer = csv.writer(outf)
    writer.writerow(['leadId', 'stage', 'enteredAt', 'leftAt'])

    for r in rows:
        if not r or len(r) < 9:
            continue
        lead_id = r[0].strip()
        stage = r[5].strip()
        created_at_raw = r[8].strip()
        base_dt = parse_iso_z(created_at_raw)
        if base_dt is None:
            # fallback: write a single 'new' row with the raw timestamp
            writer.writerow([lead_id, 'new', created_at_raw, ''])
            continue

        # build timeline: new -> qualified -> proposal -> final (won|lost)
        # enteredAt spaced by 1 second each step for continuity
        t_new = base_dt
        t_qual = base_dt + timedelta(seconds=1)
        t_prop = base_dt + timedelta(seconds=2)
        t_final = base_dt + timedelta(seconds=3)

        def fmt(dt):
            return dt.isoformat().replace('+00:00', 'Z')

        if stage == 'new':
            writer.writerow([lead_id, 'new', fmt(t_new), ''])
        elif stage == 'qualified':
            writer.writerow([lead_id, 'new', fmt(t_new), fmt(t_qual)])
            writer.writerow([lead_id, 'qualified', fmt(t_qual), ''])
        elif stage == 'proposal':
            writer.writerow([lead_id, 'new', fmt(t_new), fmt(t_qual)])
            writer.writerow([lead_id, 'qualified', fmt(t_qual), fmt(t_prop)])
            writer.writerow([lead_id, 'proposal', fmt(t_prop), ''])
        elif stage in ('won', 'lost'):
            writer.writerow([lead_id, 'new', fmt(t_new), fmt(t_qual)])
            writer.writerow([lead_id, 'qualified', fmt(t_qual), fmt(t_prop)])
            writer.writerow([lead_id, 'proposal', fmt(t_prop), fmt(t_final)])
            writer.writerow([lead_id, stage, fmt(t_final), ''])
        else:
            # unknown stage -> at least keep 'new'
            writer.writerow([lead_id, 'new', fmt(t_new), ''])

print('Wrote', out_path)
