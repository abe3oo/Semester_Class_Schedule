
# University Course Scheduler – Complete Project Setup


[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![PuLP](https://img.shields.io/badge/PuLP-2.7%2B-orange)](https://coin-or.github.io/pulp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **highly configurable linear programming model** for **university class scheduling**, built with **PuLP**. Assigns course sections to professors and time slots while respecting **hard constraints** (e.g., no overlaps, professor capacity) and **optimizing soft goals** (e.g., workload balance, time continuity).

---

## Features

### Hard Constraints (Strictly Enforced)
- Each section is assigned **exactly once**.
- **No time overlap** for professors.
- **Max section limit** per professor.
- **Unified professor per course** (optional).
- **Section distribution across different days** (for courses with 2+ sections).
- Optional: max total units, no student input conflicts.

### Soft Constraints (Optimized via Penalties)
- Meet **minimum section load** per professor.
- Prefer **fewer working days** per professor.
- Avoid **time gaps** in a professor’s daily schedule.
- Reduce **student input conflicts**.

### Fully Configurable
- Toggle constraints on/off.
- Adjustable **penalty weights**.
- Filter day-distribution rules by number of sections.

### Persian Support
- Course and professor names in Persian.
- Output in Persian (days, messages, schedule).

---

## Requirements

```txt
Python >= 3.8
PuLP >= 2.7
```

Install dependencies:

```bash
pip install pulp
```

> Uses **CBC solver** (bundled with PuLP) — no external solver required.

---

## Quick Start

1. **Clone or download** this repository.
2. **Edit the data** (courses, professors, time slots) in the script.
3. **Run**:

```bash
python scheduling.py
```

### Sample Output


شروع حل مدل با تنظیمات قابل مدیریت...
تنظیمات فعال: Min Sec Soft=True, Unified Prof Hard=True, Different Days Course Hard=True

برنامه یافت شد:

توزیع موفق: درس ریاضی2 (2 سکشن) در 2 روز مجزا تخصیص داده شده است.

برنامه استاد حسینی نیا: (تخصیص: 2 سکشن | Min هدف: 2 | کمبود: 0)
  درس ریاضی2 (سکشن 1) - شنبه 8-10
  درس ریاضی2 (سکشن 2) - یکشنبه 8-10

...

مجموع واحدهای برنامه: 126
مقدار جریمه نهایی (هدف): 0.00
وضعیت مدل: Optimal


---

## Configuration (Top of Script)

```python
# Hard Constraints
SETTING_UNIFIED_PROFESSOR_HARD = True
SETTING_DIFFERENT_DAYS_FOR_COURSE_HARD = True
TARGET_SECTIONS_FOR_HARD_DISTRIBUTION = [2]  # Apply to 2-section courses

# Soft Goals
SETTING_MIN_SEC_SOFT = True
SETTING_PREFER_CONSECUTIVE_DAYS_SOFT = True
SETTING_PREFER_CONSECUTIVE_TIME_SOFT = True

# Penalty Weights
PENALTY_MIN_SEC_SLACK = 1000
PENALTY_DAY_USAGE = 10
PENALTY_TIME_GAP = 5
```

> **Tip**: If the model is `Infeasible`, try:
> - `SETTING_UNIFIED_PROFESSOR_HARD = False`
> - Remove or reduce `TARGET_SECTIONS_FOR_HARD_DISTRIBUTION`

---

## Data Structure

### `courses` (Example)

```python
'ریاضی2': {
    'inputs': [1404],
    'sections_needed': 2,
    'group': 'علوم_کامپیوتر',
    'units': 3
}
```

### `professors` (Example)

```python
'حسینی نیا': {
    'group': 'هیات_علمی',
    'teachable_courses': ['ریاضی2'],
    'available_times': all_time,
    'section_range': (2, 5)  # min, max sections
}
```

### Time Slots

```python
(0, 8, 10)  # Day 0 = شنبه, 8:00–10:00
```

Days: `0=شنبه`, `1=یکشنبه`, ..., `4=چهارشنبه`

---

## How It Works

1. **Binary variables** for `(section, professor, time)` assignments.
2. **Hard constraints** ensure feasibility.
3. **Soft constraints** converted to penalty terms in the objective.
4. **Solved** using CBC (120s timeout, 5% optimality gap).
5. **Validated output** with per-professor schedule and diagnostics.

---

## Troubleshooting

| Problem | Solution |
|-------|----------|
| `Infeasible` | Disable `UNIFIED_PROFESSOR_HARD` or reduce `TARGET_SECTIONS_FOR_HARD_DISTRIBUTION` |
| High penalty | Increase `PENALTY_MIN_SEC_SLACK` or relax soft goals |
| Slow solve | Reduce time slots or set `options=['sec 60']` |

---

## Customization Ideas

- Add classroom constraints.
- Support multiple semesters or campuses.
- Export to CSV/Excel.
- Build a web UI with Streamlit or Flask.

---

## Contributing

Contributions are welcome! Feel free to:
- Open issues for bugs or feature requests.
- Submit pull requests with improvements.
- Keep Persian naming consistent.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE.txt) file for details.

```
Copyright (c) 2025 Amirreza Abbaszadeh
```

---

**Built with PuLP by [Amirreza Abbaszadeh](https://github.com/abe3oo)**  
*Smart, fair, and configurable scheduling for real-world universities.*
```