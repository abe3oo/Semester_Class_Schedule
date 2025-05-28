import random
import numpy as np
import pandas as pd
from deap import base, creator, tools, algorithms

# تعریف اسلات‌های زمانی
time_slots = [
    ("Saturday", "08-10"), ("Saturday", "10-12"), ("Saturday", "14-16"),
    ("Sunday", "08-10"), ("Sunday", "10-12"), ("Sunday", "14-16"),
    ("Monday", "08-10"), ("Monday", "10-12"), ("Monday", "14-16")
]

# تعریف اساتید و اسلات‌های مجاز
professors = {
    "Rezvani": [0, 1, 2],  # شنبه 8-10, 10-12
    "Sepasian": [0, 7],  # شنبه 8-10, دوشنبه 10-12
    "Nematollahi": [0, 1, 7, 8],  # شنبه 8-10, 10-12, دوشنبه 10-12, 14-16
    "Bakhshandeh": [2, 4, 7],  # شنبه 14-16, یک‌شنبه 10-12, دوشنبه 10-12
    "Firoozi": [4, 6, 7]  # یک‌شنبه 10-12, دوشنبه 8-10, 10-12
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
            "name": f"{course['name']}_{i + 1}",
            "prof": course["prof"],
            "dept": course["dept"]
        })

# تنظیمات DEAP
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()


# ژن: تخصیص هر وظیفه به یه اسلات تصادفی از اسلات‌های مجاز استادش
def init_individual():
    ind = []
    for task in tasks:
        prof_slots = professors[task["prof"]]
        ind.append(random.choice(prof_slots))
    return ind


toolbox.register("individual", tools.initIterate, creator.Individual, init_individual)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


# تابع fitness
def evaluate(individual):
    penalty = 0

    # بررسی تداخل اساتید
    for slot in range(len(time_slots)):
        slot_tasks = [i for i, s in enumerate(individual) if s == slot]
        profs = [tasks[i]["prof"] for i in slot_tasks]
        if len(profs) != len(set(profs)):
            penalty += 1000

    # بررسی تخصیص به اسلات غیرمجاز
    for i, slot in enumerate(individual):
        if slot not in professors[tasks[i]["prof"]]:
            penalty += 1000

    # بررسی تداخل درس‌های یه رشته (جریمه خیلی سنگین)
    dept_conflicts = 0
    for slot in range(len(time_slots)):
        slot_tasks = [i for i, s in enumerate(individual) if s == slot]
        depts = [tasks[i]["dept"] for i in slot_tasks]
        for dept in set(depts):
            if depts.count(dept) > 1:
                dept_conflicts += (depts.count(dept) - 1) * 500  # جریمه سنگین‌تر

    # توزیع یکنواخت
    slot_counts = [individual.count(slot) for slot in range(len(time_slots))]
    distribution_penalty = np.std(slot_counts) * 20

    return penalty + dept_conflicts + distribution_penalty,


toolbox.register("evaluate", evaluate)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.1)
toolbox.register("select", tools.selTournament, tournsize=3)


# نمایش برنامه به‌صورت جدول و ذخیره در CSV
def print_schedule(individual):
    schedule = {slot: [] for slot in range(len(time_slots))}
    for i, slot in enumerate(individual):
        schedule[slot].append(tasks[i])

    data = []
    for slot, tasks_in_slot in schedule.items():
        if tasks_in_slot:
            for task in tasks_in_slot:
                data.append({
                    "Day": time_slots[slot][0],
                    "Time": time_slots[slot][1],
                    "Course": task["name"],
                    "Professor": task["prof"],
                    "Department": task["dept"]
                })
        else:
            data.append({
                "Day": time_slots[slot][0],
                "Time": time_slots[slot][1],
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
    for slot in range(len(time_slots)):
        slot_tasks = [i for i, s in enumerate(individual) if s == slot]
        depts = [tasks[i]["dept"] for i in slot_tasks]
        for dept in set(depts):
            if depts.count(dept) > 1:
                courses = [tasks[i]["name"] for i in slot_tasks if tasks[i]["dept"] == dept]
                conflicts.append((time_slots[slot], dept, courses))

    if conflicts:
        print("\nDepartment Conflicts:")
        for slot, dept, courses in conflicts:
            print(f"{slot}: {dept} courses {courses}")
    else:
        print("\nNo Department Conflicts!")


# اجرای الگوریتم ژنتیک
def main():
    random.seed(42)
    pop = toolbox.population(n=300)  # افزایش اندازه جمعیت
    hof = tools.HallOfFame(1)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("min", np.min)

    algorithms.eaSimple(pop, toolbox, cxpb=0.7, mutpb=0.2, ngen=500,  # افزایش نسل‌ها
                        stats=stats, halloffame=hof, verbose=True)

    print_schedule(hof[0])


if __name__ == "__main__":
    main()