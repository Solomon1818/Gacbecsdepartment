"""
update_credits.py
Run once to update credit values for all subjects in all semesters.
Credits are based on the official GAC Coimbatore B.Sc Computer Science marksheets.

Usage: python update_credits.py
"""

from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.environ.get('MONGO_URI'))
db = client[os.environ.get('DB_NAME', 'student_db')]

# ── Credit mapping per semester ────────────────────────────────────────────
# Source: Official B.Sc Computer Science marksheets, GAC Coimbatore-18
# Format: { "subject name (lowercase, stripped)": credit_value }

SEMESTER_CREDITS = {
    "sem1": {
        "tamil i":                              3,
        "part-i:language:i tamil -i":           3,
        "part i tamil - i":                     3,
        "english i":                            3,
        "part-ii :english- i":                  3,
        "part ii english - i":                  3,
        "digital computer fundamentals":        3,
        "core 2: digital computer fundamentals":3,
        "programming methodology":              3,
        "core 1: programming methodology":      3,
        "programming methodology lab":          2,
        "core practical 1 : programming methodology lab": 2,
        "statistics":                           3,
        "allied 1: statistics and numerical methods": 3,
        "environmental studies":                2,
    },
    "sem2": {
        "tamil ii":                             3,
        "part i tamil - ii":                    3,
        "english ii":                           3,
        "part ii english - ii":                 3,
        "c++ programming":                      2,
        "core iii: c++ programming":            2,
        "computer system architecture":         3,
        "core iv: computer system architecture":3,
        "c++ programming lab":                  2,
        "core practical ii:c++ programming lab":2,
        "discrete mathematics":                 3,
        "allied -ii:discrete mathematics for computer science": 3,
        "value education - gandhian thoughts":  2,
        "value education- gandhian thoughts":   2,
        "nms:english language communication":   2,
    },
    "sem3": {
        "tamil iii":                            3,
        "part i tamil iii":                     3,
        "english iii":                          3,
        "part ii english iii":                  3,
        "software engineering":                 3,
        "core 5: software engineering":         3,
        "data structures":                      2,
        "core 6: data structures":              2,
        "programming in java":                  3,
        "core 7: programming in java":          3,
        "java programming lab":                 2,
        "core practical 3: java programming lab": 2,
        "operational research for computer science": 3,
        "allied- 3: operations research for computer science": 3,
        "nmn - computational skills for employability- foundation of coding with python": 2,
    },
    "sem4": {
        "tamil iv":                             3,
        "part i tamil iv":                      3,
        "english iv":                           3,
        "part ii english iv":                   3,
        "python":                               3,
        "core 10 : python pragramming":         3,
        "algorithm":                            3,
        "core 8: algorithms":                   3,
        "database management system":           3,
        "core 9: database management system":   3,
        "python lab":                           3,
        "core practical 5 : python pragramming lab": 3,
        "database management system lab":       3,
        "core practical 6 : dbms lab (sql)":    3,
        "business accounting":                  3,
        "allied -4 : business accounting":      3,
        "value education":                      2,
        "nms:fundamentals of web development":  2,
        "extension activities- ncc/nss/sports/yrc": 1,
    },
    "sem5": {
        "operating system":                     3,
        "computer networks":                    3,
        "computer graphics":                    3,
        "non major english":                    2,
        "internet technologies":                3,
        "internet technologies lab":            2,
        "linux shell scripting lab":            2,
    },
    "sem6": {
        "open source computing":                3,
        "c# programming":                       3,
        "artificial intelligence":              3,
        "open source computing lab":            2,
        "c# programming lab":                   2,
        "non major english":                    2,
    },
}

def normalize(name):
    """Lowercase and strip for fuzzy matching."""
    return name.strip().lower()

def find_credit(sem_key, subject_name):
    """Look up credit for a subject. Returns 3 as default if not found."""
    mapping = SEMESTER_CREDITS.get(sem_key, {})
    norm = normalize(subject_name)
    # Exact match first
    if norm in mapping:
        return mapping[norm]
    # Partial match fallback
    for key, credit in mapping.items():
        if key in norm or norm in key:
            return credit
    print(f"  [WARNING] No credit found for '{subject_name}' in {sem_key} — defaulting to 3")
    return 3

def update_all_students():
    students = list(db.students.find({}))
    print(f"Found {len(students)} students. Updating credits...\n")

    updated_count = 0
    for student in students:
        semesters = student.get('semesters', {})
        updated_semesters = {}
        changed = False

        for sem_key in ['sem1','sem2','sem3','sem4','sem5','sem6']:
            subjects = semesters.get(sem_key)
            if not subjects:
                continue
            updated_subjects = []
            for subj in subjects:
                credit = find_credit(sem_key, subj.get('subject', ''))
                new_subj = dict(subj)
                if new_subj.get('credit') != credit:
                    changed = True
                new_subj['credit'] = credit
                updated_subjects.append(new_subj)
            updated_semesters[sem_key] = updated_subjects

        if changed:
            # Merge updated semesters back
            merged = dict(semesters)
            merged.update(updated_semesters)
            db.students.update_one(
                {'_id': student['_id']},
                {'$set': {'semesters': merged}}
            )
            updated_count += 1
            print(f"  Updated: {student.get('name')} ({student.get('rollno')})")

    print(f"\nDone! Updated {updated_count} / {len(students)} students.")

if __name__ == '__main__':
    update_all_students()
