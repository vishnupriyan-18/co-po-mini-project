"""Course Model - multi-course per teacher"""
from database import execute_query, execute_insert, execute_update, get_db_connection


class CourseModel:
    @staticmethod
    def get_courses_by_teacher(teacher_id):
        return execute_query(
            "SELECT * FROM courses WHERE teacher_id = ? ORDER BY created_at",
            (teacher_id,)
        )

    @staticmethod
    def get_course_by_id(course_id):
        return execute_query("SELECT * FROM courses WHERE id = ?", (course_id,), fetch_one=True)

    @staticmethod
    def create_course(teacher_id, course_name, subject_code, department, semester):
        return execute_insert(
            "INSERT INTO courses (teacher_id, course_name, subject_code, department, semester) VALUES (?, ?, ?, ?, ?)",
            (teacher_id, course_name, subject_code, department, semester)
        )

    @staticmethod
    def update_course(course_id, course_name, subject_code, department, semester):
        return execute_update(
            "UPDATE courses SET course_name=?, subject_code=?, department=?, semester=? WHERE id=?",
            (course_name, subject_code, department, semester, course_id)
        )

    @staticmethod
    def delete_course(course_id):
        return execute_update("DELETE FROM courses WHERE id=?", (course_id,))
