"""Student Model - per course"""
from database import execute_query, execute_insert, execute_update, get_db_connection


class StudentModel:
    @staticmethod
    def get_students_by_course(course_id):
        return execute_query(
            "SELECT * FROM students WHERE course_id = ? ORDER BY reg_no",
            (course_id,)
        )

    @staticmethod
    def get_student_by_id(student_id):
        return execute_query("SELECT * FROM students WHERE id = ?", (student_id,), fetch_one=True)

    @staticmethod
    def create_student(course_id, reg_no, name):
        return execute_insert(
            "INSERT INTO students (course_id, reg_no, name) VALUES (?, ?, ?)",
            (course_id, reg_no, name)
        )

    @staticmethod
    def update_student(student_id, reg_no, name):
        return execute_update(
            "UPDATE students SET reg_no=?, name=? WHERE id=?",
            (reg_no, name, student_id)
        )

    @staticmethod
    def delete_student(student_id):
        return execute_update("DELETE FROM students WHERE id=?", (student_id,))

    @staticmethod
    def bulk_create_students(course_id, students_list):
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM students WHERE course_id = ?", (course_id,))
            # Also clear marks for internals of this course
            conn.execute(
                "DELETE FROM marks WHERE internal_id IN (SELECT id FROM internals WHERE course_id = ?)",
                (course_id,)
            )
            ids = []
            for s in students_list:
                cursor = conn.execute(
                    "INSERT INTO students (course_id, reg_no, name) VALUES (?, ?, ?)",
                    (course_id, s['reg_no'], s['name'])
                )
                ids.append(cursor.lastrowid)
            conn.commit()
            return ids
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
