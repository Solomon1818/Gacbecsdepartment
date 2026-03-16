from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from database import get_db
from bson import ObjectId
import re

def get_grade_point(mark):
    """Convert mark (out of 100) to grade point using GAC Coimbatore grading."""
    if mark == 'Not provided' or mark is None:
        return None, None
    mark = int(mark)
    if mark >= 90:   return 10.0, 'O'
    elif mark >= 80: return round(8.0 + (mark - 80) * 0.09, 2), 'D+'
    elif mark >= 75: return round(7.5 + (mark - 75) * 0.1, 2),  'D'
    elif mark >= 70: return round(7.0 + (mark - 70) * 0.1, 2),  'A+'
    elif mark >= 60: return round(6.0 + (mark - 60) * 0.1, 2),  'A'
    elif mark >= 50: return round(5.0 + (mark - 50) * 0.1, 2),  'B'
    elif mark >= 40: return round(4.0 + (mark - 40) * 0.1, 2),  'C'
    else:            return 0.0, 'RA'

def calculate_gpa(subjects):
    """
    GPA = Σ(Credit × GradePoint) / Σ(Credits)
    Each subject needs a 'credit' field. Default credit = 3 if missing.
    Skips subjects with 'Not provided' marks.
    """
    total_credit_points = 0
    total_credits = 0
    for subj in subjects:
        mark = subj.get('mark')
        if mark == 'Not provided' or mark is None:
            continue
        credit = subj.get('credit', 3)
        gp, _ = get_grade_point(mark)
        if gp is not None:
            total_credit_points += credit * gp
            total_credits += credit
    if total_credits == 0:
        return None
    return round(total_credit_points / total_credits, 2)

def calculate_cgpa(semesters):
    """
    CGPA = Σ(all semester Credit×GP) / Σ(all credits) across all semesters.
    """
    total_credit_points = 0
    total_credits = 0
    for sem_key in ['sem1','sem2','sem3','sem4','sem5','sem6']:
        subjects = semesters.get(sem_key, [])
        for subj in subjects:
            mark = subj.get('mark')
            if mark == 'Not provided' or mark is None:
                continue
            credit = subj.get('credit', 3)
            gp, _ = get_grade_point(mark)
            if gp is not None:
                total_credit_points += credit * gp
                total_credits += credit
    if total_credits == 0:
        return None
    return round(total_credit_points / total_credits, 2)

def enrich_semesters(semesters):
    """Add grade_point, letter_grade, gpa to each semester and subjects."""
    enriched = {}
    for sem_key in ['sem1','sem2','sem3','sem4','sem5','sem6']:
        subjects = semesters.get(sem_key)
        if not subjects:
            continue
        enriched_subjects = []
        for subj in subjects:
            mark = subj.get('mark')
            gp, grade = get_grade_point(mark)
            enriched_subjects.append({
                **subj,
                'grade_point': gp,
                'letter_grade': grade
            })
        gpa = calculate_gpa(subjects)
        enriched[sem_key] = {
            'subjects': enriched_subjects,
            'gpa': gpa
        }
    return enriched

students_bp = Blueprint('students', __name__)

def serialize_student(student):
    """Convert MongoDB document to JSON-safe dict."""
    student['_id'] = str(student['_id'])
    return student

@students_bp.route('/students')
@login_required
def students():
    db = get_db()
    year = request.args.get('year', '')
    search = request.args.get('search', '').strip()

    query = {}
    if year:
        query['year'] = year
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'rollno': {'$regex': search, '$options': 'i'}},
        ]

    students_list = list(db.students.find(query, {
        'name': 1, 'rollno': 1, 'year': 1, 'course': 1,
        'email': 1, 'phone': 1, 'community': 1, 'religion': 1
    }))
    for s in students_list:
        s['_id'] = str(s['_id'])

    year_counts = {
        'First Year': db.students.count_documents({'year': 'First Year'}),
        'Second Year': db.students.count_documents({'year': 'Second Year'}),
        'Third Year': db.students.count_documents({'year': 'Third Year'}),
    }

    return render_template('students.html',
                           students=students_list,
                           year_counts=year_counts,
                           selected_year=year,
                           search=search)

@students_bp.route('/students/<student_id>')
@login_required
def student_detail(student_id):
    db = get_db()
    student = db.students.find_one({'_id': ObjectId(student_id)})
    if not student:
        return "Student not found", 404
    student['_id'] = str(student['_id'])
    semesters = student.get('semesters', {})
    enriched = enrich_semesters(semesters)
    cgpa = calculate_cgpa(semesters)
    return render_template('student_detail.html', student=student, enriched=enriched, cgpa=cgpa)

@students_bp.route('/api/students')
@login_required
def api_students():
    db = get_db()
    year = request.args.get('year', '')
    search = request.args.get('search', '').strip()

    query = {}
    if year:
        query['year'] = year
    if search:
        query['$or'] = [
            {'name': {'$regex': search, '$options': 'i'}},
            {'rollno': {'$regex': search, '$options': 'i'}},
        ]

    students_list = list(db.students.find(query, {
        'name': 1, 'rollno': 1, 'year': 1, 'course': 1, 'email': 1, 'phone': 1
    }))
    for s in students_list:
        s['_id'] = str(s['_id'])

    return jsonify(students_list)

@students_bp.route('/students/<student_id>/attendance', methods=['POST'])
@login_required
def save_attendance(student_id):
    db = get_db()
    data = request.get_json()
    attendance = data.get('attendance', {})
    db.students.update_one(
        {'_id': ObjectId(student_id)},
        {'$set': {'attendance': attendance}}
    )
    return jsonify({'success': True})

@students_bp.route('/students/<student_id>/arrear', methods=['POST'])
@login_required
def update_arrear(student_id):
    from flask import request as req
    db = get_db()
    data = req.get_json()
    sem_key = data.get('sem_key')
    subject = data.get('subject')
    cleared = data.get('cleared', False)

    # Update the specific subject's arrear_cleared flag
    student = db.students.find_one({'_id': ObjectId(student_id)})
    if not student:
        return jsonify({'success': False}), 404

    semesters = student.get('semesters', {})
    subjects = semesters.get(sem_key, [])
    for subj in subjects:
        if subj.get('subject') == subject:
            subj['arrear_cleared'] = cleared
            break

    db.students.update_one(
        {'_id': ObjectId(student_id)},
        {'$set': {f'semesters.{sem_key}': subjects}}
    )
    return jsonify({'success': True})
