#!/usr/bin/env python3
from datetime import datetime, timedelta
import re

INPATH = 'data/T2/leads2.csv'
OUTPATH = INPATH
TARGET = 1000

first = ['Александр','Дмитрий','Максим','Иван','Сергей','Андрей','Алексей','Артём','Михаил','Никита',
         'Роман','Егор','Павел','Тимофей','Владислав','Денис','Константин','Виктор','Олег','Илья',
         'Владимир','Мария','Елена','Анна','Ольга','Наталья','Татьяна','Юлия','Светлана','Ксения',
         'Виктория','Анастасия','Полина','Людмила','Галина','Марина','Ирина','Зоя','София','Лидия']
last = ['Иванов','Смирнов','Кузнецов','Попов','Васильев','Петров','Соколов','Михайлов','Новиков','Фёдоров',
        'Морозов','Волков','Алексеев','Лебедев','Семёнов','Егоров','Павлов','Козлов','Степанов','Николаев',
        'Орлов','Антонов','Тихонов','Беляев','Зайцев','Киселёв','Григорьев','Денисов','Мартынов','Ершов',
        'Крылов','Воробьёв','Котов','Беляков','Савельев','Макаров','Овчинников','Романов','Борисов','Медведев']
statuses = ['new','qualified','proposal','won','lost']

# basic transliteration for names used in emails
tr = {
    'А':'A','а':'a','Б':'B','б':'b','В':'V','в':'v','Г':'G','г':'g','Д':'D','д':'d','Е':'E','е':'e',
    'Ё':'E','ё':'e','Ж':'Zh','ж':'zh','З':'Z','з':'z','И':'I','и':'i','Й':'Y','й':'y','К':'K','к':'k',
    'Л':'L','л':'l','М':'M','м':'m','Н':'N','н':'n','О':'O','о':'o','П':'P','п':'p','Р':'R','р':'r',
    'С':'S','с':'s','Т':'T','т':'t','У':'U','у':'u','Ф':'F','ф':'f','Х':'Kh','х':'kh','Ц':'Ts','ц':'ts',
    'Ч':'Ch','ч':'ch','Ш':'Sh','ш':'sh','Щ':'Shch','щ':'shch','Ы':'Y','ы':'y','Э':'E','э':'e','Ю':'Yu','ю':'yu','Я':'Ya','я':'ya',
    'ь':'','Ь':'','ъ':'','Ъ':''
}

def translit(s):
    return ''.join(tr.get(ch, ch) for ch in s).lower()

# read existing file
with open(INPATH, 'r', encoding='utf-8') as f:
    lines = [l.rstrip('\n') for l in f]

header = lines[0]
rows = lines[1:]

# find last id
max_id = 0
id_re = re.compile(r'^0*([0-9]+)')
for r in rows:
    if not r.strip():
        continue
    parts = r.split(',')
    if len(parts) < 1:
        continue
    m = id_re.match(parts[0].strip())
    if m:
        val = int(m.group(1))
        if val > max_id:
            max_id = val

start = max_id + 1
if start > TARGET:
    print('Already at or above target ({}). Nothing to do.'.format(TARGET))
    raise SystemExit(0)

base_dt = datetime(2026,3,5,6,0,0)

new_lines = []
for i in range(start, TARGET+1):
    idx = i
    id_str = f"{idx:016d}"
    fn = first[(idx-1) % len(first)]
    ln = last[(idx-1) % len(last)]
    phone = f"+799900{idx%1000:03d}0"
    email = f"{translit(fn)}.{translit(ln)}{idx}@nomail.test"
    stage = statuses[idx % len(statuses)]
    src = f"{(idx % 20) + 1:08d}"
    mgr = src
    created = base_dt + timedelta(minutes=idx - start)
    created_s = created.strftime('%Y-%m-%dT%H:%M:%SZ')
    if stage == 'new':
        entered = created + timedelta(seconds=5)
    else:
        entered = created + timedelta(days=1)
    entered_s = entered.strftime('%Y-%m-%dT%H:%M:%SZ')
    row = f"{id_str},{fn},{ln},{phone},{email},{stage},{src},{mgr},{created_s},{entered_s}"
    new_lines.append(row)

with open(OUTPATH, 'a', encoding='utf-8') as f:
    f.write('\n'.join(new_lines) + '\n')

print(f'Appended {len(new_lines)} rows to {OUTPATH}. New max id={TARGET:016d}')
