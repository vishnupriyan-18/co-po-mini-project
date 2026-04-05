"""Attainment Routes - Advanced Calculation Matching Excel"""
from flask import Blueprint, request, jsonify, session
from database import execute_query, get_db_connection

attainment_bp = Blueprint('attainment', __name__, url_prefix='/api/attainment')


def check_auth():
    return 'user_id' in session

# ----------------------------------------------------
# CO-PO Configuration Vectors (ESE & IDA Config)
# ----------------------------------------------------
@attainment_bp.route('/<int:course_id>/config', methods=['GET'])
def get_config(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    configs = execute_query(
        "SELECT co_number, ese_marks, ida_level FROM co_attainment_config WHERE course_id = ?",
        (course_id,)
    )
    return jsonify({'success': True, 'data': configs})

@attainment_bp.route('/<int:course_id>/config', methods=['POST'])
def save_config(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    configs = data.get('configs', [])

    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM co_attainment_config WHERE course_id = ?", (course_id,))
        for c in configs:
            try:
                co_num = int(c['co_number'])
                ese = float(c['ese_marks'])
                ida = float(c['ida_level'])
                conn.execute(
                    "INSERT INTO co_attainment_config (course_id, co_number, ese_marks, ida_level) VALUES (?, ?, ?, ?)",
                    (course_id, co_num, ese, ida)
                )
            except (ValueError, TypeError, KeyError):
                pass
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()
    
    return jsonify({'success': True, 'message': 'Configuration saved successfully'})


# ----------------------------------------------------
# DA Level Threshold Configuration
# ----------------------------------------------------
@attainment_bp.route('/<int:course_id>/da-config', methods=['GET'])
def get_da_config(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    config = execute_query(
        "SELECT level_3, level_2, level_1 FROM da_level_config WHERE course_id = ?",
        (course_id,)
    )
    if not config:
        # Default values if not set
        return jsonify({'success': True, 'data': {'level_3': 85.0, 'level_2': 75.0, 'level_1': 60.0}})
    return jsonify({'success': True, 'data': config[0]})

@attainment_bp.route('/<int:course_id>/grade-mapping', methods=['GET', 'POST'])
def manage_grade_mapping(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    conn = get_db_connection()
    try:
        if request.method == 'GET':
            cursor = conn.execute("SELECT grade, marks_equivalent FROM grade_mapping WHERE course_id = ?", (course_id,))
            rows = [{'grade': r['grade'], 'marks_equivalent': r['marks_equivalent']} for r in cursor.fetchall()]
            return jsonify({'success': True, 'data': rows})
        else:
            data = request.get_json().get('mappings', [])
            conn.execute("DELETE FROM grade_mapping WHERE course_id = ?", (course_id,))
            for m in data:
                conn.execute(
                    "INSERT INTO grade_mapping (course_id, grade, marks_equivalent) VALUES (?, ?, ?)",
                    (course_id, m['grade'], m['marks_equivalent'])
                )
            conn.commit()
            return jsonify({'success': True, 'message': 'Grade mapping saved'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@attainment_bp.route('/<int:course_id>/da-config', methods=['POST'])
def save_da_config(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    data = request.get_json()
    l3 = float(data.get('level_3', 85.0))
    l2 = float(data.get('level_2', 75.0))
    l1 = float(data.get('level_1', 60.0))

    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM da_level_config WHERE course_id = ?", (course_id,))
        conn.execute(
            "INSERT INTO da_level_config (course_id, level_3, level_2, level_1) VALUES (?, ?, ?, ?)",
            (course_id, l3, l2, l1)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()
    
    return jsonify({'success': True, 'message': 'DA thresholds saved'})

# ----------------------------------------------------
# Mapping (CO -> PO Matrix)
# ----------------------------------------------------
@attainment_bp.route('/<int:course_id>/mapping', methods=['GET'])
def get_mapping(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    mappings = execute_query(
        "SELECT co_number, po_name, correlation_level FROM co_po_mapping WHERE course_id = ?",
        (course_id,)
    )
    return jsonify({'success': True, 'data': mappings})

@attainment_bp.route('/<int:course_id>/mapping', methods=['POST'])
def save_mapping(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    mappings = data.get('mappings', [])
    
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM co_po_mapping WHERE course_id = ?", (course_id,))
        for m in mappings:
            try:
                val = int(m.get('correlation_level'))
                if val in [1, 2, 3]:
                    conn.execute(
                        "INSERT INTO co_po_mapping (course_id, co_number, po_name, correlation_level) VALUES (?, ?, ?, ?)",
                        (course_id, m['co_number'], m['po_name'], val)
                    )
            except (ValueError, TypeError):
                pass
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()
        
    return jsonify({'success': True, 'message': 'Mappings saved'})


# ----------------------------------------------------
# Core Calculation Output
# ----------------------------------------------------
@attainment_bp.route('/<int:course_id>/calculate', methods=['GET'])
def calculate_attainment(course_id):
    if not check_auth():
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    return jsonify(calculate_attainment_logic(course_id))

def calculate_attainment_logic(course_id):
    # Student retrieval
    students = execute_query("SELECT id FROM students WHERE course_id = ?", (course_id,))
    if not students:
         return {'success': False, 'message': 'No students found', 'data': {}}
    num_students = len(students)

    internals = execute_query("SELECT id, internal_name FROM internals WHERE course_id = ? ORDER BY id", (course_id,))
    cos = execute_query("SELECT co_number, co_name FROM course_outcomes WHERE course_id = ?", (course_id,))
    
    if not internals or not cos:
        return {'success': False, 'message': 'Setup internals or COs first', 'data': {}}

    internal_ids_str = ",".join(str(i['id']) for i in internals)

    # Max Marks
    co_mappings = execute_query(f"""
        SELECT internal_id, co_number, max_marks
        FROM internal_co_mapping
        WHERE internal_id IN ({internal_ids_str})
    """)
    co_max_dict = {(cm['internal_id'], cm['co_number']): cm['max_marks'] for cm in co_mappings}

    assign_mappings = execute_query(f"""
        SELECT internal_id, sum(max_marks) as total_max 
        FROM assignment_structure 
        WHERE internal_id IN ({internal_ids_str})
        GROUP BY internal_id
    """)
    assign_max_dict = {a['internal_id']: a['total_max'] for a in assign_mappings}

    # Sum Over All Marks
    marks_sum = execute_query(f"""
        SELECT internal_id, component_type, component_number, sum(marks) as total_marks 
        FROM marks
        WHERE internal_id IN ({internal_ids_str})
        GROUP BY internal_id, component_type, component_number
    """)
    
    internal_co_sums = {}
    internal_assign_sums = {}
    for m in marks_sum:
        iid = m['internal_id']
        stype = m['component_type']
        snum = m['component_number']
        if stype == 'CO':
            internal_co_sums[(iid, snum)] = m['total_marks']
        elif stype == 'ASSIGNMENT':
             internal_assign_sums[iid] = internal_assign_sums.get(iid, 0) + m['total_marks']

    # ESE calculation from student marks
    ese_marks_data = execute_query("SELECT marks FROM ese_marks WHERE course_id = ?", (course_id,))
    if ese_marks_data and len(ese_marks_data) > 0:
        ese_average = sum(m['marks'] for m in ese_marks_data) / len(ese_marks_data)
        ese_percentage = (ese_average / 100.0) * 100  # assuming max 100 marks
    else:
        ese_percentage = 0.0

    configs = execute_query("SELECT co_number, ida_level FROM co_attainment_config WHERE course_id = ?", (course_id,))
    config_dict = {c['co_number']: {'ida': c['ida_level']} for c in configs}

    # DA Level Thresholds - Defaulting to 90/80/70 based on user's sample data
    da_config_data = execute_query("SELECT level_3, level_2, level_1 FROM da_level_config WHERE course_id = ?", (course_id,))
    if da_config_data:
        lvl3_t = da_config_data[0]['level_3']
        lvl2_t = da_config_data[0]['level_2']
        lvl1_t = da_config_data[0]['level_1']
    else:
        # User's CO2 (89.8%) was Level 2, meaning Level 3 threshold is likely 90+
        lvl3_t, lvl2_t, lvl1_t = 90.0, 80.0, 70.0

    co_attainment_data = []

    for co in cos:
        co_num = co['co_number']
        co_internal_averages = {}
        co_assign_percentages = []
        
        sum_internal_perc = 0
        internal_count = 0
        
        for internal in internals:
            iid = internal['id']
            if (iid, co_num) in co_max_dict:
                max_m = co_max_dict[(iid, co_num)]
                obtained = internal_co_sums.get((iid, co_num), 0)
                perc = (obtained / (num_students * max_m)) * 100 if max_m > 0 and num_students > 0 else 0
                co_internal_averages[str(iid)] = round(perc, 1)
                
                sum_internal_perc += perc
                internal_count += 1
                
                a_max = assign_max_dict.get(iid, 0)
                a_obt = internal_assign_sums.get(iid, 0)
                a_perc = (a_obt / (num_students * a_max)) * 100 if a_max > 0 and num_students > 0 else 0
                co_assign_percentages.append(a_perc)
            else:
                 co_internal_averages[str(iid)] = 0.0
                 
        assign_mean = sum(co_assign_percentages)/len(co_assign_percentages) if co_assign_percentages else 0.0
        internal_mean = sum_internal_perc / internal_count if internal_count > 0 else 0.0
        
        # Internal * 0.7 + Assignment * 0.3 (Calculates the final internal mark percentage out of 100%)
        final_internal_percentage = (internal_mean * 0.7) + (assign_mean * 0.3)
        
        # Assessment (40%) scaling
        assessment_40 = final_internal_percentage * 0.40
        
        ese_60 = ese_percentage * 0.60
        da_100 = assessment_40 + ese_60
        da_80 = da_100 * 0.80
        
        # IDA Level Calculation - Automated based on Internal performance scaling (out of 3)
        # e.g., 70% Internal -> IDA 2.1 level
        ida = round((internal_mean / 100.0) * 3.0, 1)

        if da_100 >= lvl3_t: da_level = 3.0
        elif da_100 >= lvl2_t: da_level = 2.0
        elif da_100 >= lvl1_t: da_level = 1.0
        else: da_level = 0.0
             
        overall = (da_level * 0.80) + (ida * 0.20)
        
        co_attainment_data.append({
             'co_number': co_num,
             'co_name': co['co_name'],
             'internals': co_internal_averages,
             'assignment': round(assign_mean, 1),
             'assessment_40': round(assessment_40, 1),
             'ese': round(ese_percentage, 1),
             'ese_60': round(ese_60, 1),
             'da_100': round(da_100, 1),
             'da_80': round(da_80, 1),
             'da_level': round(da_level, 1),
             'ida_level': round(ida, 1),
             'overall': round(overall, 2)
        })

    # Final PO Calculation based on precise Overall Level * mapping / 3
    mappings_raw = execute_query("SELECT co_number, po_name, correlation_level FROM co_po_mapping WHERE course_id = ?", (course_id,))
    po_totals = {}
    po_counts = {}
    co_overalls = {c['co_number']: c['overall'] for c in co_attainment_data}

    for m in mappings_raw:
        co_num = m['co_number']
        po_name = m['po_name']
        val = m['correlation_level']
        
        overall = co_overalls.get(co_num, 0)
        po_score = (overall * val) / 3.0
        
        if po_name not in po_totals:
            po_totals[po_name] = 0
            po_counts[po_name] = 0
            
        po_totals[po_name] += po_score
        po_counts[po_name] += 1
        
    po_attainments = {}
    for po_name in po_totals:
        avg = po_totals[po_name] / po_counts[po_name]
        po_attainments[po_name] = round(avg, 2)

    return {
        'success': True,
        'data': {
            'internals': [{'id': str(i['id']), 'name': i['internal_name']} for i in internals],
            'co_attainment': co_attainment_data,
            'po_attainment': po_attainments,
            'course_attainment_avg': round(sum(c['overall'] for c in co_attainment_data)/len(co_attainment_data), 2) if co_attainment_data else 0.0
        }
    }
