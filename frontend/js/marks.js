// Marks Entry Module - Enhanced

let currentInternalId = null;
let currentStructure = null;
let allInputs = [];

// Load internals dropdown
async function loadInternalsDropdown() {
    const courseId = localStorage.getItem('selectedCourseId');
    if (!courseId) return;
    const result = await api.get(`/internals/${courseId}`);
    if (result.success) {
        const select = document.getElementById('internalSelect');
        select.innerHTML = '<option value="">-- Select Internal --</option>';
        result.data.forEach(internal => {
            select.innerHTML += `<option value="${internal.id}">${internal.internal_name}</option>`;
        });
    }
}

// Load marks table when internal selected
async function loadMarksTable() {
    const internalId = document.getElementById('internalSelect').value;
    if (!internalId) {
        document.getElementById('marksCard').classList.add('hidden');
        document.getElementById('emptyState').classList.remove('hidden');
        document.getElementById('infoStrip').classList.add('hidden');

        document.getElementById('clearBtn').style.display = 'none';
        return;
    }

    currentInternalId = internalId;
    showLoading();

    const result = await api.get(`/marks/${internalId}`);
    hideLoading();

    if (!result.success) {
        showNotification('Failed to load marks', 'error');
        return;
    }

    const data = result.data;
    currentStructure = { co_list: data.co_list, assignments: data.assignments };

    // Info strip
    const selectedOption = document.getElementById('internalSelect').selectedOptions[0];
    document.getElementById('internalTitle').textContent = selectedOption.text + ' — Marks Entry';
    document.getElementById('infoCOs').textContent = `📋 ${data.co_list.length} CO${data.co_list.length !== 1 ? 's' : ''}`;
    document.getElementById('infoAssigns').textContent = `📄 ${data.assignments.length} Assignment${data.assignments.length !== 1 ? 's' : ''}`;
    document.getElementById('infoStudents').textContent = `👥 ${data.students.length} Student${data.students.length !== 1 ? 's' : ''}`;
    document.getElementById('infoStrip').classList.remove('hidden');

    // Footer stats
    const coMaxTotal = data.co_list.reduce((s, co) => s + co.max_marks, 0);
    const assignMaxTotal = data.assignments.reduce((s, a) => s + a.max_marks, 0);
    document.getElementById('statStudents').textContent = data.students.length;
    document.getElementById('statCOMax').textContent = coMaxTotal;
    document.getElementById('statAssignMax').textContent = assignMaxTotal;
    document.getElementById('statInternalMax').textContent = coMaxTotal + assignMaxTotal;

    buildTableHeader(data.co_list, data.assignments);
    buildTableBody(data.students, data.co_list, data.assignments);

    document.getElementById('fillProgress').style.display = 'block';
    updateProgress();

    document.getElementById('marksCard').classList.remove('hidden');
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('saveBtn').disabled = false;
    document.getElementById('clearBtn').style.display = 'inline-flex';

    setupKeyboardNav();
    loadAnalytics(internalId);
    loadAttainmentAnalytics();
}

// Build table header (two rows: group + individual with max marks)
function buildTableHeader(coList, assignments) {
    const thead = document.getElementById('marksTableHead');

    let row1 = `<tr>
        <th rowspan="2" class="sticky-sno th-group-identity">S.No</th>
        <th rowspan="2" class="sticky-reg th-group-identity">Reg No</th>
        <th rowspan="2" class="sticky-name th-group-identity col-sep-right">Name</th>`;

    if (coList.length > 0) {
        row1 += `<th colspan="${coList.length}" class="th-group-co">
            CO Marks <span class="section-label">${coList.length} Component${coList.length > 1 ? 's' : ''}</span>
        </th>`;
    }
    row1 += `<th rowspan="2" class="th-group-cototal col-sep-right">CO<br>Total</th>`;

    if (assignments.length > 0) {
        row1 += `<th colspan="${assignments.length}" class="th-group-assign">
            Assignment Marks <span class="section-label">${assignments.length} Assignment${assignments.length > 1 ? 's' : ''}</span>
        </th>`;
    }
    row1 += `<th rowspan="2" class="th-group-assigntotal col-sep-right">Assign<br>Total</th>`;
    row1 += `<th rowspan="2" class="th-group-internaltotal">Internal<br>Total</th></tr>`;

    let row2 = `<tr>`;
    coList.forEach((co, idx) => {
        const isLast = idx === coList.length - 1;
        row2 += `<th class="th-group-co th-max ${isLast ? 'col-sep-right' : ''}">
            CO${co.co_number}<br>
            <small style="font-family:'JetBrains Mono',monospace;font-size:.78rem;opacity:.85;">(${co.max_marks})</small>
        </th>`;
    });
    assignments.forEach((assign, idx) => {
        const isLast = idx === assignments.length - 1;
        row2 += `<th class="th-group-assign th-max ${isLast ? 'col-sep-right' : ''}">
            A${assign.assignment_number}<br>
            <small style="font-family:'JetBrains Mono',monospace;font-size:.78rem;opacity:.85;">(${assign.max_marks})</small>
        </th>`;
    });
    row2 += `</tr>`;

    thead.innerHTML = row1 + row2;
}

// Build table body
function buildTableBody(students, coList, assignments) {
    const tbody = document.getElementById('marksTableBody');
    const totalCols = 3 + coList.length + 1 + assignments.length + 2;

    if (students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${totalCols}" class="text-center" style="padding:40px;color:var(--text-muted);">
            No students found. Please add students first.
        </td></tr>`;
        return;
    }

    tbody.innerHTML = students.map((student, index) => {
        let row = `<tr data-student-id="${student.student_id}">
            <td class="sticky-sno-body">${index + 1}</td>
            <td class="sticky-reg-body">${student.reg_no}</td>
            <td class="sticky-name-body">${student.name}</td>`;

        coList.forEach((co, idx) => {
            const coKey = `CO${co.co_number}`;
            const value = student.marks[coKey] !== undefined ? student.marks[coKey] : '';
            const isLast = idx === coList.length - 1;
            const filled = value !== '' && value !== 0 ? 'input-filled' : '';
            row += `<td class="co-cell ${isLast ? 'col-sep-right-body' : ''}">
                <input type="number" class="marks-input ${filled}"
                       data-component-type="CO"
                       data-component-number="${co.co_number}"
                       data-max="${co.max_marks}"
                       value="${value === 0 && student.marks[coKey] === 0 ? 0 : (value || '')}"
                       min="0" max="${co.max_marks}" placeholder="—"
                       onchange="validateAndUpdateMark(this)"
                       onkeyup="calculateTotals(this);updateProgress();">
            </td>`;
        });

        row += `<td class="co-total-cell col-sep-right-body">${student.co_total || 0}</td>`;

        assignments.forEach((assign, idx) => {
            const assignKey = `A${assign.assignment_number}`;
            const value = student.marks[assignKey] !== undefined ? student.marks[assignKey] : '';
            const isLast = idx === assignments.length - 1;
            const filled = value !== '' && value !== 0 ? 'input-filled' : '';
            row += `<td class="assign-cell ${isLast ? 'col-sep-right-body' : ''}">
                <input type="number" class="marks-input ${filled}"
                       data-component-type="ASSIGNMENT"
                       data-component-number="${assign.assignment_number}"
                       data-max="${assign.max_marks}"
                       value="${value === 0 && student.marks[assignKey] === 0 ? 0 : (value || '')}"
                       min="0" max="${assign.max_marks}" placeholder="—"
                       onchange="validateAndUpdateMark(this)"
                       onkeyup="calculateTotals(this);updateProgress();">
            </td>`;
        });

        row += `<td class="assign-total-cell col-sep-right-body">${student.assignment_total || 0}</td>`;
        row += `<td class="internal-total-cell">${student.internal_total || 0}</td>`;
        row += `</tr>`;
        return row;
    }).join('');
}

// Validate a single mark input
function validateAndUpdateMark(input) {
    const maxMarks = parseFloat(input.dataset.max);
    let value = parseFloat(input.value);
    input.classList.remove('input-warn', 'input-error', 'input-filled');
    if (input.value === '' || isNaN(value)) {
        input.value = '';
    } else if (value < 0) {
        input.value = 0;
        input.classList.add('input-warn');
    } else if (value > maxMarks) {
        input.value = maxMarks;
        input.classList.add('input-warn');
        showNotification(`⚠️ Max marks for this component is ${maxMarks}`, 'warning');
    } else {
        input.classList.add('input-filled');
    }
    calculateTotals(input);
    updateProgress();
}

// Recalculate row totals
function calculateTotals(input) {
    const row = input.closest('tr');
    let coTotal = 0, assignTotal = 0;
    row.querySelectorAll('input[data-component-type="CO"]').forEach(inp => { coTotal += parseFloat(inp.value) || 0; });
    row.querySelectorAll('input[data-component-type="ASSIGNMENT"]').forEach(inp => { assignTotal += parseFloat(inp.value) || 0; });
    row.querySelector('.co-total-cell').textContent = coTotal;
    row.querySelector('.assign-total-cell').textContent = assignTotal;
    row.querySelector('.internal-total-cell').textContent = coTotal + assignTotal;
}

// Progress bar
function updateProgress() {
    const inputs = [...document.querySelectorAll('#marksTableBody .marks-input')];
    if (!inputs.length) return;
    const filled = inputs.filter(i => i.value !== '').length;
    const pct = Math.round((filled / inputs.length) * 100);
    document.getElementById('progressBar').style.width = pct + '%';
    document.getElementById('progressLabel').textContent = `${pct}% filled`;
}

// Clear all marks in current view
function clearAll() {
    if (!confirm('Clear all marks in the current view? Unsaved changes will be lost.')) return;
    document.querySelectorAll('#marksTableBody .marks-input').forEach(input => {
        input.value = '';
        input.className = 'marks-input';
    });
    document.querySelectorAll('.co-total-cell, .assign-total-cell, .internal-total-cell').forEach(td => {
        td.textContent = '0';
    });
    updateProgress();
}

// Save all marks
async function saveAllMarks() {
    if (!currentInternalId) { showNotification('Please select an internal first', 'error'); return; }

    const marksToSave = [];
    document.querySelectorAll('#marksTableBody tr').forEach(row => {
        const studentId = row.dataset.studentId;
        if (!studentId) return;
        row.querySelectorAll('input[data-component-type="CO"]').forEach(input => {
            marksToSave.push({
                student_id: studentId, internal_id: currentInternalId,
                component_type: 'CO', component_number: input.dataset.componentNumber,
                marks: parseFloat(input.value) || 0
            });
        });
        row.querySelectorAll('input[data-component-type="ASSIGNMENT"]').forEach(input => {
            marksToSave.push({
                student_id: studentId, internal_id: currentInternalId,
                component_type: 'ASSIGNMENT', component_number: input.dataset.componentNumber,
                marks: parseFloat(input.value) || 0
            });
        });
    });
    if (!marksToSave.length) { showNotification('No marks to save', 'warning'); return; }
    showLoading();
    const result = await api.post('/marks/bulk-save', { marks: marksToSave });
    hideLoading();
    if (result.success) {
        showNotification(`✅ ${result.message}`, 'success');
        loadAnalytics(currentInternalId);
        loadAttainmentAnalytics();
    } else {
        showNotification(result.message || 'Failed to save marks', 'error');
    }
}

// Export CSV
function exportCSV() {
    if (!currentInternalId) { showNotification('Select an internal first', 'error'); return; }
    window.open(`/api/marks/${currentInternalId}/export`, '_blank');
}

// ==== ESE Logic ====
let gradeMappings = [];

async function loadEseMarksTable() {
    const courseId = localStorage.getItem('selectedCourseId');
    
    // Fetch mappings first
    const gRes = await api.get(`/attainment/${courseId}/grade-mapping`);
    gradeMappings = gRes.success ? gRes.data : [];

    const result = await api.get(`/marks/${courseId}/ese`);
    if (!result.success) return;
    const students = result.data.students;
    
    const tbody = document.getElementById('eseMarksTableBody');
    if (students.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center" style="padding:40px;color:var(--text-muted);">No students found.</td></tr>`;
    } else {
        tbody.innerHTML = students.map((stu, i) => {
            const selectedGrade = stu.ese_grade || '';
            const currentMark = stu.ese_mark || 0;
            
            let options = '<option value="">-- Grade --</option>';
            gradeMappings.forEach(gm => {
                const sel = (String(gm.grade).trim() === String(selectedGrade).trim()) ? 'selected' : '';
                options += `<option value="${gm.grade}" data-marks="${gm.marks_equivalent}" ${sel}>${gm.grade}</option>`;
            });

            return `<tr data-student-id="${stu.id}">
                <td class="sticky-sno-body">${i + 1}</td>
                <td class="sticky-reg-body">${stu.reg_no}</td>
                <td class="sticky-name-body col-sep-right-body">${stu.name}</td>
                <td>
                    <div style="display:flex;align-items:center;gap:10px;">
                        <select class="form-control ese-grade-select ${selectedGrade ? 'input-filled' : ''}" 
                                style="width:120px;"
                                onchange="onEseGradeChange(this)">
                            ${options}
                        </select>
                        <span class="ese-mark-preview" style="font-weight:600;color:#2b6cb0;min-width:60px;">
                            ${selectedGrade ? `(${currentMark.toFixed(1)})` : ''}
                        </span>
                        <input type="hidden" class="ese-numeric-mark" value="${currentMark}">
                    </div>
                </td>
            </tr>`;
        }).join('');
    }
}

function onEseGradeChange(select) {
    const option = select.selectedOptions[0];
    const marks = option ? (parseFloat(option.dataset.marks) || 0) : 0;
    const row = select.closest('tr');
    const preview = row.querySelector('.ese-mark-preview');
    const hidden = row.querySelector('.ese-numeric-mark');
    
    if (marks > 0 || select.value !== '') {
        preview.textContent = `(${marks.toFixed(1)})`;
        hidden.value = marks;
        select.classList.add('input-filled');
    } else {
        preview.textContent = '';
        hidden.value = 0;
        select.classList.remove('input-filled');
    }
}

async function saveEseMarks() {
    const marksToSave = [];
    document.querySelectorAll('#eseMarksTableBody tr').forEach(row => {
        const studentId = row.dataset.studentId;
        if (!studentId) return;
        
        const select = row.querySelector('.ese-grade-select');
        const hidden = row.querySelector('.ese-numeric-mark');
        
        if (select && select.value !== '') {
            marksToSave.push({ 
                student_id: studentId, 
                grade: select.value,
                marks: parseFloat(hidden.value) || 0 
            });
        }
    });
    
    const courseId = localStorage.getItem('selectedCourseId');
    showLoading();
    const result = await api.post(`/marks/${courseId}/ese`, { marks: marksToSave });
    hideLoading();
    if (result.success) {
        showNotification(result.message, 'success');
        loadAttainmentAnalytics();
    } else {
        showNotification(result.message || 'Failed to save ESE marks', 'error');
    }
}

// Load and display analytics panel
async function loadAnalytics(internalId) {
    const result = await api.get(`/marks/${internalId}/analytics`);
    if (!result.success || !result.data) return;
    const d = result.data;
    const panel = document.getElementById('analyticsPanel');
    if (!panel) return;

    const pct = d.total_students > 0 ? Math.round((d.pass_count / d.total_students) * 100) : 0;
    panel.innerHTML = `
        <div class="analytics-grid">
            <div class="an-card">
                <div class="an-label">Class Avg</div>
                <div class="an-value">${d.internal_total_stats?.avg ?? '—'}</div>
                <div class="an-sub">/ ${d.max_possible}</div>
            </div>
            <div class="an-card">
                <div class="an-label">Highest</div>
                <div class="an-value an-success">${d.internal_total_stats?.max ?? '—'}</div>
            </div>
            <div class="an-card">
                <div class="an-label">Lowest</div>
                <div class="an-value an-danger">${d.internal_total_stats?.min ?? '—'}</div>
            </div>
            <div class="an-card">
                <div class="an-label">Pass Rate</div>
                <div class="an-value ${pct >= 60 ? 'an-success' : 'an-danger'}">${pct}%</div>
                <div class="an-sub">${d.pass_count} / ${d.total_students}</div>
            </div>
        </div>`;
    panel.classList.remove('hidden');
}

// Load and display attainment analytics
async function loadAttainmentAnalytics() {
    const cid = localStorage.getItem('selectedCourseId');
    if (!cid) return;
    const result = await api.get(`/attainment/${cid}/calculate`);
    if (!result.success || !result.data || !result.data.co_attainment) return;
    
    document.getElementById('attainmentCard').style.display = 'block';

    // 1. Render CO Attainment
    const co_data = result.data.co_attainment;
    let coHtml = '';
    if (co_data.length === 0) {
        coHtml = `<tr><td colspan="3" style="padding:8px;border:1px solid #e0e5ef;color:#7a8a9e;">No CO data available</td></tr>`;
    } else {
        co_data.forEach(c => {
            const lvl = c.da_level;
            const levelClass = lvl >= 3 ? '#c6f6d5' : (lvl >= 2 ? '#fefcbf' : (lvl >= 1 ? '#fed7d7' : '#e2e8f0'));
            coHtml += `<tr>
                <td style="padding:8px;border:1px solid #e0e5ef;"><b>CO${c.co_number}</b></td>
                <td style="padding:8px;border:1px solid #e0e5ef;">${c.da_100.toFixed(1)}%</td>
                <td style="padding:8px;border:1px solid #e0e5ef;"><span style="background:${levelClass};padding:2px 8px;border-radius:4px;font-weight:600;font-size:0.9rem;">Level ${c.da_level.toFixed(1)}</span></td>
                <td style="padding:8px;border:1px solid #e0e5ef;color:#22543d;"><b>${c.overall.toFixed(2)}</b></td>
            </tr>`;
        });
    }
    document.getElementById('marksCoBody').innerHTML = coHtml;

    // 2. Render PO Attainment
    const p_data = result.data.po_attainment || {};
    if (Object.keys(p_data).length === 0) {
        document.getElementById('marksPoHeader').innerHTML = `<tr style="background:#f8fafc;"><th style="padding:8px;border:1px solid #e0e5ef;">PO Mapping Matrix Currently Empty</th></tr>`;
        document.getElementById('marksPoBody').innerHTML = `<tr><td style="padding:8px;border:1px solid #e0e5ef;color:#7a8a9e;">You must define the CO-PO correlation mappings in the <a href="attainment.html" style="color:#0051cc;">Attainment page</a> to see PO scores here.</td></tr>`;
    } else {
        let headHtml = '<th style="padding:8px;border:1px solid #e0e5ef;">Outcome</th>';
        let bodyHtml = '<td style="padding:8px;border:1px solid #e0e5ef;"><b>Score</b></td>';
        
        const PO_LIST = ['PO1','PO2','PO3','PO4','PO5','PO6','PO7','PO8','PO9','PO10','PO11','PO12','PSO1','PSO2'];
        PO_LIST.forEach(po => {
            headHtml += `<th style="padding:8px;border:1px solid #e0e5ef;">${po}</th>`;
            const val = p_data[po];
            bodyHtml += `<td style="padding:8px;border:1px solid #e0e5ef;font-weight:500;">${val !== undefined ? val : '-'}</td>`;
        });
        
        document.getElementById('marksPoHeader').innerHTML = `<tr style="background:#f8fafc;">${headHtml}</tr>`;
        document.getElementById('marksPoBody').innerHTML = `<tr>${bodyHtml}</tr>`;
    }
}

// Keyboard navigation
function setupKeyboardNav() {
    const inputs = [...document.querySelectorAll('#marksTableBody .marks-input')];
    allInputs = inputs;
    inputs.forEach((input, idx) => {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const next = inputs[idx + 1];
                if (next) next.focus();
            }
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                const row = input.closest('tr');
                const nextRow = row.nextElementSibling;
                if (nextRow) {
                    const cols = [...row.querySelectorAll('.marks-input')];
                    const colIdx = cols.indexOf(input);
                    const nextInputs = nextRow.querySelectorAll('.marks-input');
                    if (nextInputs[colIdx]) nextInputs[colIdx].focus();
                }
            }
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                const row = input.closest('tr');
                const prevRow = row.previousElementSibling;
                if (prevRow) {
                    const cols = [...row.querySelectorAll('.marks-input')];
                    const colIdx = cols.indexOf(input);
                    const prevInputs = prevRow.querySelectorAll('.marks-input');
                    if (prevInputs[colIdx]) prevInputs[colIdx].focus();
                }
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', () => { 
    loadInternalsDropdown(); 
    loadEseMarksTable();
});
