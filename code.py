import pulp
from collections import defaultdict
import itertools

# تعریف در ها
courses = {
    'ریاضی1': {'inputs': [1401, 1402], 'sections_needed': 2, 'group': 'ریاضی', 'units': 3},
    'منطق': {'inputs': [1401], 'sections_needed': 1, 'group': 'ریاضی', 'units': 3},
    'برنامه_نویسی': {'inputs': [1401, 1402], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 4}
}

# نعریف استاد ها با اسلات های زمانی مخصوص به خودشون
professors = {
    'استادA': {
        'group': 'هیات_علمی',
        'teachable_courses': ['ریاضی1', 'منطق'],
        'available_times': [(0, 8, 10), (0, 10, 12), (1, 8, 10), (1, 10, 12), (2, 8, 10)],  # اضافه کردن زمان‌ها
        'section_range': (1, 2)
    },
    'استادB': {
        'group': 'مدعو',
        'teachable_courses': ['برنامه_نویسی'],
        'available_times': [(1, 10, 12), (2, 8, 10), (2, 10, 12), (3, 8, 10), (3, 10, 12)],  # اضافه کردن زمان‌ها
        'section_range': (2, 2)
    },
    'استادC': {
        'group': 'هیات_علمی',
        'teachable_courses': ['ریاضی1', 'منطق'],
        'available_times': [(1, 8, 10), (2, 8, 10), (2, 10, 12), (3, 8, 10)],  # اضافه کردن زمان‌ها
        'section_range': (1, 3)
    }
}

# رنج روی های هفته
days = range(6)

# محدودیت‌های خاص (فعال میکنم یا غیر فعال)
prefer_consecutive_guest = True # کلاس استاد های مدعو ترجیجا پشت سر هم میشن
prefer_consecutive_faculty = True # مثل مدعو ولی برای هیئت علمی
avoid_two_sections_same_day = True # سعی میکنه دو سکشن یه درس تو یه روز نباشه
no_overlap_same_input = True # درس های یک ورودی رو همزمان نمیذاره
prefer_same_day_for_input = True # تا جای ممکن درس های یک ورودی رو توی یه روز میچینه
max_units = 17  # حداکثر واحد های مجاز تو برنامه کلاسی


# تابع چک کردن تداخل زمانی
# تاپل زمان میگیره
def has_overlap(time1, time2):
    day1, start1, end1 = time1
    day2, start2, end2 = time2
    if day1 != day2:
        return False
    return not (end1 <= start2 or end2 <= start1)

"""
section_instances = []
for course, data in courses.items():
    for sec_id in range(data['sections_needed']):
        section_instances.append([course, sec_id])
"""
# جمع‌آوری سکشنا (تاپلی)
# مثلاً برای "ریاضی1" که 2 سکشن نیاز داره، (ریاضی1, 0) و (ریاضی1, 1) به لیست اضافه میشه.
section_instances = []
for course, data in courses.items():
    for sec_id in range(data['sections_needed']):
        section_instances.append((course, sec_id))

# تعریف مدل بهینه سازی تو pulp
model = pulp.LpProblem("University_Scheduling", pulp.LpMinimize)

# متغیرا
assign_vars = {}
for sec in section_instances:
    course, sec_id = sec
    for prof, prof_data in professors.items():
        if course in prof_data['teachable_courses']:
            for time in prof_data['available_times']:
                assign_vars[(sec, prof, time)] = pulp.LpVariable(
                    f"assign_{course}_{sec_id}_{prof}_{time[0]}_{time[1]}_{time[2]}", cat='Binary')
"""
for sec in section_instances:
    valid_assignments = []
    for prof in professors:
        for time in professors[prof]['available_times']:
            if (sec, prof, time) in assign_vars:
                valid_assignments.append(assign_vars[(sec, prof, time)])
    model += pulp.lpSum(valid_assignments) == 1
"""
# محدودیت : هر سکشن دقیقا برای یک استاد و زمان
for sec in section_instances:
    model += pulp.lpSum(
        assign_vars[(sec, prof, time)] for prof in professors for time in professors[prof]['available_times'] if
        (sec, prof, time) in assign_vars) == 1
# روش بهینه تر حلقه (تست کنم بعدا)
"""
for sec in section_instances:
    model += pulp.lpSum(assign_vars[key] for key in assign_vars if key[0] == sec) == 1
"""
# محدودیت: تعداد سکشن‌های استاد
# متغیر های باینری تخصیصش باید تو بازه مین و ماکسش باشه. همون حداقل و حداکثر  تعداد سکشن های تدریس استاد
for prof, data in professors.items():
    min_sec, max_sec = data['section_range']
    model += pulp.lpSum(
        assign_vars[(sec, prof, time)] for sec in section_instances for time in data['available_times'] if
        (sec, prof, time) in assign_vars) >= min_sec
    model += pulp.lpSum(
        assign_vars[(sec, prof, time)] for sec in section_instances for time in data['available_times'] if
        (sec, prof, time) in assign_vars) <= max_sec

# محدودیت: حداکثر واحد
total_units = pulp.lpSum(
    assign_vars[(sec, prof, time)] * courses[sec[0]]['units'] for sec in section_instances for prof in professors for
    time in professors[prof]['available_times'] if (sec, prof, time) in assign_vars)
model += total_units <= max_units

# محدودیت: عدم تداخل برای استاد
for prof in professors:
    all_possible = [(sec, time) for sec in section_instances for time in professors[prof]['available_times'] if
                    (sec, prof, time) in assign_vars]
    for (sec1, time1), (sec2, time2) in itertools.combinations(all_possible, 2):
        if has_overlap(time1, time2):
            model += assign_vars[(sec1, prof, time1)] + assign_vars[(sec2, prof, time2)] <= 1

# محدودیت: عدم تداخل برای درس‌های یک ورودی
if no_overlap_same_input:
    input_courses = defaultdict(list)
    for course, data in courses.items():
        for inp in data['inputs']:
            input_courses[inp].append(course)

    for inp, inp_courses in input_courses.items():
        inp_sections = [sec for sec in section_instances if sec[0] in inp_courses] #برای هر ورودی، تمام سکشن ‌های درس‌ های اون ورودی جمع‌آوری میشن
        for (sec1, prof1, time1), (sec2, prof2, time2) in itertools.product(assign_vars.keys(), repeat=2):
            if sec1[0] in inp_courses and sec2[0] in inp_courses and sec1 != sec2 and has_overlap(time1, time2):
                model += assign_vars[(sec1, prof1, time1)] + assign_vars[(sec2, prof2, time2)] <= 1
#اگه دو سکشن از درس‌های یه ورودی هم‌زمان باشن (has_overlap) و سکشن‌ها متفاوت باشن (sec1 != sec2)، جمع متغیرهای باینریشون باید حداکثر 1 باشه.

# محدودیت: تمام سکشن‌های یک درس باید توسط یک استاد تدریس شوند
prof_assignment = {}
for course in courses:
    for prof in professors:
        if course in professors[prof]['teachable_courses']:
            prof_assignment[(course, prof)] = pulp.LpVariable(f"prof_assign_{course}_{prof}", cat='Binary')

# محدودیت: هر درس دقیقاً به یک استاد تخصیص داده شود
for course in courses:
    model += pulp.lpSum(
        prof_assignment[(course, prof)] for prof in professors if (course, prof) in prof_assignment
    ) == 1

# محدودیت: تخصیص سکشن‌ها به همان استاد انتخاب‌شده
for course in courses:
    if courses[course]['sections_needed'] > 1:  # فقط برای درس‌هایی که چند سکشن دارند
        for prof in professors:
            if course in professors[prof]['teachable_courses']:
                for sec_id in range(courses[course]['sections_needed']):
                    sec = (course, sec_id)
                    model += pulp.lpSum(
                        assign_vars[(sec, prof, time)] for time in professors[prof]['available_times']
                        if (sec, prof, time) in assign_vars
                    ) <= prof_assignment[(course, prof)] * courses[course]['sections_needed']

# محدودیت: دو سکشن یک درس در یک روز
if avoid_two_sections_same_day:
    for course, data in courses.items(): #برای درس‌هایی که بیش از یه سکشن دارن (مثل ریاضی1 با 2 سکشن)، یه متغیر باینری day_usage برای هر روز تعریف می‌شه.
        if data['sections_needed'] > 1:
            course_secs = [(course, i) for i in range(data['sections_needed'])]
            for day in days:
                day_usage = pulp.LpVariable(f"day_usage_{course}_{day}", cat='Binary') # متغیر ینی آیا حداقل یه سکشن تو این روز قرار داره یا نه.
                model += day_usage >= pulp.lpSum(
                    assign_vars[(sec, prof, time)] for sec in course_secs for prof in professors for time in
                    professors[prof]['available_times'] if (sec, prof, time) in assign_vars and time[0] == day) / data[
                             'sections_needed']
                model += pulp.lpSum(
                    assign_vars[(sec, prof, time)] for sec in course_secs for prof in professors for time in
                    professors[prof]['available_times'] if (sec, prof, time) in assign_vars and time[0] == day) <= 1 + (
                                     1 - day_usage) * 100 #big-M method

# بهینه‌سازی: حداقل کردن تعداد روزهای استفاده‌شده
penalty = 0
if prefer_consecutive_guest or prefer_consecutive_faculty:
    for prof, data in professors.items():
        if (data['group'] == 'مدعو' and prefer_consecutive_guest) or (
                data['group'] == 'هیات_علمی' and prefer_consecutive_faculty):
            days_used = {day: pulp.LpVariable(f"days_used_{prof}_{day}", cat='Binary') for day in days}
            for day in days:
                model += days_used[day] >= pulp.lpSum(
                    assign_vars[(sec, prof, time)] for sec in section_instances for time in data['available_times'] if
                    (sec, prof, time) in assign_vars and time[0] == day) / 100
            penalty += pulp.lpSum(days_used.values()) * 10

# بهینه‌سازی: درس‌های یک ورودی در یک روز
if prefer_same_day_for_input:
    for inp, inp_courses in input_courses.items():
        if len(inp_courses) > 1:
            days_used_inp = {day: pulp.LpVariable(f"days_used_inp_{inp}_{day}", cat='Binary') for day in days}
            for day in days:
                valid_assignments = []
                for course in inp_courses:
                    for i in range(courses[course]['sections_needed']):
                        sec = (course, i)
                        for prof in professors:
                            if course in professors[prof]['teachable_courses']:
                                for time in professors[prof]['available_times']:
                                    if time[0] == day and (sec, prof, time) in assign_vars:
                                        valid_assignments.append(assign_vars[(sec, prof, time)])
                if valid_assignments:
                    model += days_used_inp[day] >= pulp.lpSum(valid_assignments) / 100
                else:
                    model += days_used_inp[day] >= 0
            penalty += pulp.lpSum(days_used_inp.values()) * 5

# هدف: حداقل کردن پنالتی
model += penalty

# حل مدل با دیباگ
status = model.solve(pulp.PULP_CBC_CMD(msg=1))

# خروجی با دیباگ
if status == pulp.LpStatusOptimal:
    print("برنامه بهینه یافت شد:")
    total_units = 0
    schedule = defaultdict(list)
    day_names = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']
    for var in assign_vars:
        if assign_vars[var].varValue == 1:
            (course, sec_id), prof, (day, start, end) = var
            total_units += courses[course]['units']
            schedule[prof].append((day, start, end, course, sec_id))

    for prof in schedule:
        print(f"\nبرنامه استاد {prof}:")
        for day, start, end, course, sec_id in sorted(schedule[prof]):
            print(f"  درس {course} (سکشن {sec_id + 1}) - {day_names[day]} {start}-{end}")

    print(f"\nمجموع واحدهای برنامه: {total_units}")
    for inp in input_courses:
        days_used = set()
        for var in assign_vars:
            if assign_vars[var].varValue == 1:
                (course, sec_id), _, (day, _, _) = var
                if course in input_courses[inp]:
                    days_used.add(day)
        print(f"ورودی {inp}: کلاس در {len(days_used)} روز ({[day_names[d] for d in sorted(days_used)]})")
else:
    print("هیچ برنامه‌ای یافت نشد. محدودیت‌ها را چک کنید.")
    print(f"وضعیت مدل: {pulp.LpStatus[status]}")
    # دیباگ: بررسی محدودیت‌ها
    print("چک کردن محدودیت‌های ورودی:")
    print(f"مجموع واحدها: {sum(data['sections_needed'] * data['units'] for data in courses.values())}")
    print(f"حداکثر واحد مجاز: {max_units}")
    for prof, data in professors.items():
        print(
            f"استاد {prof}: {data['section_range'][0]} تا {data['section_range'][1]} سکشن، درس‌های قابل ارائه: {data['teachable_courses']}")