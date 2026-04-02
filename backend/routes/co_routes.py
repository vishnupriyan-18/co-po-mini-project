"""Course Outcomes Routes - per course"""
from flask import Blueprint, request, jsonify, session
from models.co_model import COModel

co_bp = Blueprint('co', __name__, url_prefix='/api/co')


def check_auth():
    return 'user_id' in session


@co_bp.route('/<int:course_id>', methods=['GET'])
def get_cos(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    cos = COModel.get_cos_by_course(course_id)
    total = COModel.get_total_co_count(course_id)
    return jsonify({'success': True, 'data': cos, 'total_co': total})


@co_bp.route('/<int:course_id>/setup', methods=['POST'])
def setup_co_pool(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    total_co = data.get('total_co', 0)
    if total_co < 1:
        return jsonify({'success': False, 'message': 'Invalid CO count'}), 400
    try:
        COModel.create_co_pool(course_id, total_co)
        return jsonify({'success': True, 'message': f'{total_co} COs created'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
