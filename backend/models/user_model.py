"""User Model - Teacher ID based authentication"""
from database import execute_query, execute_insert, get_db_connection


class UserModel:
    @staticmethod
    def get_user_by_teacher_id(teacher_id):
        return execute_query("SELECT * FROM users WHERE teacher_id = ?", (teacher_id,), fetch_one=True)

    @staticmethod
    def verify_user(teacher_id, password):
        user = UserModel.get_user_by_teacher_id(teacher_id)
        if user and user['password'] == password:
            return {'id': user['id'], 'teacher_id': user['teacher_id'], 'name': user['name']}
        return None

    @staticmethod
    def create_user(teacher_id, name, password):
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO users (teacher_id, name, password) VALUES (?, ?, ?)",
                (teacher_id, name, password)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
