"""Internal Assessment Routes - per course"""
from flask import Blueprint, request, jsonify, session
from models.internal_model import InternalModel

internal_bp = Blueprint('internals', __name__, url_prefix='/api/internals')


def check_auth():
    return 'user_id' in session


@internal_bp.route('/<int:course_id>', methods=['GET'])
def get_internals(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    internals = InternalModel.get_internals_by_course(course_id)
    return jsonify({'success': True, 'data': internals})


@internal_bp.route('/detail/<int:internal_id>', methods=['GET'])
def get_internal(internal_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    internal = InternalModel.get_internal_by_id(internal_id)
    structure = InternalModel.get_full_internal_structure(internal_id)
    return jsonify({'success': True, 'data': {**internal, **structure}})


@internal_bp.route('/<int:course_id>/setup', methods=['POST'])
def setup_internals(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    count = data.get('count', 0)
    if count < 1:
        return jsonify({'success': False, 'message': 'Invalid count'}), 400
    internals = InternalModel.create_internals_batch(course_id, count)
    return jsonify({'success': True, 'data': internals})


@internal_bp.route('/detail/<int:internal_id>/co', methods=['POST'])
def setup_internal_co(internal_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    co_data = data.get('co_data', [])
    try:
        InternalModel.setup_internal_co_mapping(internal_id, co_data)
        return jsonify({'success': True, 'message': 'CO mapping updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@internal_bp.route('/detail/<int:internal_id>/assignments', methods=['POST'])
def setup_internal_assignments(internal_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    assignment_count = data.get('assignment_count', 0)
    assignment_marks = data.get('assignment_marks', {})
    try:
        InternalModel.setup_assignment_structure(internal_id, assignment_count, assignment_marks)
        return jsonify({'success': True, 'message': 'Assignments updated'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@internal_bp.route('/detail/<int:internal_id>/rename', methods=['PUT'])
def rename_internal(internal_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Name required'}), 400
    InternalModel.rename_internal(internal_id, name)
    return jsonify({'success': True, 'message': 'Internal renamed'})


@internal_bp.route('/detail/<int:internal_id>/fill-stats', methods=['GET'])
def get_fill_stats(internal_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    stats = InternalModel.get_internal_fill_stats(internal_id)
    return jsonify({'success': True, 'data': stats})
