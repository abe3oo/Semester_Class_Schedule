import pulp
import pandas as pd  # برای خروجی جدول (اختیاری)

# تعریف اسلات‌های زمانی
time_slots = [
    ("Saturday", "08-10"), ("Saturday", "10-12"), ("Saturday", "14-15:45"), ("Saturday", "15:45-17:30"),("Saturday", "17:30-19"),
    ("Sunday", "08-10"), ("Sunday", "10-12"), ("Sunday", "14-15:45"), ("Sunday", "15:45-17:30"),("Sunday", "17:30-19"),
    ("Monday", "08-10"), ("Monday", "10-12"), ("Monday", "14-15:45"), ("Monday", "15:45-17:30"),("Monday", "17:30-19"),
    ("Tuesday", "08-10"), ("Tuesday", "10-12"), ("Tuesday", "14-15:45"), ("Tuesday", "15:45-17:30"),("Tuesday", "17:30-19"),
("Wednesday", "08-10"), ("Wednesday", "10-12"), ("Wednesday", "14-15:45"), ("Wednesday", "15:45-17:30"),("Wednesday", "17:30-19"),
]
num_slots = len(time_slots)

# روزهای هفته
days = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday"]
slots_per_day = {
    "Saturday": [0, 1, 2, 3, 4],
    "Sunday": [5,6,7,8,9],
    "Monday": [10,11,12,13,14],
    "Tuesday": [15,16,17,18,19],
    "Wednesday": [20,21,22,23,24]
}

# گروه‌های درسی و دروس (ورودی شما)
# هر درس: نام، گروه (dept)، ورودی‌ها (لیست سال‌ها)، تعداد سکشن‌ها
courses = [
    {"name": "riazi1", "dept": "CS", "intakes": [1403, 1404], "sections": 2},
    {"name": "mabani_computer", "CS": "CS", "intakes": [1403, 1404], "sections": 2},
{"name": "osol_system", "dept": "CS", "intakes": [1402], "sections": 2},
{"name": "tarahi_algoritm", "dept": "CS", "intakes": [1402], "sections": 2},
{"name": "zaban_haye_barnamesazi", "dept": "CS", "intakes": [1401], "sections": 2},
{"name": "behine_sazi", "dept": "CS", "intakes": [1401], "sections": 2},
    {"name": "mabani_olom", "dept": "Math", "intakes": [1404], "sections": 1},
{"name": "nazarie_adad", "dept": "Math", "intakes": [1401,1402,1403], "sections": 2},
{"name": "amar_moghadamati", "dept": "Math", "intakes": [1404], "sections": 2},
{"name": "riazi2", "dept": "Math", "intakes": [1403], "sections": 2},
{"name": "behine_sazi", "dept": "Math", "intakes": [1401,1402], "sections": 2},
{"name": "riazi1", "dept": "ES", "intakes": [1403,1404], "sections": 2},
{"name": "madar_manteghi", "dept": "ES", "intakes": [1402], "sections": 2},
{"name": "zaban_takhasosi", "dept": "ES", "intakes": [1401], "sections": 2},
{"name": "fizik1", "dept": "ES", "intakes": [1404], "sections": 2},
{"name": "riazi_gosaste", "dept": "ES", "intakes": [1403], "sections": 2},
{"name": "mabahes_vijeh", "dept": "ES", "intakes": [1402], "sections": 2},
{"name": "madar_electeriki", "dept": "ES", "intakes": [1401], "sections": 2},
    # درس‌های بیشتر اضافه کن، مثلاً:
    # {"name": "Physics", "dept": "Physics", "intakes": [1401], "sections": 2},
]

# تولید لیست سکشن‌ها
sections = []
section_to_course = {}
section_to_intakes = {}
for course in courses:
    for sec_num in range(1, course["sections"] + 1):
        sec_id = f"{course['name']}_{sec_num}"
        sections.append(sec_id)
        section_to_course[sec_id] = course["name"]
        section_to_intakes[sec_id] = course["intakes"]

num_sections = len(sections)

# اساتید (ورودی شما)
# هر استاد: گروه ('Guest' یا 'Faculty')، درس‌های قابل ارائه، اسلات‌های مجاز، min/max سکشن‌ها
professors = {
    "ProfA1": {"group": "Faculty", "courses": ["mabani_mantegh", "mabani_matris", "jabr_khati","mabani_tarkibiat","mabani_moghadamati","jabr","nazarie_adad"], "slots": [0, 1, 3, 4], "min_sections": 1, "max_sections": 3},
"ProfA2": {"group": "Faculty", "courses": ["mabani_moghadamati", "sakhteman_dadeh", "jabr_khati","mabani_tarkibiat"], "slots": [0, 1, 3, 4], "min_sections": 1, "max_sections": 3},
"ProfA3": {"group": "Faculty", "courses": ["mabani_computer", "tarahi_algoritm", "madar_manteghi","signal","barnamesazi_pishrafteh"], "slots": [0, 1, 3, 4], "min_sections": 1, "max_sections": 3},
    "ProfB": {"group": "Guest", "courses": ["Logic", "Math1"], "slots": [6, 7, 8], "min_sections": 3, "max_sections": 3},
    "ProfC": {"group": "Faculty", "courses": ["Matrix"], "slots": [0, 1, 2, 3, 4, 5], "min_sections": 2, "max_sections": 4},
    # استادهای بیشتر اضافه کن
}
prof_list = list(professors.keys())

# فاصله بین اسلات‌ها
distance = {}
for day in days:
    day_slots = slots_per_day[day]
    for s1 in day_slots:
        for s2 in day_slots:
            if s1 == s2:
                distance[(s1, s2)] = 0
            elif abs(day_slots.index(s1) - day_slots.index(s2)) == 1:
                distance[(s1, s2)] = 0  # پشت سر هم
            else:
                distance[(s1, s2)] = 2  # فاصله زیاد

# فلگ‌های اختیاری (True برای فعال کردن)
enable_guest_consecutive = True
enable_faculty_consecutive = True
enable_no_two_sections_same_day = True
enable_intake_same_day = True

# مدل PuLP
model = pulp.LpProblem("University_Timetabling", pulp.LpMinimize)

# متغیرها: x[sec, prof, slot] = 1 اگر سکشن sec توسط prof در slot
x = pulp.LpVariable.dicts("x", [(sec, prof, slot) for sec in sections for prof in prof_list for slot in range(num_slots)], cat="Binary")

# متغیرهای کمکی برای فاصله اسلات‌ها
z_prof = pulp.LpVariable.dicts("z_prof", [(prof, day, s1, s2) for prof in prof_list for day in days for s1 in slots_per_day[day] for s2 in slots_per_day[day] if s1 < s2], lowBound=0, cat="Continuous")

# متغیرهای توزیع یکنواخت
dev_pos = pulp.LpVariable.dicts("dev_pos", range(num_slots), lowBound=0, cat="Continuous")
dev_neg = pulp.LpVariable.dicts("dev_neg", range(num_slots), lowBound=0, cat="Continuous")

# متغیرهای ترجیح ورودی در یک روز
all_intakes = set()
for sec in sections:
    all_intakes.update(section_to_intakes[sec])
w_intake_day = pulp.LpVariable.dicts("w_intake_day", [(intake, day) for intake in all_intakes for day in days], cat="Binary")

# محدودیت‌های سخت
for sec in sections:
    model += pulp.lpSum(x[sec, prof, slot] for prof in prof_list for slot in range(num_slots)) == 1, f"Assign_{sec}"

for sec in sections:
    course = section_to_course[sec]
    for prof in prof_list:
        if course not in professors[prof]["courses"]:
            for slot in range(num_slots):
                model += x[sec, prof, slot] == 0, f"NoTeach_{sec}_{prof}_{slot}"

for sec in sections:
    for prof in prof_list:
        for slot in range(num_slots):
            if slot not in professors[prof]["slots"]:
                model += x[sec, prof, slot] == 0, f"InvalidSlot_{sec}_{prof}_{slot}"

for prof in prof_list:
    for slot in range(num_slots):
        model += pulp.lpSum(x[sec, prof, slot] for sec in sections) <= 1, f"ProfNoOverlap_{prof}_{slot}"

for prof in prof_list:
    min_sec = professors[prof]["min_sections"]
    max_sec = professors[prof]["max_sections"]
    model += pulp.lpSum(x[sec, prof, slot] for sec in sections for slot in range(num_slots)) >= min_sec, f"MinSec_{prof}"
    model += pulp.lpSum(x[sec, prof, slot] for sec in sections for slot in range(num_slots)) <= max_sec, f"MaxSec_{prof}"

for intake in all_intakes:
    intake_sections = [sec for sec in sections if intake in section_to_intakes[sec]]
    for slot in range(num_slots):
        model += pulp.lpSum(x[sec, prof, slot] for sec in intake_sections for prof in prof_list) <= 1, f"NoIntakeOverlap_{intake}_{slot}"

# محدودیت‌های اختیاری
if enable_no_two_sections_same_day:
    for course in set(section_to_course.values()):
        course_sections = [sec for sec in sections if section_to_course[sec] == course]
        if len(course_sections) > 1:
            for day in days:
                model += pulp.lpSum(x[sec, prof, slot] for sec in course_sections for prof in prof_list for slot in slots_per_day[day]) <= 1, f"NoTwoSecSameDay_{course}_{day}"

for prof in prof_list:
    group = professors[prof]["group"]
    if (group == "Guest" and enable_guest_consecutive) or (group == "Faculty" and enable_faculty_consecutive):
        for day in days:
            day_slots = slots_per_day[day]
            for i in range(len(day_slots)):
                for j in range(i + 1, len(day_slots)):
                    s1 = day_slots[i]
                    s2 = day_slots[j]
                    model += z_prof[prof, day, s1, s2] >= pulp.lpSum(x[sec, prof, s1] for sec in sections) + pulp.lpSum(x[sec, prof, s2] for sec in sections) - 1
                    model += z_prof[prof, day, s1, s2] >= 0

average_load = num_sections / num_slots
for slot in range(num_slots):
    model += pulp.lpSum(x[sec, prof, slot] for sec in sections for prof in prof_list) - average_load == dev_pos[slot] - dev_neg[slot]

if enable_intake_same_day:
    for intake in all_intakes:
        intake_sections = [sec for sec in sections if intake in section_to_intakes[sec]]
        M = len(intake_sections) + 1  # Big M
        for day in days:
            sum_day = pulp.lpSum(x[sec, prof, slot] for sec in intake_sections for prof in prof_list for slot in slots_per_day[day])
            model += w_intake_day[intake, day] <= sum_day
            model += sum_day <= M * w_intake_day[intake, day]

# تابع هدف
model += (
    pulp.lpSum(z_prof[prof, day, s1, s2] * distance[(s1, s2)] * (100 if professors[prof]["group"] == "Guest" else 50)
               for prof in prof_list for day in days for s1 in slots_per_day[day] for s2 in slots_per_day[day] if s1 < s2) +
    pulp.lpSum(dev_pos[slot] + dev_neg[slot] for slot in range(num_slots)) * 20 +
    (pulp.lpSum(w_intake_day[intake, day] for intake in all_intakes for day in days) * 30 if enable_intake_same_day else 0)
)

# حل
status = model.solve(pulp.PULP_CBC_CMD(msg=1))

# خروجی
data = []
if pulp.LpStatus[status] == 'Optimal':
    print("جواب بهینه پیدا شد!")
    for sec in sections:
        for prof in prof_list:
            for slot in range(num_slots):
                if pulp.value(x[sec, prof, slot]) == 1:
                    day, time = time_slots[slot]
                    data.append({
                        "Section": sec,
                        "Course": section_to_course[sec],
                        "Intakes": section_to_intakes[sec],
                        "Professor": prof,
                        "Day": day,
                        "Time": time
                    })
    df = pd.DataFrame(data)
    print(df.to_string(index=False))
    df.to_csv("timetable.csv", index=False)
else:
    print("جواب بهینه پیدا نشد. وضعیت:", pulp.LpStatus[status])
    # اگر infeasible بود، محدودیت‌ها رو بررسی کن (مثل بازه سکشن‌ها یا اسلات‌ها)