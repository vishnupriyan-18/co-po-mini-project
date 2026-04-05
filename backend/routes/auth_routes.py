"""Authentication Routes - Teacher ID based"""
from flask import Blueprint, request, jsonify, session
from models.user_model import UserModel

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    teacher_id = data.get('teacher_id', '').strip()
    name = data.get('name', '').strip()
    password = data.get('password', '').strip()

    if not all([teacher_id, name, password]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    existing = UserModel.get_user_by_teacher_id(teacher_id)
    if existing:
        return jsonify({'success': False, 'message': 'Teacher ID already registered'}), 400

    try:
        user_id = UserModel.create_user(teacher_id, name, password)
        return jsonify({'success': True, 'message': 'Registration successful', 'user_id': user_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    teacher_id = data.get('teacher_id', '').strip()
    password = data.get('password', '').strip()

    user = UserModel.verify_user(teacher_id, password)
    if user:
        session['user_id'] = user['id']
        session['teacher_id'] = user['teacher_id']
        session['name'] = user['name']
        return jsonify({'success': True, 'message': 'Login successful', 'name': user['name']})

    return jsonify({'success': False, 'message': 'Invalid Teacher ID or Password'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})


@auth_bp.route('/check', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'authenticated': True,
            'teacher_id': session.get('teacher_id'),
            'name': session.get('name')
        })
    return jsonify({'success': True, 'authenticated': False})
