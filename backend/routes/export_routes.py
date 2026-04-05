import io
from flask import Blueprint, jsonify, session, send_file
from database import execute_query
from routes.attainment_routes import calculate_attainment_logic

export_bp = Blueprint('export', __name__, url_prefix='/api/export')

def check_auth():
    return 'user_id' in session

@export_bp.route('/<int:course_id>/excel', methods=['GET'])
def export_course_excel(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        import pandas as pd
    except ImportError:
        return jsonify({'success': False, 'message': 'Export requires pandas and openpyxl. Please run: pip install pandas openpyxl'}), 501

    # 1. Fetch Students
    students = execute_query("SELECT id, reg_no, name FROM students WHERE course_id=? ORDER BY reg_no", (course_id,))
    if not students:
        return jsonify({'success': False, 'message': 'No students found to export'}), 404

    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # --- SHEET 1 & 2: Internals ---
        internals = execute_query("SELECT id, internal_name FROM internals WHERE course_id=? ORDER BY id", (course_id,))
        for idx, internal in enumerate(internals):
            internal_id = internal['id']
            sheet_name = f"Internal {idx + 1}"
            
            # Get structure
            cos = execute_query("SELECT co_number FROM internal_co_mapping WHERE internal_id=?", (internal_id,))
            assigns = execute_query("SELECT assignment_number FROM assignment_structure WHERE internal_id=?", (internal_id,))
            
            # Get marks
            marks_raw = execute_query("SELECT student_id, component_type, component_number, marks FROM marks WHERE internal_id=?", (internal_id,))
            marks_map = {}
            for m in marks_raw:
                key = (m['student_id'], m['component_type'], m['component_number'])
                marks_map[key] = m['marks']
            
            rows = []
            for s_idx, s in enumerate(students):
                row = {
                    'S.No': s_idx + 1,
                    'Reg No': s['reg_no'],
                    'Name': s['name']
                }
                # CO Marks
                for co in cos:
                    row[f"CO{co['co_number']}"] = marks_map.get((s['id'], 'CO', co['co_number']), 0)
                # Assignment Marks
                for a in assigns:
                    row[f"A{a['assignment_number']}"] = marks_map.get((s['id'], 'ASSIGNMENT', a['assignment_number']), 0)
                
                rows.append(row)
            
            df_int = pd.DataFrame(rows)
            df_int.to_excel(writer, sheet_name=sheet_name, index=False)

        # --- SHEET 3: ESE Marks ---
        ese_raw = execute_query("SELECT student_id, grade, marks FROM ese_marks WHERE course_id=?", (course_id,))
        ese_map = {m['student_id']: m for m in ese_raw}
        
        ese_rows = []
        for s_idx, s in enumerate(students):
            rec = ese_map.get(s['id'], {})
            ese_rows.append({
                'S.No': s_idx + 1,
                'Reg No': s['reg_no'],
                'Name': s['name'],
                'Grade': rec.get('grade', '-'),
                'Marks Equivalent': rec.get('marks', 0.0)
            })
        
        df_ese = pd.DataFrame(ese_rows)
        df_ese.to_excel(writer, sheet_name="ESE Results", index=False)

        # --- SHEET 4: Attainment Summary ---
        # I need the attainment calculation logic in a reusable way.
        # I'll modify attainment_routes.py to expose it if needed.
        # For now, let's call the calculation logic if available.
        try:
            att_res = calculate_attainment_logic(course_id)
            if att_res['success']:
                att_data = att_res['data']['co_attainment']
                att_rows = []
                for co in att_data:
                    row = {
                        "CO's": f"CO{co['co_number']}",
                        "Assignment": co['assignment'],
                        "Assessment (40%)": co['assessment_40'],
                        "ESE (100%)": co['ese'],
                        "ESE (60%)": co['ese_60'],
                        "DA (100%)": co['da_100'],
                        "DA (80%)": co['da_80'],
                        "DA level": co['da_level'],
                        "IDA Level": co['ida_level'],
                        "Overall": co['overall']
                    }
                    # Insert internal columns dynamically
                    for i_idx, internal in enumerate(internals):
                        i_id = str(internal['id'])
                        row[f"INT {i_idx + 1}"] = co['internals'].get(i_id, 0.0)
                    
                    att_rows.append(row)
                
                df_att = pd.DataFrame(att_rows)
                # Reorder columns to match the 12-column layout
                cols = ["CO's"]
                for i_idx in range(len(internals)):
                    cols.append(f"INT {i_idx + 1}")
                cols += ["Assignment", "Assessment (40%)", "ESE (100%)", "ESE (60%)", "DA (100%)", "DA (80%)", "DA level", "IDA Level", "Overall"]
                
                df_att = df_att[cols]
                df_att.to_excel(writer, sheet_name="Attainment Summary", index=False)
        except Exception as e:
            print(f"Attainment excel export error: {e}")

    output.seek(0)
    course_info = execute_query("SELECT course_name FROM courses WHERE id=?", (course_id,))
    name = course_info[0]['course_name'].replace(' ', '_') if course_info else 'Course'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"{name}_Full_Report.xlsx"
    )
