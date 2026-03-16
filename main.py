from flask import Blueprint, render_template
from flask_login import login_required, current_user
from database import get_db
from students import get_grade_point, calculate_cgpa, enrich_semesters

main_bp = Blueprint('main', __name__)

def get_arrears(student):
    """Return list of arrear subjects (RA grade) with semester info."""
    arrears = []
    semesters = student.get('semesters', {})
    sem_labels = {
        'sem1': 'Semester 1', 'sem2': 'Semester 2',
        'sem3': 'Semester 3', 'sem4': 'Semester 4',
        'sem5': 'Semester 5', 'sem6': 'Semester 6',
    }
    for sem_key, label in sem_labels.items():
        subjects = semesters.get(sem_key, [])
        for subj in subjects:
            mark = subj.get('mark')
            if mark == 'Not provided' or mark is None:
                continue
            gp, grade = get_grade_point(mark)
            if grade == 'RA':
                arrears.append({
                    'semester': label,
                    'sem_key': sem_key,
                    'subject': subj.get('subject'),
                    'mark': mark,
                    'cleared': subj.get('arrear_cleared', False),
                })
    return arrears

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    stats = {
        'total':       db.students.count_documents({}),
        'first_year':  db.students.count_documents({'year': 'First Year'}),
        'second_year': db.students.count_documents({'year': 'Second Year'}),
        'third_year':  db.students.count_documents({'year': 'Third Year'}),
    }
    # Arrear summary counts
    all_students = list(db.students.find({}, {'name':1,'rollno':1,'year':1,'semesters':1}))
    arrear_count = 0
    for s in all_students:
        if get_arrears(s):
            arrear_count += 1
    stats['arrear_students'] = arrear_count
    return render_template('dashboard.html', stats=stats, user=current_user)


@main_bp.route('/rankings')
@login_required
def rankings():
    db = get_db()
    years = ['First Year', 'Second Year', 'Third Year']
    rankings_data = {}

    for year in years:
        students = list(db.students.find(
            {'year': year},
            {'name':1, 'rollno':1, 'year':1, 'semesters':1}
        ))
        ranked = []
        for s in students:
            semesters = s.get('semesters', {})
            cgpa = calculate_cgpa(semesters)
            arrears = get_arrears(s)
            ranked.append({
                '_id': str(s['_id']),
                'name': s.get('name'),
                'rollno': s.get('rollno'),
                'cgpa': cgpa,
                'arrear_count': len(arrears),
            })
        # Sort by CGPA descending, None last
        ranked.sort(key=lambda x: x['cgpa'] if x['cgpa'] else 0, reverse=True)
        rankings_data[year] = ranked[:10]

    return render_template('rankings.html', rankings_data=rankings_data)


@main_bp.route('/arrears')
@login_required
def arrears():
    db = get_db()
    years = ['First Year', 'Second Year', 'Third Year']
    arrears_data = {}

    for year in years:
        students = list(db.students.find(
            {'year': year},
            {'name':1, 'rollno':1, 'year':1, 'semesters':1, '_id':1}
        ))
        year_arrears = []
        for s in students:
            student_arrears = get_arrears(s)
            if student_arrears:
                year_arrears.append({
                    '_id': str(s['_id']),
                    'name': s.get('name'),
                    'rollno': s.get('rollno'),
                    'arrears': student_arrears,
                    'total': len(student_arrears),
                    'cleared': sum(1 for a in student_arrears if a['cleared']),
                    'pending': sum(1 for a in student_arrears if not a['cleared']),
                })
        year_arrears.sort(key=lambda x: x['pending'], reverse=True)
        arrears_data[year] = year_arrears

    return render_template('arrears.html', arrears_data=arrears_data)
