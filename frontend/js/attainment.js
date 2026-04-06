const courseId = localStorage.getItem('selectedCourseId');
if (!courseId) { window.location.href = 'courses.html'; }

const PO_LIST = ['PO1','PO2','PO3','PO4','PO5','PO6','PO7','PO8','PO9','PO10','PO11','PO12','PSO1','PSO2'];
let coChartInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    calculateAttainment();
});

async function calculateAttainment() {
    showLoading();
    const res = await api.get(`/attainment/${courseId}/calculate`);
    hideLoading();

    if (!res.success) { 
        showNotification('Failed to calculate', 'error'); 
        return; 
    }

    const data = res.data;
    const coHead = document.getElementById('coAttainmentHeader');
    const coBody = document.getElementById('coAttainmentBody');
    
    if (!data.co_attainment || data.co_attainment.length === 0) {
        coBody.innerHTML = '<tr><td colspan="15">No data available</td></tr>';
        return;
    }

    // 1. Build Header
    let headHTML = '<tr><th class="sticky-col-co">CO\'s</th>';
    data.internals.forEach((inv, i) => {
        headHTML += `<th>INT ${i === 0 ? 'I' : (i === 1 ? 'II' : i + 1)}</th>`;
    });
    headHTML += `
        <th>Assignment</th>
        <th>Assessment (40%)</th>
        <th>ESE (100%)</th>
        <th>ESE (60%)</th>
        <th>DA (100%)</th>
        <th>DA (80%)</th>
        <th>DA Level</th>
        <th>IDA Level</th>
        <th class="column-highlight-overall">Overall</th>
    </tr>`;
    coHead.innerHTML = headHTML;

    // 2. Build Body & Calc Stats
    coBody.innerHTML = '';
    let successCount = 0;
    let highestVal = -1;
    let highestCO = '-';

    data.co_attainment.forEach(co => {
        const overall = co.overall || 0;
        if (overall >= 2.0) successCount++;
        if (overall > highestVal) {
            highestVal = overall;
            highestCO = `CO${co.co_number}`;
        }

        const daLvl = Math.round(co.da_level);
        const daClass = `level-${daLvl}`;
        const overallLvl = overall >= 2.5 ? 3 : (overall >= 1.5 ? 2 : 1);
        const overallClass = `level-${overallLvl}`;

        let tr = `<tr>
            <td class="sticky-col-co" style="font-weight:700; color:#4a5568;">CO${co.co_number}</td>`;
        
        // Individual Internal averages
        data.internals.forEach(inv => {
            const v = co.internals[inv.id];
            tr += `<td>${v !== undefined ? v.toFixed(1) : '0.0'}</td>`;
        });

        tr += `
            <td>${co.assignment.toFixed(1)}</td>
            <td>${co.assessment_40.toFixed(1)}</td>
            <td>${co.ese.toFixed(1)}</td>
            <td>${co.ese_60.toFixed(1)}</td>
            <td>${co.da_100.toFixed(1)}</td>
            <td>${co.da_80.toFixed(1)}</td>
            <td><span class="level-badge ${daClass}">${co.da_level.toFixed(1)}</span></td>
            <td>${co.ida_level.toFixed(1)}</td>
            <td class="column-highlight-overall">
                <span class="level-badge ${overallClass}">${overall.toFixed(2)}</span>
            </td>
        </tr>`;
        coBody.innerHTML += tr;
    });

    // 3. Update Dashboard Stats
    document.getElementById('statCourseAvg').textContent = data.course_attainment_avg.toFixed(2);
    document.getElementById('statSuccessRate').textContent = `${Math.round((successCount / data.co_attainment.length) * 100)}%`;
    document.getElementById('statHighestCO').textContent = highestCO;

    // 4. Update Footer
    const footer = document.getElementById('attainmentFooter');
    if (footer) {
        footer.classList.remove('hidden');
        document.getElementById('footerAvg').textContent = data.course_attainment_avg.toFixed(2);
    }

    // 5. Update PO mapping
    const poHead = document.getElementById('poAttainmentHeaderRow');
    const poBody = document.getElementById('poAttainmentBody');
    
    poHead.innerHTML = '<th>Outcome</th>';
    let vals = '<td style="background:#27ae60;color:#fff;font-weight:bold;">Class Avg</td>';
    PO_LIST.forEach(po => {
        poHead.innerHTML += `<th>${po}</th>`;
        const v = data.po_attainment[po];
        vals += `<td>${v !== undefined ? v : '-'}</td>`;
    });
    poBody.innerHTML = `<tr class="summary-row">${vals}</tr>`;

    // 6. Update Chart
    updateAttainmentChart(data.co_attainment);

    showNotification('Results Generated!', 'success');
}

function updateAttainmentChart(coData) {
    // Safety Check 1: Ensure Chart.js is actually loaded from CDN
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js library is not loaded. Graph will be skipped.');
        return;
    }

    // Safety Check 2: Ensure the canvas element exists in the DOM
    const canvas = document.getElementById('coAttainmentChart');
    if (!canvas) {
        console.error('Canvas element "coAttainmentChart" not found.');
        return;
    }

    const ctx = canvas.getContext('2d');
    
    const labels = coData.map(co => `CO${co.co_number}`);
    const values = coData.map(co => co.overall || 0);
    const colors = values.map(v => {
        if (v >= 2.5) return 'rgba(39, 174, 96, 0.7)'; // success
        if (v >= 1.5) return 'rgba(243, 156, 18, 0.7)'; // warning
        return 'rgba(231, 76, 60, 0.7)'; // danger
    });
    const borderColors = values.map(v => {
        if (v >= 2.5) return 'rgba(39, 174, 96, 1)';
        if (v >= 1.5) return 'rgba(243, 156, 18, 1)';
        return 'rgba(231, 76, 60, 1)';
    });

    if (coChartInstance) {
        coChartInstance.destroy();
    }

    try {
        coChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Overall Attainment Value',
                data: values,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 1,
                borderRadius: 5,
                barThickness: 40
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 3,
                    ticks: {
                        stepSize: 0.5,
                        font: { family: 'Outfit', size: 11 }
                    },
                    grid: { color: '#f0f0f0' },
                    title: {
                        display: true,
                        text: 'Attainment Level (0-3)',
                        font: { family: 'Outfit', weight: 'bold' }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Outfit', size: 12, weight: 'bold' } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(44, 62, 80, 0.9)',
                    titleFont: { family: 'Outfit', size: 14 },
                    bodyFont: { family: 'Outfit', size: 13 },
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return `Attainment: ${context.raw.toFixed(2)}`;
                        }
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
    } catch (e) {
        console.error('Error rendering chart:', e);
    }
}

function exportToExcel() {
    const courseId = localStorage.getItem('selectedCourseId');
    if (!courseId) return;
    
    showNotification('Preparing Excel Report...', 'info');
    // Using simple window.location for file download
    window.location.href = `/api/export/${courseId}/excel`;
}
