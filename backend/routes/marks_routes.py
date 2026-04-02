"""Marks Routes - per course/internal"""
import csv
import io
from flask import Blueprint, request, jsonify, session, Response
from models.marks_model import MarksModel
from models.internal_model import InternalModel

marks_bp = Blueprint('marks', __name__, url_prefix='/api/marks')


def check_auth():
    return 'user_id' in session


@marks_bp.route('/<int:internal_id>', methods=['GET'])
def get_marks(internal_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    internal = InternalModel.get_internal_by_id(internal_id)
    if not internal:
        return jsonify({'success': False, 'message': 'Internal not found'}), 404
    structure = InternalModel.get_full_internal_structure(internal_id)
    students_data = MarksModel.get_marks_table_data(
        internal['course_id'], internal_id,
        structure['co_list'], structure['assignments']
    )
    return jsonify({
        'success': True,
        'data': {
            'students': students_data,
            'co_list': structure['co_list'],
            'assignments': structure['assignments']
        }
    })


@marks_bp.route('/save', methods=['POST'])
def save_mark():
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    MarksModel.save_mark(
        data.get('student_id'), data.get('internal_id'),
        data.get('component_type'), data.get('component_number'), data.get('marks')
    )
    return jsonify({'success': True, 'message': 'Mark saved'})


@marks_bp.route('/bulk-save', methods=['POST'])
def bulk_save_marks():
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    marks = data.get('marks', [])
    if not marks:
        return jsonify({'success': False, 'message': 'No marks provided'}), 400
    try:
        MarksModel.bulk_save_marks(marks)
        return jsonify({'success': True, 'message': f'{len(marks)} marks saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@marks_bp.route('/<int:internal_id>/analytics', methods=['GET'])
def get_analytics(internal_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    internal = InternalModel.get_internal_by_id(internal_id)
    structure = InternalModel.get_full_internal_structure(internal_id)
    analytics = MarksModel.get_internal_analytics(
        internal['course_id'], internal_id,
        structure['co_list'], structure['assignments']
    )
    return jsonify({'success': True, 'data': analytics})


@marks_bp.route('/<int:internal_id>/export', methods=['GET'])
def export_marks_csv(internal_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    internal = InternalModel.get_internal_by_id(internal_id)
    structure = InternalModel.get_full_internal_structure(internal_id)
    rows = MarksModel.get_export_data(
        internal['course_id'], internal_id,
        structure['co_list'], structure['assignments']
    )
    if not rows:
        return jsonify({'success': False, 'message': 'No data to export'}), 404
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    filename = f"{internal['internal_name'].replace(' ', '_')}_marks.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@marks_bp.route('/<int:internal_id>', methods=['DELETE'])
def delete_internal_marks(internal_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    count = MarksModel.delete_internal_marks(internal_id)
    return jsonify({'success': True, 'message': f'Deleted marks for internal {internal_id}', 'rows': count})


@marks_bp.route('/<int:internal_id>/student/<int:student_id>', methods=['DELETE'])
def delete_student_marks(internal_id, student_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    count = MarksModel.delete_student_marks(student_id, internal_id)
    return jsonify({'success': True, 'message': 'Student marks cleared', 'rows': count})
