#!/usr/bin/env python3
import csv
from datetime import datetime, timedelta

IN = 'data/T2/leads2.csv'
OUT = 'data/T2/lead_stages2.csv'

def parse_iso_z(s):
    s = s.strip()
    if not s:
        return None
    s_mod = s.replace('Z', '+00:00')
    s_mod = s_mod.replace(':60', ':59')
    try:
        return datetime.fromisoformat(s_mod)
    except Exception:
        return None

def fmt_z(dt):
    return dt.replace(microsecond=0).isoformat().replace('+00:00', 'Z')

rows = []
with open(IN, newline='', encoding='utf-8') as f:
    r = csv.reader(f)
    header = next(r, None)
    for row in r:
        if not row:
            continue
        rows.append(row)

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['leadId','stage','enteredAt','leftAt'])

    for row in rows:
        lead_id = row[0].strip()
        # stage column index based on leads.csv header expectation
        stage = row[5].strip() if len(row) > 5 else 'new'
        created_raw = row[8].strip() if len(row) > 8 else ''
        base = parse_iso_z(created_raw)
        if base is None:
            # fallback: skip problematic rows
            continue

        # We'll space stages by 1 day to ensure continuity and keep leftAt <= final enteredAt
        t_new = base
        t_qual = base + timedelta(days=1)
        t_prop = base + timedelta(days=2)
        t_final = base + timedelta(days=3)

        if stage == 'new':
            w.writerow([lead_id, 'new', fmt_z(t_new), 'null'])

        elif stage == 'qualified':
            w.writerow([lead_id, 'new', fmt_z(t_new), fmt_z(t_qual)])
            w.writerow([lead_id, 'qualified', fmt_z(t_qual), 'null'])

        elif stage == 'proposal':
            w.writerow([lead_id, 'new', fmt_z(t_new), fmt_z(t_qual)])
            w.writerow([lead_id, 'qualified', fmt_z(t_qual), fmt_z(t_prop)])
            w.writerow([lead_id, 'proposal', fmt_z(t_prop), 'null'])

        elif stage in ('won','lost'):
            w.writerow([lead_id, 'new', fmt_z(t_new), fmt_z(t_qual)])
            w.writerow([lead_id, 'qualified', fmt_z(t_qual), fmt_z(t_prop)])
            w.writerow([lead_id, 'proposal', fmt_z(t_prop), fmt_z(t_final)])
            w.writerow([lead_id, stage, fmt_z(t_final), 'null'])

        else:
            w.writerow([lead_id, 'new', fmt_z(t_new), 'null'])

print('Rebuilt', OUT)
