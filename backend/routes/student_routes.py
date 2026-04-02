"""Student Routes - per course"""
from flask import Blueprint, request, jsonify, session
from models.student_model import StudentModel

student_bp = Blueprint('students', __name__, url_prefix='/api/students')


def check_auth():
    return 'user_id' in session


@student_bp.route('/<int:course_id>', methods=['GET'])
def get_students(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    students = StudentModel.get_students_by_course(course_id)
    return jsonify({'success': True, 'data': students})


@student_bp.route('/<int:course_id>', methods=['POST'])
def create_student(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    student_id = StudentModel.create_student(course_id, data.get('reg_no'), data.get('name'))
    return jsonify({'success': True, 'data': {'id': student_id, 'reg_no': data.get('reg_no'), 'name': data.get('name')}})


@student_bp.route('/student/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    StudentModel.update_student(student_id, data.get('reg_no'), data.get('name'))
    return jsonify({'success': True, 'message': 'Student updated'})


@student_bp.route('/student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    StudentModel.delete_student(student_id)
    return jsonify({'success': True, 'message': 'Student deleted'})


@student_bp.route('/<int:course_id>/bulk', methods=['POST'])
def bulk_create_students(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    students = data.get('students', [])
    if not students:
        return jsonify({'success': False, 'message': 'No students provided'}), 400
    StudentModel.bulk_create_students(course_id, students)
    return jsonify({'success': True, 'message': f'{len(students)} students saved'})
