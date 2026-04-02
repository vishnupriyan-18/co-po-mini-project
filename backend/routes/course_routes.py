"""Course Routes - multi-course per teacher"""
from flask import Blueprint, request, jsonify, session
from models.course_model import CourseModel

course_bp = Blueprint('course', __name__, url_prefix='/api/courses')


def check_auth():
    return 'user_id' in session


@course_bp.route('/', methods=['GET'])
def get_courses():
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    courses = CourseModel.get_courses_by_teacher(session['user_id'])
    return jsonify({'success': True, 'data': courses})


@course_bp.route('/', methods=['POST'])
def create_course():
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    course_name = data.get('course_name', '').strip()
    subject_code = data.get('subject_code', '').strip()
    department = data.get('department', '').strip()
    semester = data.get('semester', '').strip()

    if not all([course_name, subject_code, department, semester]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    try:
        course_id = CourseModel.create_course(
            session['user_id'], course_name, subject_code, department, semester
        )
        return jsonify({'success': True, 'message': 'Course created', 'course_id': course_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@course_bp.route('/<int:course_id>', methods=['GET'])
def get_course(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    course = CourseModel.get_course_by_id(course_id)
    if not course or course['teacher_id'] != session['user_id']:
        return jsonify({'success': False, 'message': 'Course not found'}), 404
    return jsonify({'success': True, 'data': course})


@course_bp.route('/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    CourseModel.update_course(
        course_id,
        data.get('course_name'),
        data.get('subject_code'),
        data.get('department'),
        data.get('semester')
    )
    return jsonify({'success': True, 'message': 'Course updated'})


@course_bp.route('/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    CourseModel.delete_course(course_id)
    return jsonify({'success': True, 'message': 'Course deleted'})
