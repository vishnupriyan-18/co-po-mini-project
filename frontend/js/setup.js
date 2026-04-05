// Setup Module - CO Pool, Internals, and Structure Configuration

// ============== CO POOL SETUP ==============

function generateCOPoolDisplay() {
    const totalCO = parseInt(document.getElementById('totalCO').value) || 0;
    const container = document.getElementById('coMaxMarksContainer');

    if (totalCO < 1) {
        container.innerHTML = '';
        return;
    }

    let html = '<div class="co-pool-display">';
    html += '<p class="text-muted">COs available: ';
    for (let i = 1; i <= totalCO; i++) {
        html += `<span class="badge">CO${i}</span> `;
    }
    html += '</p><p class="text-muted"><small>Max marks will be set per internal below</small></p></div>';
    container.innerHTML = html;

    // Regenerate internal forms whenever CO count changes
    generateInternalForms();
}

// ============== INTERNAL SETUP ==============

function generateInternalForms() {
    const count = parseInt(document.getElementById('internalCount').value) || 0;
    const container = document.getElementById('internalsContainer');

    if (count < 1) {
        container.innerHTML = '';
        return;
    }

    const totalCO = parseInt(document.getElementById('totalCO').value) || 0;

    let html = '';
    for (let i = 1; i <= count; i++) {
        html += `
            <div class="internal-setup-card" data-internal-index="${i}">
                <div class="internal-setup-header">
                    <span class="internal-setup-title">Internal ${i}</span>
                </div>

                <div class="form-group">
                    <label class="form-label">Select COs for this Internal:</label>
                    <div class="co-checkbox-group" id="coCheckboxes_${i}">
                        ${generateCOCheckboxesHTML(i, totalCO)}
                    </div>
                </div>

                <div class="mt-2">
                    <label class="form-label">CO Maximum Marks</label>
                    <div class="config-grid" id="coMaxMarks_${i}"></div>
                </div>

                <div class="form-group">
                    <label class="form-label">Number of Assignments</label>
                    <input type="number" class="form-control assignment-count"
                           data-internal="${i}" min="0" max="10" value="2"
                           style="width:120px;"
                           oninput="generateAssignmentMarksInputs(${i})">
                </div>

                <div class="mt-2">
                    <label class="form-label">Assignment Maximum Marks</label>
                    <div class="config-grid" id="assignmentMarks_${i}"></div>
                </div>
            </div>
        `;
    }

    container.innerHTML = html;

    for (let i = 1; i <= count; i++) {
        generateAssignmentMarksInputs(i);
    }
}

// Generates CO checkboxes based on CURRENT totalCO value (not hardcoded 5)
function generateCOCheckboxesHTML(internalIndex, totalCO) {
    if (totalCO < 1) {
        return '<p class="text-muted">Please set the number of COs first (Step 1)</p>';
    }

    let html = '<div style="display:flex;flex-wrap:wrap;gap:15px;">';
    for (let i = 1; i <= totalCO; i++) {
        html += `
            <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
                <input type="checkbox" class="co-checkbox"
                       data-internal="${internalIndex}" value="${i}"
                       onchange="updateCOMaxMarks(${internalIndex})">
                <span>CO${i}</span>
            </label>
        `;
    }
    html += '</div>';
    return html;
}

function updateCOMaxMarks(internalIndex) {
    const container = document.getElementById(`coMaxMarks_${internalIndex}`);
    const selectedCOs = [];

    document.querySelectorAll(`.co-checkbox[data-internal="${internalIndex}"]:checked`).forEach(cb => {
        selectedCOs.push(parseInt(cb.value));
    });

    let html = '';
    selectedCOs.forEach(coNum => {
        html += `
            <div class="config-item">
                <label>CO${coNum} Max Marks</label>
                <input type="number" class="form-control co-max-mark"
                       data-internal="${internalIndex}" data-co="${coNum}"
                       value="10" min="1" max="100">
            </div>
        `;
    });

    container.innerHTML = html;
}

function generateAssignmentMarksInputs(internalIndex) {
    const countInput = document.querySelector(`.assignment-count[data-internal="${internalIndex}"]`);
    const count = parseInt(countInput ? countInput.value : 0) || 0;
    const container = document.getElementById(`assignmentMarks_${internalIndex}`);

    let html = '';
    for (let i = 1; i <= count; i++) {
        html += `
            <div class="config-item">
                <label>A${i} Max Marks</label>
                <input type="number" class="form-control assignment-max-mark"
                       data-internal="${internalIndex}" data-assignment="${i}"
                       value="5" min="1" max="100">
            </div>
        `;
    }
    container.innerHTML = html;
}

// ============== SAVE ALL ==============

async function saveAllSetup() {
    const courseId = localStorage.getItem('selectedCourseId');
    if (!courseId) {
        showNotification('No course selected', 'error');
        return;
    }

    const totalCO = parseInt(document.getElementById('totalCO').value);
    if (!totalCO || totalCO < 1) {
        showNotification('Please enter valid number of COs', 'error');
        return;
    }

    showLoading();

    // Step 1: Save CO Pool for this course
    let result = await api.post(`/co/${courseId}/setup`, { total_co: totalCO });
    if (!result.success) {
        hideLoading();
        showNotification('Failed to save CO Pool: ' + (result.message || ''), 'error');
        return;
    }

    // Step 2: Create Internals for this course
    const internalCount = parseInt(document.getElementById('internalCount').value);
    if (!internalCount || internalCount < 1) {
        hideLoading();
        showNotification('Please enter valid number of internals', 'error');
        return;
    }

    result = await api.post(`/internals/${courseId}/setup`, { count: internalCount });
    if (!result.success) {
        hideLoading();
        showNotification('Failed to create internals: ' + (result.message || ''), 'error');
        return;
    }

    const internals = result.data;

    // Step 3: Setup each internal
    for (let i = 0; i < internals.length; i++) {
        const internalId = internals[i].id;
        const internalIndex = i + 1;

        const coData = [];
        document.querySelectorAll(`.co-checkbox[data-internal="${internalIndex}"]:checked`).forEach(cb => {
            const coNumber = parseInt(cb.value);
            const maxMarksInput = document.querySelector(`.co-max-mark[data-internal="${internalIndex}"][data-co="${coNumber}"]`);
            coData.push({
                co_number: coNumber,
                max_marks: parseFloat(maxMarksInput?.value) || 10
            });
        });

        if (coData.length === 0) {
            hideLoading();
            showNotification(`Please select at least one CO for Internal ${internalIndex}`, 'error');
            return;
        }

        const coResult = await api.post(`/internals/detail/${internalId}/co`, { co_data: coData });
        if (!coResult.success) {
            hideLoading();
            showNotification(`Failed to save CO mapping for Internal ${internalIndex}: ` + (coResult.message || ''), 'error');
            return;
        }

        const assignmentCount = parseInt(document.querySelector(`.assignment-count[data-internal="${internalIndex}"]`).value) || 0;
        const assignmentMarks = {};
        document.querySelectorAll(`.assignment-max-mark[data-internal="${internalIndex}"]`).forEach(input => {
            assignmentMarks[`A${input.dataset.assignment}`] = parseFloat(input.value) || 5;
        });

        const assignResult = await api.post(`/internals/detail/${internalId}/assignments`, {
            assignment_count: assignmentCount,
            assignment_marks: assignmentMarks
        });
        if (!assignResult.success) {
            hideLoading();
            showNotification(`Failed to save assignments for Internal ${internalIndex}: ` + (assignResult.message || ''), 'error');
            return;
        }
    }

    // Step 4: Save DA Level Thresholds
    const l3 = parseFloat(document.getElementById('lvl3Threshold').value) || 85.0;
    const l2 = parseFloat(document.getElementById('lvl2Threshold').value) || 75.0;
    const l1 = parseFloat(document.getElementById('lvl1Threshold').value) || 60.0;
    const daConfRes = await api.post(`/attainment/${courseId}/da-config`, {
        level_3: l3, level_2: l2, level_1: l1
    });

    // Step 5: Map Matrix
    const mappings = [];
    const pList = ['PO1', 'PO2', 'PO3', 'PO4', 'PO5', 'PO6', 'PO7', 'PO8', 'PO9', 'PO10', 'PO11', 'PO12', 'PSO1', 'PSO2'];
    for (let i = 1; i <= totalCO; i++) {
        pList.forEach(po => {
            const v = document.getElementById(`map_${i}_${po}`)?.value.trim();
            if (v === '1' || v === '2' || v === '3') {
                mappings.push({ co_number: i, po_name: po, correlation_level: parseInt(v) });
            }
        });
    }

    await api.post(`/attainment/${courseId}/mapping`, { mappings: mappings });

    // Step 6: Save Grade Mapping
    const gradeMappings = [];
    document.querySelectorAll('#gradeMappingBody tr').forEach(row => {
        const grade = row.querySelector('.grade-name').value.trim();
        const marks = parseFloat(row.querySelector('.grade-marks').value) || 0;
        if (grade) {
            gradeMappings.push({ grade, marks_equivalent: marks });
        }
    });
    await api.post(`/attainment/${courseId}/grade-mapping`, { mappings: gradeMappings });

    hideLoading();
    showNotification('Setup saved successfully!', 'success');
}

// ============== LOAD EXISTING SETUP ==============

async function loadExistingSetup() {
    const courseId = localStorage.getItem('selectedCourseId');
    if (!courseId) return;

    // Load CO Pool
    const coResult = await api.get(`/co/${courseId}`);
    if (coResult.success && coResult.total_co > 0) {
        document.getElementById('totalCO').value = coResult.total_co;
    }

    // Generate CO pool display
    generateCOPoolDisplay();

    const totalCO = parseInt(document.getElementById('totalCO').value) || 0;
    let mHTML = '';
    const pList = ['PO1', 'PO2', 'PO3', 'PO4', 'PO5', 'PO6', 'PO7', 'PO8', 'PO9', 'PO10', 'PO11', 'PO12', 'PSO1', 'PSO2'];
    for (let i = 1; i <= totalCO; i++) {
        let tdHtml = '';
        pList.forEach(po => {
            tdHtml += `<td><input type="text" id="map_${i}_${po}" class="form-control" style="width:40px;height:30px;text-align:center;padding:2px;margin:auto;" placeholder="-"></td>`;
        });
        mHTML += `<tr><td><b>CO${i}</b></td>${tdHtml}</tr>`;
    }
    const mb = document.getElementById('mappingBody');
    if (mb) mb.innerHTML = mHTML;

    // Load internals
    const internalsResult = await api.get(`/internals/${courseId}`);
    if (internalsResult.success && internalsResult.data.length > 0) {
        document.getElementById('internalCount').value = internalsResult.data.length;
    }

    // Generate internal forms (uses current totalCO value)
    generateInternalForms();

    // If existing internals, load their configuration
    if (internalsResult.success && internalsResult.data.length > 0) {
        internalsResult.data.forEach(async (internal, idx) => {
            const internalIndex = idx + 1;
            const detailResult = await api.get(`/internals/detail/${internal.id}`);

            if (detailResult.success) {
                const data = detailResult.data;

                // Check the COs that were previously selected
                data.co_list.forEach(co => {
                    const checkbox = document.querySelector(`.co-checkbox[data-internal="${internalIndex}"][value="${co.co_number}"]`);
                    if (checkbox) checkbox.checked = true;
                });

                // Generate max marks inputs
                updateCOMaxMarks(internalIndex);

                // Set saved max marks values
                data.co_list.forEach(co => {
                    const maxMarksInput = document.querySelector(`.co-max-mark[data-internal="${internalIndex}"][data-co="${co.co_number}"]`);
                    if (maxMarksInput) maxMarksInput.value = co.max_marks;
                });

                // Set assignment count
                const assignInput = document.querySelector(`.assignment-count[data-internal="${internalIndex}"]`);
                if (assignInput) {
                    assignInput.value = data.assignments.length;
                    generateAssignmentMarksInputs(internalIndex);
                }

                // Set assignment marks
                data.assignments.forEach(assign => {
                    const input = document.querySelector(`.assignment-max-mark[data-internal="${internalIndex}"][data-assignment="${assign.assignment_number}"]`);
                    if (input) input.value = assign.max_marks;
                });
            }
        });
    }

    // Load DA configuration
    const daConfigRes = await api.get(`/attainment/${courseId}/da-config`);
    if (daConfigRes.success && daConfigRes.data) {
        const d = daConfigRes.data;
        const o3 = document.getElementById('lvl3Threshold');
        const o2 = document.getElementById('lvl2Threshold');
        const o1 = document.getElementById('lvl1Threshold');
        if (o3) o3.value = d.level_3;
        if (o2) o2.value = d.level_2;
        if (o1) o1.value = d.level_1;
    }
    
    // Load Maps
    const mapRes = await api.get(`/attainment/${courseId}/mapping`);
    if(mapRes.success && mapRes.data) {
        mapRes.data.forEach(m => {
             const inP = document.getElementById(`map_${m.co_number}_${m.po_name}`);
             if(inP) inP.value = (m.correlation_level === 0 ? '-' : m.correlation_level);
        });
    }

    // Load Grade Mapping
    const gradeRes = await api.get(`/attainment/${courseId}/grade-mapping`);
    const gBody = document.getElementById('gradeMappingBody');
    if (gBody) {
        gBody.innerHTML = '';
        if (gradeRes.success && gradeRes.data && gradeRes.data.length > 0) {
            gradeRes.data.forEach(g => addGradeRow(g.grade, g.marks_equivalent));
        } else {
            // Defaults
            const defaults = [
                {g:'O', m:100}, {g:'A+', m:90}, {g:'A', m:80}, 
                {g:'B+', m:70}, {g:'B', m:60}, {g:'C', m:50}, {g:'U', m:0}
            ];
            defaults.forEach(d => addGradeRow(d.g, d.m));
        }
    }
}

function addGradeRow(grade = '', marks = '') {
    const tbody = document.getElementById('gradeMappingBody');
    if (!tbody) return;
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" class="form-control grade-name" value="${grade}" placeholder="e.g. O"></td>
        <td><input type="number" class="form-control grade-marks" value="${marks}" step="0.1" placeholder="0.0"></td>
        <td><button class="btn btn-danger btn-sm" onclick="this.closest('tr').remove()">remove</button></td>
    `;
    tbody.appendChild(tr);
}
