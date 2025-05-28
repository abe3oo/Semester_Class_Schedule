import pulp
import pandas as pd

# تعریف اسلات‌های زمانی
time_slots = [
    ("Saturday", "08-10"), ("Saturday", "10-12"), ("Saturday", "14-16"),
    ("Sunday", "08-10"), ("Sunday", "10-12"), ("Sunday", "14-16"),
    ("Monday", "08-10"), ("Monday", "10-12"), ("Monday", "14-16")
]

# تعریف اساتید و اسلات‌های مجاز
professors = {
    "Rezvani": [0, 1],
    "Sepasian": [0, 7],
    "Nematollahi": [0, 1, 7, 8],
    "Bakhshandeh": [2, 4, 7],
    "Firoozi": [4, 6, 7]
}

# تعریف دروس و سکشن‌ها
courses = [
    {"name": "Math", "prof": "Sepasian", "sections": 2, "dept": "CS"},
    {"name": "Fundamentals", "prof": "Nematollahi", "sections": 2, "dept": "CS"},
    {"name": "Industry", "prof": "Rezvani", "sections": 1, "dept": "CS"},
    {"name": "Database", "prof": "Bakhshandeh", "sections": 2, "dept": "CE"},
    {"name": "Circuit", "prof": "Firoozi", "sections": 2, "dept": "CE"}
]

# تبدیل دروس به لیست وظایف
tasks = []
for course in courses:
    for i in range(course["sections"]):
        tasks.append({
            "name": f"{course['name']}_{i+1}",
            "prof": course["prof"],
            "dept": course["dept"]
        })

# تعریف روزها و اسلات‌های هر روز
days = ["Saturday", "Sunday", "Monday"]
slots_per_day = {
    "Saturday": [0, 1, 2],  # 08-10, 10-12, 14-16
    "Sunday": [3, 4, 5],
    "Monday": [6, 7, 8]
}

# تعریف فاصله بین اسلات‌ها در هر روز (وزن فاصله: 0 برای پشت سر هم، 2 برای بیشتر)
distance = {}
for day in days:
    day_slots = slots_per_day[day]
    for s1 in day_slots:
        for s2 in day_slots:
            if s1 == s2:
                distance[(s1, s2)] = 0
            elif abs(day_slots.index(s1) - day_slots.index(s2)) == 1:
                distance[(s1, s2)] = 0  # پشت سر هم (مثل 08-10 و 10-12)
            else:
                distance[(s1, s2)] = 2  # فاصله زیاد (مثل 08-10 و 14-16)

# ایجاد مدل
model = pulp.LpProblem("Timetabling", pulp.LpMinimize)

# متغیرها: x[t, s] = 1 اگر وظیفه t به اسلات s تخصیص داده شده باشد
x = pulp.LpVariable.dicts("x", [(t, s) for t in range(len(tasks)) for s in range(len(time_slots))],
                          cat="Binary")

# متغیرهای کمکی برای تداخل درس‌های رشته
y = pulp.LpVariable.dicts("y", [(d, s) for d in ["CS", "CE"] for s in range(len(time_slots))],
                          lowBound=0, cat="Continuous")

# متغیرهای کمکی برای جریمه فاصله اسلات‌های استاد در هر روز
z = pulp.LpVariable.dicts("z", [(p, d, s1, s2) for p in professors for d in days
                                for s1 in slots_per_day[d] for s2 in slots_per_day[d]],
                          lowBound=0, cat="Continuous")

# متغیرهای کمکی برای انحراف توزیع (مثبت و منفی)
dev_pos = pulp.LpVariable.dicts("dev_pos", [s for s in range(len(time_slots))], lowBound=0, cat="Continuous")
dev_neg = pulp.LpVariable.dicts("dev_neg", [s for s in range(len(time_slots))], lowBound=0, cat="Continuous")

# قیود سخت
# 1. هر وظیفه دقیقاً به یک اسلات تخصیص داده شود
for t in range(len(tasks)):
    model += pulp.lpSum(x[t, s] for s in range(len(time_slots))) == 1, f"Assign_{t}"

# 2. هر استاد در هر اسلات حداکثر یک کلاس داشته باشد
for s in range(len(time_slots)):
    for prof in professors:
        model += pulp.lpSum(x[t, s] for t in range(len(tasks)) if tasks[t]["prof"] == prof) <= 1, f"Prof_{prof}_{s}"

# 3. تخصیص فقط به اسلات‌های مجاز استاد
for t in range(len(tasks)):
    prof = tasks[t]["prof"]
    for s in range(len(time_slots)):
        if s not in professors[prof]:
            model += x[t, s] == 0, f"InvalidSlot_{t}_{s}"

# قیود نرم
# 1. محاسبه تداخل درس‌های رشته
for s in range(len(time_slots)):
    for d in ["CS", "CE"]:
        model += y[d, s] >= pulp.lpSum(x[t, s] for t in range(len(tasks)) if tasks[t]["dept"] == d) - 1
        model += y[d, s] >= 0

# 2. جریمه فاصله زیاد بین اسلات‌های استاد در هر روز
for p in professors:
    for d in days:
        for s1 in slots_per_day[d]:
            for s2 in slots_per_day[d]:
                model += z[p, d, s1, s2] >= pulp.lpSum(x[t1, s1] for t1 in range(len(tasks)) if tasks[t1]["prof"] == p) + \
                                          pulp.lpSum(x[t2, s2] for t2 in range(len(tasks)) if tasks[t2]["prof"] == p) - 1
                model += z[p, d, s1, s2] >= 0

# 3. جریمه توزیع نایکنواخت: انحراف از میانگین
average_load = len(tasks) / len(time_slots)  # میانگین کلاس‌ها در هر اسلات (مثلاً 9/9 = 1)
for s in range(len(time_slots)):
    model += pulp.lpSum(x[t, s] for t in range(len(tasks))) - average_load == dev_pos[s] - dev_neg[s]

# تابع هدف: کم کردن تداخل درس‌های رشته + فاصله اسلات‌های استاد + انحراف توزیع
model += (
    pulp.lpSum(y[d, s] * 500 for d in ["CS", "CE"] for s in range(len(time_slots))) +  # جریمه تداخل رشته‌ها
    pulp.lpSum(z[p, d, s1, s2] * distance[(s1, s2)] * 50 for p in professors for d in days
               for s1 in slots_per_day[d] for s2 in slots_per_day[d]) +  # جریمه فاصله اسلات‌ها
    pulp.lpSum(dev_pos[s] + dev_neg[s] for s in range(len(time_slots))) * 20  # جریمه انحراف توزیع
), "Minimize_Objective"

# حل مدل
model.solve(pulp.PULP_CBC_CMD(msg=1))

# نمایش برنامه کلاسی
data = []
for s in range(len(time_slots)):
    slot_tasks = []
    for t in range(len(tasks)):
        if pulp.value(x[t, s]) == 1:
            slot_tasks.append(tasks[t])
    if slot_tasks:
        for task in slot_tasks:
            data.append({
                "Day": time_slots[s][0],
                "Time": time_slots[s][1],
                "Course": task["name"],
                "Professor": task["prof"],
                "Department": task["dept"]
            })
    else:
        data.append({
            "Day": time_slots[s][0],
            "Time": time_slots[s][1],
            "Course": "-",
            "Professor": "-",
            "Department": "-"
        })

df = pd.DataFrame(data)
print("\nBest Schedule (Table Format):")
print(df.to_string(index=False))

# ذخیره در فایل CSV
df.to_csv("schedule_output.csv", index=False, encoding='utf-8-sig')
print("\nSchedule saved to 'schedule_output.csv'")

# بررسی تداخل‌های رشته‌ای
conflicts = []
for s in range(len(time_slots)):
    for d in ["CS", "CE"]:
        count = sum(1 for t in range(len(tasks)) if tasks[t]["dept"] == d and pulp.value(x[t, s]) == 1)
        if count > 1:
            courses = [tasks[t]["name"] for t in range(len(tasks)) if tasks[t]["dept"] == d and pulp.value(x[t, s]) == 1]
            conflicts.append((time_slots[s], d, courses))

if conflicts:
    print("\nDepartment Conflicts:")
    for slot, dept, courses in conflicts:
        print(f"{slot}: {dept} courses {courses}")
else:
    print("\nNo Department Conflicts!")

# بررسی فاصله اسلات‌های استاد
distance_issues = []
for p in professors:
    for d in days:
        slots_used = []
        for s in slots_per_day[d]:
            if sum(1 for t in range(len(tasks)) if tasks[t]["prof"] == p and pulp.value(x[t, s]) == 1) > 0:
                slots_used.append(s)
        if len(slots_used) > 1:
            for i in range(len(slots_used)):
                for j in range(i + 1, len(slots_used)):
                    s1, s2 = slots_used[i], slots_used[j]
                    if distance[(s1, s2)] > 0:
                        distance_issues.append((p, d, time_slots[s1], time_slots[s2]))

if distance_issues:
    print("\nProfessor Slot Distance Issues:")
    for prof, day, slot1, slot2 in distance_issues:
        print(f"Professor {prof} on {day}: {slot1} and {slot2}")
else:
    print("\nNo Professor Slot Distance Issues!")