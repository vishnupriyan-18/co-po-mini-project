"""Marks Model - per course/internal"""
from database import execute_query, execute_insert, execute_update, get_db_connection


class MarksModel:

    @staticmethod
    def save_mark(student_id, internal_id, component_type, component_number, marks):
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """SELECT id FROM marks
                   WHERE student_id=? AND internal_id=? AND component_type=? AND component_number=?""",
                (student_id, internal_id, component_type, component_number)
            )
            existing = cursor.fetchone()
            if existing:
                conn.execute(
                    """UPDATE marks SET marks=?, updated_at=CURRENT_TIMESTAMP
                       WHERE student_id=? AND internal_id=? AND component_type=? AND component_number=?""",
                    (marks, student_id, internal_id, component_type, component_number)
                )
            else:
                conn.execute(
                    """INSERT INTO marks (student_id, internal_id, component_type, component_number, marks)
                       VALUES (?, ?, ?, ?, ?)""",
                    (student_id, internal_id, component_type, component_number, marks)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def bulk_save_marks(marks_data):
        conn = get_db_connection()
        try:
            for mark in marks_data:
                cursor = conn.execute(
                    """SELECT id FROM marks
                       WHERE student_id=? AND internal_id=? AND component_type=? AND component_number=?""",
                    (mark['student_id'], mark['internal_id'],
                     mark['component_type'], mark['component_number'])
                )
                existing = cursor.fetchone()
                if existing:
                    conn.execute(
                        """UPDATE marks SET marks=?, updated_at=CURRENT_TIMESTAMP
                           WHERE student_id=? AND internal_id=? AND component_type=? AND component_number=?""",
                        (mark['marks'], mark['student_id'], mark['internal_id'],
                         mark['component_type'], mark['component_number'])
                    )
                else:
                    conn.execute(
                        """INSERT INTO marks (student_id, internal_id, component_type, component_number, marks)
                           VALUES (?, ?, ?, ?, ?)""",
                        (mark['student_id'], mark['internal_id'],
                         mark['component_type'], mark['component_number'], mark['marks'])
                    )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_marks_for_internal(internal_id):
        return execute_query(
            "SELECT student_id, component_type, component_number, marks FROM marks WHERE internal_id=?",
            (internal_id,)
        )

    @staticmethod
    def get_marks_table_data(course_id, internal_id, co_list, assignments):
        students = execute_query(
            "SELECT * FROM students WHERE course_id = ? ORDER BY reg_no",
            (course_id,)
        )
        marks = MarksModel.get_marks_for_internal(internal_id)

        marks_by_student = {}
        for mark in marks:
            key = f"{mark['student_id']}_{mark['component_type']}_{mark['component_number']}"
            marks_by_student[key] = mark['marks']

        result = []
        for student in students:
            sid = student['id']
            student_data = {
                'student_id': sid,
                'reg_no': student['reg_no'],
                'name': student['name'],
                'marks': {},
                'co_total': 0,
                'assignment_total': 0,
                'internal_total': 0
            }
            for co in co_list:
                val = marks_by_student.get(f"{sid}_CO_{co['co_number']}", 0)
                student_data['marks'][f"CO{co['co_number']}"] = val
                student_data['co_total'] += val
            for assign in assignments:
                val = marks_by_student.get(f"{sid}_ASSIGNMENT_{assign['assignment_number']}", 0)
                student_data['marks'][f"A{assign['assignment_number']}"] = val
                student_data['assignment_total'] += val
            student_data['internal_total'] = student_data['co_total'] + student_data['assignment_total']
            result.append(student_data)
        return result

    @staticmethod
    def get_student_summary(student_id, course_id):
        internals = execute_query(
            "SELECT * FROM internals WHERE course_id = ? ORDER BY id", (course_id,)
        )
        summary = []
        for internal in internals:
            iid = internal['id']
            marks = execute_query(
                "SELECT component_type, marks FROM marks WHERE student_id=? AND internal_id=?",
                (student_id, iid)
            )
            co_total = sum(m['marks'] for m in marks if m['component_type'] == 'CO')
            assign_total = sum(m['marks'] for m in marks if m['component_type'] == 'ASSIGNMENT')
            summary.append({
                'internal_id': iid,
                'internal_name': internal['internal_name'],
                'co_total': co_total,
                'assignment_total': assign_total,
                'internal_total': co_total + assign_total
            })
        return summary

    @staticmethod
    def get_internal_analytics(course_id, internal_id, co_list, assignments):
        data = MarksModel.get_marks_table_data(course_id, internal_id, co_list, assignments)
        if not data:
            return {}
        totals = [d['internal_total'] for d in data]
        co_totals = [d['co_total'] for d in data]
        assign_totals = [d['assignment_total'] for d in data]
        max_internal = sum(c['max_marks'] for c in co_list) + sum(a['max_marks'] for a in assignments)
        pass_threshold = max_internal * 0.4

        def stats(lst):
            if not lst:
                return {}
            return {'avg': round(sum(lst)/len(lst), 2), 'max': max(lst), 'min': min(lst), 'count': len(lst)}

        return {
            'internal_total_stats': stats(totals),
            'co_total_stats': stats(co_totals),
            'assignment_total_stats': stats(assign_totals),
            'pass_count': sum(1 for t in totals if t >= pass_threshold),
            'fail_count': sum(1 for t in totals if t < pass_threshold),
            'total_students': len(data),
            'max_possible': max_internal
        }

    @staticmethod
    def get_export_data(course_id, internal_id, co_list, assignments):
        rows = MarksModel.get_marks_table_data(course_id, internal_id, co_list, assignments)
        export = []
        for i, row in enumerate(rows, 1):
            flat = {'S.No': i, 'Reg No': row['reg_no'], 'Name': row['name']}
            for co in co_list:
                flat[f"CO{co['co_number']} (max {co['max_marks']})"] = row['marks'].get(f"CO{co['co_number']}", 0)
            flat['CO Total'] = row['co_total']
            for assign in assignments:
                flat[f"A{assign['assignment_number']} (max {assign['max_marks']})"] = row['marks'].get(f"A{assign['assignment_number']}", 0)
            flat['Assignment Total'] = row['assignment_total']
            flat['Internal Total'] = row['internal_total']
            export.append(flat)
        return export

    @staticmethod
    def delete_student_marks(student_id, internal_id):
        return execute_update(
            "DELETE FROM marks WHERE student_id=? AND internal_id=?",
            (student_id, internal_id)
        )

    @staticmethod
    def delete_internal_marks(internal_id):
        return execute_update("DELETE FROM marks WHERE internal_id=?", (internal_id,))
