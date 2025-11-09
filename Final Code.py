import pulp
from collections import defaultdict

# ==============================================================================
# 🎯 تنظیمات مدل: محدودیت‌های سخت و اهداف نرم (Soft Constraints)
# ==============================================================================

# محدودیت‌های سخت اختیاری
SETTING_MAX_UNITS_HARD = False # حداکثر واحد مجاز برای کل برنامه (Hard Constraint)
SETTING_NO_OVERLAP_INPUT_HARD = False # عدم تداخل زمانی تمام دروس یک ورودی (توصیه: False در صورتی که فقط یک ورودی وجود دارد)
SETTING_UNIFIED_PROFESSOR_HARD = True # یک درس باید فقط توسط یک استاد تدریس شود (توصیه: True)
SETTING_DIFFERENT_DAYS_FOR_COURSE_HARD = True  # اجبار به توزیع سکشن‌های یک درس در روزهای متفاوت

# تعیین تعداد سکشن‌هایی که محدودیت توزیع روز برای آن‌ها اعمال می‌شود.
# مثال: [2] -> فقط دروس ۲ سکشنی. مثال: [2, 3] -> دروس ۲ و ۳ سکشنی.
TARGET_SECTIONS_FOR_HARD_DISTRIBUTION = [2]

# محدودیت‌های Soft (اهداف بهینه‌سازی)
SETTING_MIN_SEC_SOFT = True # تبدیل Min Sec استاد به هدف نرم (برای جلوگیری از Infeasible)
SETTING_PREFER_CONSECUTIVE_DAYS_SOFT = True # ترجیح کمترین روز کاری برای استادان
SETTING_PREFER_CONSECUTIVE_TIME_SOFT = True # ترجیح پیوستگی زمانی سکشن‌های استاد در طول روز
SETTING_PREFER_NO_CONFLICT_INPUT_SOFT = False # کاهش تداخل بین دروس یک ورودی (Soft Constraint)
SETTING_PREFER_DIFFERENT_DAYS_FOR_COURSE_SOFT = False #هدف نرم توضیع درس در روزهای مختلف

# ضرایب جریمه (Penalty Weights)
PENALTY_MIN_SEC_SLACK = 1000 # جریمه سنگین برای عدم برآورده شدن Min Sec
PENALTY_INPUT_CONFLICT = 100 # جریمه متوسط برای تداخل دروس یک ورودی
PENALTY_DAY_USAGE = 10 # جریمه سبک برای استفاده از روزهای بیشتر توسط استادان
PENALTY_TIME_GAP = 5 # جریمه سبک برای هر واحد فاصله زمانی (Time Gap)

# ==============================================================================
# --- ۱. تعریف داده‌ها  ---
# ==============================================================================
courses = {
    'ریاضی2': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 3},
    'فیزیک1': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 3},
    'آماراحتمال1': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 4},
    'هوش مصنوعی': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 3},
    'پایگاه داده': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 3},
    'ساختمان داده': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 4},
    'ماتریس': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 3},
    'دیفرانسیل': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 3},
    'آنالیز ریاضی': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 3},
    'بهینه سازی خطی': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 3},
    'مباحث': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 3},
    'ریاضی1': {'inputs': [1404], 'sections_needed': 2, 'group': 'علوم_کامپیوتر', 'units': 3},
    'فیزیک1 م': {'inputs': [1404], 'sections_needed': 2, 'group': 'مهندسی_کامپیوتر', 'units': 3},
    'گسسته': {'inputs': [1404], 'sections_needed': 2, 'group': 'مهندسی_کامپیوتر', 'units': 3},
    'دیفرانسیل م': {'inputs': [1404], 'sections_needed': 2, 'group': 'مهندسی_کامپیوتر', 'units': 3},
    'کارگاه کامپیوتر': {'inputs': [1404], 'sections_needed': 4, 'group': 'مهندسی_کامپیوتر', 'units': 1},
    'برنامه سازی پیشرفته': {'inputs': [1404], 'sections_needed': 2, 'group': 'مهندسی_کامپیوتر', 'units': 3},
    'آز فیزیک2': {'inputs': [1404], 'sections_needed': 3, 'group': 'مهندسی_کامپیوتر', 'units': 1},
    'زبان تخصصی': {'inputs': [1404], 'sections_needed': 1, 'group': 'مهندسی_کامپیوتر', 'units': 3},
    'سیستم های عامل': {'inputs': [1404], 'sections_needed': 2, 'group': 'مهندسی_کامپیوتر', 'units': 3},
    'آز پایگاه': {'inputs': [1404], 'sections_needed': 2, 'group': 'مهندسی_کامپیوتر', 'units': 1},
    'آز مدار': {'inputs': [1404], 'sections_needed': 2, 'group': 'مهندسی_کامپیوتر', 'units': 1},
    'معماری کامپیوتر': {'inputs': [1404], 'sections_needed': 2, 'group': 'مهندسی_کامپیوتر', 'units': 3}
}

all_time = [(0, 8, 10), (0, 10, 12), (0, 13, 15), (0, 15, 17), (0, 17, 19),
            (1, 8, 10), (1, 10, 12), (1, 13, 15), (1, 15, 17), (1, 17, 19),
            (2, 8, 10), (2, 10, 12), (2, 13, 15), (2, 15, 17), (2, 17, 19),
            (3, 8, 10), (3, 10, 12), (3, 13, 15), (3, 15, 17), (3, 17, 19),
            (4, 8, 10), (4, 10, 12), (4, 13, 15), (4, 15, 17), (4, 17, 19)]

professors = {
    'حسینی نیا': {'group': 'هیات_علمی', 'teachable_courses': ['ریاضی2'], 'available_times': all_time,
                  'section_range': (2, 5)},
    'دهیار': {'group': 'هیات_علمی', 'teachable_courses': ['فیزیک1', 'آز فیزیک2'], 'available_times': all_time,
              'section_range': (2, 5)},
    'نصیرزاده': {'group': 'هیات_علمی', 'teachable_courses': ['آماراحتمال1'], 'available_times': all_time,
                 'section_range': (2, 5)},
    'روشن ضمیر': {'group': 'هیات_علمی', 'teachable_courses': ['پایگاه داده', 'هوش مصنوعی'], 'available_times': all_time,
                  'section_range': (2, 5)},
    'نعمت الهی': {'group': 'هیات_علمی', 'teachable_courses': ['ماتریس', 'ساختمان داده'], 'available_times': all_time,
                  'section_range': (1, 5)},
    'مصلحی': {'group': 'هیات_علمی', 'teachable_courses': ['دیفرانسیل'], 'available_times': all_time,
              'section_range': (1, 5)},
    'لطفی پور': {'group': 'هیات_علمی', 'teachable_courses': ['آنالیز ریاضی'], 'available_times': all_time,
                 'section_range': (1, 5)},
    'سپاسیان': {'group': 'هیات_علمی', 'teachable_courses': ['بهینه سازی خطی'], 'available_times': all_time,
                'section_range': (1, 5)},
    'عبدالهی': {'group': 'هیات_علمی', 'teachable_courses': ['نظریه محاسبه', 'مباحث'], 'available_times': all_time,
                'section_range': (2, 6)},
    'ستوده': {'group': 'هیات_علمی', 'teachable_courses': ['آز پایگاه', 'گسسته'], 'available_times': all_time,
              'section_range': (4, 6)},
    'نصیری': {'group': 'هیات_علمی', 'teachable_courses': ['معماری کامپیوتر'], 'available_times': all_time,
              'section_range': (2, 5)},
    'کوهنورد': {'group': 'هیات_علمی', 'teachable_courses': ['ریاضی1'], 'available_times': all_time,
                'section_range': (2, 5)},
    'موسوی': {'group': 'هیات_علمی', 'teachable_courses': ['فیزیک1 م'], 'available_times': all_time,
              'section_range': (2, 5)},
    'امیری': {'group': 'هیات_علمی', 'teachable_courses': ['دیفرانسیل م'], 'available_times': all_time,
              'section_range': (2, 5)},
    'خدادوست': {'group': 'هیات_علمی', 'teachable_courses': ['کارگاه کامپیوتر'], 'available_times': all_time,
                'section_range': (2, 5)},
    'انصاری': {'group': 'هیات_علمی', 'teachable_courses': ['برنامه سازی پیشرفته'], 'available_times': all_time,
               'section_range': (2, 5)},
    'رفیعی': {'group': 'هیات_علمی', 'teachable_courses': ['زبان تخصصی'], 'available_times': all_time,
              'section_range': (1, 5)},
    'جاویدی': {'group': 'هیات_علمی', 'teachable_courses': ['سیستم های عامل'], 'available_times': all_time,
               'section_range': (2, 5)},
    'فیروزی': {'group': 'هیات_علمی', 'teachable_courses': ['آز مدار'], 'available_times': all_time,
               'section_range': (2, 5)}
}

# لیست اسلات‌های زمانی منظم برای تشخیص شکاف
time_slots_ordered = sorted(list(set([(t[0], t[1], t[2]) for t in all_time])))
day_time_map = defaultdict(list)
for day, start, end in time_slots_ordered:
    day_time_map[day].append((start, end))

days = range(5)
max_units = 126

section_instances = []
all_inputs = set(sum([data['inputs'] for data in courses.values()], []))

for course, data in courses.items():
    for sec_id in range(data['sections_needed']):
        section_instances.append((course, sec_id))

# ==============================================================================
# --- ۲. تعریف مدل و متغیرها ---
# ==============================================================================
model = pulp.LpProblem("University_Scheduling_Configurable", pulp.LpMinimize)
assign_vars = {}
for course, data in courses.items():
    for sec_id in range(data['sections_needed']):
        sec = (course, sec_id)
        for prof, prof_data in professors.items():
            if course in prof_data['teachable_courses']:
                for time in prof_data['available_times']:
                    assign_vars[(sec, prof, time)] = pulp.LpVariable(
                        f"assign_{course}_{sec_id}_{prof}_{time[0]}_{time[1]}_{time[2]}", cat='Binary')

prof_assignment = {}
if SETTING_UNIFIED_PROFESSOR_HARD:
    for course in courses:
        for prof in professors:
            if course in professors[prof]['teachable_courses']:
                prof_assignment[(course, prof)] = pulp.LpVariable(f"prof_assign_{course}_{prof}", cat='Binary')

# ==============================================================================
# --- ۳. محدودیت‌های سخت (Hard Constraints) ---
# ==============================================================================

# ۱. هر سکشن دقیقاً یک تخصیص دارد (ضروری)
for sec in section_instances:
    model += pulp.lpSum(
        assign_vars[key] for key in assign_vars if key[0] == sec) == 1, f"One_Assignment_for_{sec[0]}_{sec[1]}"

# ۲. عدم تداخل زمانی برای استاد (ضروری)
for prof in professors:
    for time_slot in professors[prof]['available_times']:
        model += pulp.lpSum(
            assign_vars[key] for key in assign_vars if key[1] == prof and key[2] == time_slot
        ) <= 1, f"Prof_{prof}_No_Overlap_at_{time_slot[0]}_{time_slot[1]}"

# ۳. محدودیت حداکثر سکشن استاد (ضروری برای ظرفیت)
for prof, data in professors.items():
    _, max_sec = data['section_range']
    prof_assignments = pulp.lpSum(
        assign_vars[key] for key in assign_vars if key[1] == prof)
    model += prof_assignments <= max_sec, f"Prof_{prof}_Max_Sections_HARD"

# ۴. محدودیت: تخصیص یکپارچه استاد به درس (اختیاری)
if SETTING_UNIFIED_PROFESSOR_HARD:
    for course in courses:
        model += pulp.lpSum(
            prof_assignment[(course, prof)] for prof in professors if (course, prof) in prof_assignment
        ) == 1, f"One_Prof_per_Course_{course}"

    for course in courses:
        sec_count = courses[course]['sections_needed']
        for prof in professors:
            if course in professors[prof]['teachable_courses']:
                for sec_id in range(sec_count):
                    sec = (course, sec_id)
                    model += pulp.lpSum(
                        assign_vars[(sec, prof, time)] for time in professors[prof]['available_times']
                        if (sec, prof, time) in assign_vars
                    ) <= prof_assignment[(course, prof)], f"Sec_{course}_{sec_id}_Assigned_to_{prof}_Link"

# ۵. محدودیت: حداکثر واحد (اختیاری)
if SETTING_MAX_UNITS_HARD:
    total_units = pulp.lpSum(
        assign_vars[key] * courses[key[0][0]]['units'] for key in assign_vars)
    model += total_units <= max_units, "Max_Total_Units_HARD"

# ۶. محدودیت: عدم تداخل ورودی (اختیاری)
if SETTING_NO_OVERLAP_INPUT_HARD:
    for input_id in all_inputs:
        input_sections = [
            sec for sec in section_instances if input_id in courses[sec[0]]['inputs']]

        for time_slot in all_time:
            model += pulp.lpSum(
                assign_vars[key] for key in assign_vars if key[0] in input_sections and key[2] == time_slot
            ) <= 1, f"Input_{input_id}_No_Overlap_at_{time_slot[0]}_{time_slot[1]}_HARD"

# ۷. محدودیت: توزیع سکشن‌های درس در روزهای متفاوت (اجباری و قابل فیلتر) 💡
if SETTING_DIFFERENT_DAYS_FOR_COURSE_HARD:

    # فیلتر دروس بر اساس TARGET_SECTIONS_FOR_HARD_DISTRIBUTION
    target_courses = [
        c for c, data in courses.items()
        if data['sections_needed'] in TARGET_SECTIONS_FOR_HARD_DISTRIBUTION
    ]

    for course in target_courses:
        # متغیر باینری برای ردیابی روزهایی که درس در آن تخصیص یافته است
        course_assigned_to_day = {day: pulp.LpVariable(f"course_{course}_day_hard_{day}", cat='Binary') for day in days}
        M_course = courses[course]['sections_needed']

        # ۱. لینک کردن تخصیص سکشن به روز:
        for day in days:
            # مجموع تخصیص‌های سکشن‌های درس در این روز
            sum_sections_in_day = pulp.lpSum(
                assign_vars[key] for key in assign_vars if key[0][0] == course and key[2][0] == day
            )

            # اگر sum_sections_in_day >= 1 باشد، course_assigned_to_day باید 1 شود.
            model += sum_sections_in_day <= M_course * course_assigned_to_day[
                day], f"Link_{course}_Day_{day}_Upper_HARD"

            # اگر course_assigned_to_day=1 باشد، حداقل 1 سکشن باید تخصیص یابد.
            model += sum_sections_in_day >= course_assigned_to_day[day], f"Link_{course}_Day_{day}_Lower_HARD"

        # ۲. محدودیت نهایی: مجموع روزهای استفاده شده باید حداقل ۲ باشد.
        # این تضمین می‌کند که سکشن‌ها (مثلا ۲ یا ۳ سکشن) در حداقل دو روز مختلف قرار گیرند.
        model += pulp.lpSum(course_assigned_to_day.values()) >= 2, f"Force_Different_Days_{course}_HARD"

# ==============================================================================
# --- ۴. توابع هدف بهینه‌سازی (Soft Constraints) ---
# ==============================================================================
penalty = 0

# ۱. هدف نرم: حداقل کردن کمبود حجم کاری استاد (تبدیل Min Sec به هدف)
if SETTING_MIN_SEC_SOFT:
    for prof, data in professors.items():
        min_sec, _ = data['section_range']
        prof_assignments = pulp.lpSum(
            assign_vars[key] for key in assign_vars if key[1] == prof)
        min_sec_slack = pulp.LpVariable(f"slack_min_sec_{prof}", lowBound=0)
        model += min_sec - prof_assignments <= min_sec_slack, f"Soft_Min_Sections_{prof}_SLACK"
        penalty += min_sec_slack * PENALTY_MIN_SEC_SLACK

# ۲. هدف نرم: حداقل کردن تداخل ورودی (Soft)
if SETTING_PREFER_NO_CONFLICT_INPUT_SOFT:
    for input_id in all_inputs:
        input_sections = [
            sec for sec in section_instances if input_id in courses[sec[0]]['inputs']]
        for time_slot in all_time:
            input_overlap = pulp.LpVariable(f"input_overlap_{input_id}_{time_slot[0]}_{time_slot[1]}", cat='Binary')
            M = len(input_sections)
            model += pulp.lpSum(
                assign_vars[key] for key in assign_vars if key[0] in input_sections and key[2] == time_slot
            ) - 1 <= M * input_overlap, f"Input_{input_id}_Overlap_Detect_{time_slot[0]}_{time_slot[1]}"
            penalty += input_overlap * PENALTY_INPUT_CONFLICT

# ۳. هدف نرم: حداقل کردن تعداد روزهای استفاده‌شده استاد (پیوستگی روزها)
if SETTING_PREFER_CONSECUTIVE_DAYS_SOFT:
    for prof, data in professors.items():
        if data['group'] in ['هیات_علمی', 'مدعو']:
            days_used = {day: pulp.LpVariable(f"days_used_{prof}_{day}", cat='Binary') for day in days}

            for day in days:
                M = data['section_range'][1]
                model += pulp.lpSum(
                    assign_vars[key] for key in assign_vars if key[1] == prof and key[2][0] == day
                ) <= M * days_used[day], f"Link_Prof_{prof}_Day_{day}"

            penalty += pulp.lpSum(days_used.values()) * PENALTY_DAY_USAGE

# ۴. هدف نرم: حداقل کردن فاصله زمانی بین کلاس‌ها در یک روز (پیوستگی ساعتی)
if SETTING_PREFER_CONSECUTIVE_TIME_SOFT:
    for prof, data in professors.items():
        if data['group'] in ['هیات_علمی', 'مدعو']:

            for day in days:
                if len(day_time_map[day]) <= 1:
                    continue

                for i in range(1, len(day_time_map[day]) - 1):
                    prev_time = (day, day_time_map[day][i - 1][0], day_time_map[day][i - 1][1])
                    curr_time = (day, day_time_map[day][i][0], day_time_map[day][i][1])
                    next_time = (day, day_time_map[day][i + 1][0], day_time_map[day][i + 1][1])

                    gap_var = pulp.LpVariable(f"gap_{prof}_{day}_{i}", cat='Binary')

                    is_used = lambda t: pulp.lpSum(
                        assign_vars[key] for key in assign_vars if key[1] == prof and key[2] == t)

                    M_gap = 2
                    model += is_used(prev_time) + is_used(next_time) - is_used(
                        curr_time) <= 1 + gap_var * M_gap, f"Prof_{prof}_Time_Gap_Check_{day}_{i}"

                    penalty += gap_var * PENALTY_TIME_GAP

# هدف نهایی: حداقل کردن جریمه
model += penalty, "Total_Penalty"

# ==============================================================================
# --- ۵. حل و نمایش خروجی ---
# ==============================================================================

print("شروع حل مدل با تنظیمات قابل مدیریت...")
print(
    f"تنظیمات فعال: Min Sec Soft={SETTING_MIN_SEC_SOFT}, Unified Prof Hard={SETTING_UNIFIED_PROFESSOR_HARD}, Different Days Course Hard={SETTING_DIFFERENT_DAYS_FOR_COURSE_HARD}")
print(f"محدودیت توزیع روز برای دروس با سکشن‌های: {TARGET_SECTIONS_FOR_HARD_DISTRIBUTION}")

status = model.solve(pulp.PULP_CBC_CMD(msg=1, options=['sec 120', 'gap 0.05']))

if status == pulp.LpStatusOptimal or status == pulp.LpStatusNotSolved:
    print("\n✅ برنامه یافت شد:")

    total_units = 0
    schedule = defaultdict(list)
    course_day_check = defaultdict(set)  # برای بررسی توزیع روز
    day_names = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']

    for var in assign_vars:
        if pulp.value(assign_vars[var]) == 1.0:
            (course, sec_id), prof, (day, start, end) = var
            total_units += courses[course]['units']
            schedule[prof].append((day, start, end, course, sec_id))
            course_day_check[course].add(day)

    final_penalty = 0
    if model.objective:
        final_penalty = pulp.value(model.objective)

    target_courses_for_check = [c for c, data in courses.items() if
                                data['sections_needed'] in TARGET_SECTIONS_FOR_HARD_DISTRIBUTION]

    for course in target_courses_for_check:
        days_used = len(course_day_check[course])
        if days_used < 2:
            print(
                f"\n❌ خطای توزیع: درس {course} ({courses[course]['sections_needed']} سکشن) در {days_used} روز تخصیص داده شده است. (باید حداقل ۲ باشد).")
        elif days_used >= 2:
            print(
                f"\n✅ توزیع موفق: درس {course} ({courses[course]['sections_needed']} سکشن) در {days_used} روز مجزا تخصیص داده شده است.")

    for prof in sorted(schedule.keys()):
        min_sec_target = professors[prof]['section_range'][0]
        actual_sec = len(schedule[prof])
        slack_value = max(0, min_sec_target - actual_sec)

        print(f"\nبرنامه استاد {prof}: (تخصیص: {actual_sec} سکشن | Min هدف: {min_sec_target} | کمبود: {slack_value})")
        for day, start, end, course, sec_id in sorted(schedule[prof]):
            print(f"  درس {course} (سکشن {sec_id + 1}) - {day_names[day]} {start}-{end}")

    print(f"\nمجموع واحدهای برنامه: {total_units}")
    print(f"مقدار جریمه نهایی (هدف): {final_penalty:.2f}")
    print(f"وضعیت مدل: {pulp.LpStatus[status]}")

else:
    print(f"\n❌ هیچ برنامه‌ای یافت نشد. وضعیت: {pulp.LpStatus[status]}")
    print(
        "توجه: اگر مدل Infeasible شد، تضاد در محدودیت‌های سخت است. برای حل، SETTING_UNIFIED_PROFESSOR_HARD یا SETTING_DIFFERENT_DAYS_FOR_COURSE_HARD را FALSE کنید و یا TARGET_SECTIONS_FOR_HARD_DISTRIBUTION را کوچک‌تر کنید.")