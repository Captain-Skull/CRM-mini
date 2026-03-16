#!/usr/bin/env python3
import csv

in_path = 'data/T2/lead_stages2.csv'
tmp_path = in_path + '.tmp'

with open(in_path, newline='', encoding='utf-8') as inf, open(tmp_path, 'w', newline='', encoding='utf-8') as outf:
    reader = csv.reader(inf)
    writer = csv.writer(outf)
    header = next(reader, None)
    if header:
        writer.writerow(header)
    for row in reader:
        if not row:
            continue
        # ensure row has 4 columns
        if len(row) < 4:
            row += [''] * (4 - len(row))
        if row[3].strip() == '':
            row[3] = 'null'
        writer.writerow(row)

import os
os.replace(tmp_path, in_path)
print('Filled nulls in', in_path)
