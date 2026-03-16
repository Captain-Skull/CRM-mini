#!/usr/bin/env python3
import shutil
import re
IN='data/T2/leads2.csv'
BACKUP='data/T2/leads2.csv.bak'
shutil.copyfile(IN,BACKUP)

out_lines=[]
with open(IN,encoding='utf-8') as f:
    header=f.readline().rstrip('\n')
    out_lines.append(header)
    for l in f:
        l=l.rstrip('\n')
        if not l:
            out_lines.append(l)
            continue
        parts=l.split(',')
        phone=parts[3]
        # if phone missing one digit and starts with +799900, insert an extra 0 after prefix
        if re.match(r'^\+799900\d{4}$',phone):
            parts[3] = '+7999000' + phone[len('+799900'):]
        out_lines.append(','.join(parts))

with open(IN,'w',encoding='utf-8') as f:
    f.write('\n'.join(out_lines)+"\n")

print('Wrote fixed phones to',IN,'(backup at',BACKUP+')')
