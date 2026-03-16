import csv
import random
import datetime

male_first = ["Александр", "Дмитрий", "Максим", "Иван", "Сергей", "Андрей", "Алексей", "Артём", "Михаил", "Никита", "Роман", "Егор", "Павел", "Тимофей", "Владислав", "Денис", "Константин", "Виктор", "Олег", "Илья"]
male_last = ["Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев", "Петров", "Соколов", "Михайлов", "Новиков", "Фёдоров", "Морозов", "Волков", "Алексеев", "Лебедев", "Семёнов", "Егоров", "Павлов", "Козлов", "Степанов", "Николаев"]

female_first = ["Александра", "Дарья", "Екатерина", "Мария", "Анна", "Анастасия", "Виктория", "Елизавета", "Полина", "Ксения", "Алиса", "София", "Татьяна", "Ольга", "Елена", "Наталья", "Юлия", "Ирина", "Светлана", "Марина"]
female_last = ["Иванова", "Смирнова", "Кузнецова", "Попова", "Васильева", "Петрова", "Соколова", "Михайлова", "Новикова", "Фёдорова", "Морозова", "Волкова", "Алексеева", "Лебедева", "Семёнова", "Егорова", "Павлова", "Козлова", "Степанова", "Николаева"]

def random_date(start, end):
    return start + datetime.timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def to_iso(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

leads = []
with open('data/T2/leads2.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        leads.append(row)

stagesByLead = {}
with open('data/T2/lead_stages2.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        lead_id = row['leadId']
        if lead_id not in stagesByLead:
            stagesByLead[lead_id] = []
        stagesByLead[lead_id].append(row)

# update leads
start_dt = datetime.datetime(2025, 10, 1)
end_dt = datetime.datetime(2026, 3, 1)

for lead in leads:
    is_male = random.choice([True, False])
    if is_male:
        lead['firstname'] = random.choice(male_first)
        lead['lastname'] = random.choice(male_last)
    else:
        lead['firstname'] = random.choice(female_first)
        lead['lastname'] = random.choice(female_last)
        
    lead['email'] = f"{lead['firstname'].lower()}_{lead['lastname'].lower()}{random.randint(100, 999)}@example.com"
    
    # Base created at
    created = random_date(start_dt, end_dt)
    lead['createdAt'] = to_iso(created)
    
    current_time = created
    lead_stages = stagesByLead.get(lead['id'], [])
    
    for i, stage in enumerate(lead_stages):
        stage['enteredAt'] = to_iso(current_time)
        if i < len(lead_stages) - 1:
            # Add some random time for the stage
            stage_duration = datetime.timedelta(days=random.randint(0, 14), hours=random.randint(1, 23), minutes=random.randint(1, 59))
            current_time += stage_duration
            stage['leftAt'] = to_iso(current_time)
        else:
            stage['leftAt'] = 'null'
            # The current stage of the lead
            lead['enteredAt'] = stage['enteredAt']
            
# write back
with open('data/T2/leads2.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=leads[0].keys())
    writer.writeheader()
    writer.writerows(leads)

with open('data/T2/lead_stages2.csv', 'w', encoding='utf-8', newline='') as f:
    if len(leads) > 0 and len(stagesByLead) > 0:
        first_lead = next(iter(stagesByLead.values()))[0]
        writer = csv.DictWriter(f, fieldnames=first_lead.keys())
        writer.writeheader()
        for lead_id, stages in stagesByLead.items():
            writer.writerows(stages)

print("done")
