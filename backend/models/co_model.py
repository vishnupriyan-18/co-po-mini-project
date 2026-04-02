"""Course Outcomes Model - per course"""
from database import execute_query, execute_insert, execute_update, get_db_connection


class COModel:
    @staticmethod
    def get_cos_by_course(course_id):
        return execute_query(
            "SELECT * FROM course_outcomes WHERE course_id = ? ORDER BY co_number",
            (course_id,)
        )

    @staticmethod
    def get_total_co_count(course_id):
        row = execute_query(
            "SELECT total_co FROM courses WHERE id = ?", (course_id,), fetch_one=True
        )
        return row['total_co'] if row else 0

    @staticmethod
    def create_co_pool(course_id, total_co):
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM course_outcomes WHERE course_id = ?", (course_id,))
            for i in range(1, total_co + 1):
                conn.execute(
                    "INSERT INTO course_outcomes (course_id, co_number, co_name) VALUES (?, ?, ?)",
                    (course_id, i, f"CO{i}")
                )
            conn.execute("UPDATE courses SET total_co = ? WHERE id = ?", (total_co, course_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
