"""Internal Assessment Model - per course"""
from database import execute_query, execute_insert, execute_update, get_db_connection


class InternalModel:

    @staticmethod
    def get_internals_by_course(course_id):
        return execute_query(
            "SELECT * FROM internals WHERE course_id = ? ORDER BY id",
            (course_id,)
        )

    @staticmethod
    def get_internal_by_id(internal_id):
        return execute_query("SELECT * FROM internals WHERE id=?", (internal_id,), fetch_one=True)

    @staticmethod
    def create_internals_batch(course_id, count):
        """Drop and recreate internals for this course"""
        conn = get_db_connection()
        try:
            # Get existing internal ids for this course
            existing = conn.execute(
                "SELECT id FROM internals WHERE course_id = ?", (course_id,)
            ).fetchall()
            for row in existing:
                conn.execute("DELETE FROM internal_co_mapping WHERE internal_id = ?", (row[0],))
                conn.execute("DELETE FROM assignment_structure WHERE internal_id = ?", (row[0],))
                conn.execute("DELETE FROM marks WHERE internal_id = ?", (row[0],))
            conn.execute("DELETE FROM internals WHERE course_id = ?", (course_id,))

            internal_ids = []
            for i in range(1, count + 1):
                cursor = conn.execute(
                    "INSERT INTO internals (course_id, internal_name, assignment_count) VALUES (?, ?, 0)",
                    (course_id, f"Internal {i}")
                )
                internal_ids.append({'id': cursor.lastrowid, 'internal_name': f"Internal {i}"})
            conn.commit()
            return internal_ids
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def setup_internal_co_mapping(internal_id, co_data):
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM internal_co_mapping WHERE internal_id=?", (internal_id,))
            for co in co_data:
                conn.execute(
                    "INSERT INTO internal_co_mapping (internal_id, co_number, max_marks) VALUES (?, ?, ?)",
                    (internal_id, co['co_number'], co.get('max_marks', 10))
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_internal_co_mapping(internal_id):
        rows = execute_query(
            """SELECT im.co_number, im.max_marks, co.co_name
               FROM internal_co_mapping im
               LEFT JOIN course_outcomes co ON im.co_number = co.co_number
                   AND co.course_id = (SELECT course_id FROM internals WHERE id = ?)
               WHERE im.internal_id=? ORDER BY im.co_number""",
            (internal_id, internal_id)
        )
        for r in rows:
            if r.get('co_name') is None:
                r['co_name'] = f"CO{r['co_number']}"
        return rows

    @staticmethod
    def setup_assignment_structure(internal_id, assignment_count, assignment_marks):
        conn = get_db_connection()
        try:
            conn.execute("DELETE FROM assignment_structure WHERE internal_id=?", (internal_id,))
            for i in range(1, assignment_count + 1):
                conn.execute(
                    "INSERT INTO assignment_structure (internal_id, assignment_number, max_marks) VALUES (?, ?, ?)",
                    (internal_id, i, assignment_marks.get(f"A{i}", 5))
                )
            conn.execute(
                "UPDATE internals SET assignment_count=? WHERE id=?",
                (assignment_count, internal_id)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_assignment_structure(internal_id):
        return execute_query(
            "SELECT * FROM assignment_structure WHERE internal_id=? ORDER BY assignment_number",
            (internal_id,)
        )

    @staticmethod
    def get_full_internal_structure(internal_id):
        return {
            'co_list': InternalModel.get_internal_co_mapping(internal_id),
            'assignments': InternalModel.get_assignment_structure(internal_id)
        }

    @staticmethod
    def rename_internal(internal_id, new_name):
        return execute_update(
            "UPDATE internals SET internal_name=? WHERE id=?",
            (new_name.strip(), internal_id)
        )

    @staticmethod
    def get_internal_fill_stats(internal_id):
        internal = InternalModel.get_internal_by_id(internal_id)
        if not internal:
            return {'expected': 0, 'entered': 0, 'percent': 0}
        structure = InternalModel.get_full_internal_structure(internal_id)
        student_count_row = execute_query(
            "SELECT COUNT(*) as cnt FROM students WHERE course_id = ?",
            (internal['course_id'],), fetch_one=True
        )
        student_count = student_count_row['cnt'] if student_count_row else 0
        components = len(structure['co_list']) + len(structure['assignments'])
        expected = student_count * components
        entered = execute_query(
            "SELECT COUNT(*) as cnt FROM marks WHERE internal_id=? AND marks > 0",
            (internal_id,), fetch_one=True
        )
        entered_count = entered['cnt'] if entered else 0
        return {
            'expected': expected,
            'entered': entered_count,
            'percent': round((entered_count / expected * 100) if expected else 0, 1)
        }
