// analytics.js
document.addEventListener('DOMContentLoaded', () => {
    updateCharts();
});

function updateCharts(timeFilter = 'today') {
    // Determine role from path
    const path = window.location.pathname;
    let role = 'all';
    let endpoint = '/api/barangay_analytics_data';
    let location = '';
    if (path.includes('barangay')) {
        role = 'barangay';
        endpoint = '/api/barangay_analytics_data';
        location = `&barangay=${path.split('/').pop().toLowerCase()}`;
    } else if (path.includes('cdrrmo')) {
        role = 'cdrrmo';
        endpoint = '/api/cdrrmo_analytics_data';
        location = `&municipality=${path.split('/').pop().toLowerCase()}`;
    } else if (path.includes('pnp')) {
        role = 'pnp';
        endpoint = '/api/pnp_analytics_data';
        location = `&municipality=${path.split('/').pop().toLowerCase()}`;
    } else if (path.includes('bfp')) {
        role = 'bfp';
        endpoint = '/api/bfp_analytics_data';
        location = `&municipality=${path.split('/').pop().toLowerCase()}`;
    }

    // Fetch analytics data
    fetch(`${endpoint}?time=${timeFilter}&role=${role}${location}`)
        .then(res => res.json())
        .then(data => {
            if (role === 'barangay' || role === 'cdrrmo' || role === 'pnp') {
                renderLine('roadIncidentTrendsChart', data.trends.labels, data.trends.total, 'Total Incidents');
                renderPie('roadAccidentDistributionChart', data.distribution, 'Accident Distribution');
                renderPie('roadRespondedAlertsChart', data.responded, 'Responded Alerts');
                renderBar('roadCauseAnalysisChart', data.causes.road, 'Accident Cause');
                renderBar('roadAccidentTypeChart', data.accident_types, 'Accident Type');
                renderBar('roadConditionChart', data.road_conditions, 'Road Condition');
                renderBar('roadWeatherChart', data.weather, 'Weather Condition');
                renderBar('roadVehicleTypesChart', data.vehicle_types, 'Vehicle Types');
                renderBar('roadDriverAgeChart', data.driver_age, 'Driver Age Groups');
                renderBar('roadDriverGenderChart', data.driver_gender, 'Driver Gender');
            }
            if (role === 'barangay' || role === 'bfp') {
                renderLine('fireIncidentTrendsChart', data.trends.labels, data.trends.total, 'Total Incidents');
                renderPie('fireIncidentDistributionChart', data.distribution, 'Incident Distribution');
                renderPie('fireRespondedAlertsChart', data.responded, 'Responded Alerts');
                renderBar('fireCauseAnalysisChart', data.causes.fire, 'Fire Cause Analysis');
                renderBar('fireWeatherChart', data.weather, 'Weather Impact');
                renderBar('firePropertyTypeChart', data.property_types, 'Property Type');
                renderBar('fireCauseChart', data.causes.fire, 'Fire Cause');
            }
        })
        .catch(err => console.error('Analytics load error:', err));
}

// Helpers
function renderPie(canvasId, objData, title) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    if (window[canvasId]) window[canvasId].destroy();
    window[canvasId] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(objData),
            datasets: [{ data: Object.values(objData), backgroundColor: generateColors(objData) }]
        },
        options: { 
            responsive: true, 
            plugins: { 
                title: { display: true, text: title },
                legend: { position: 'top' }
            }
        }
    });
}

function renderLine(canvasId, labels, dataSet, label) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    if (window[canvasId]) window[canvasId].destroy();
    window[canvasId] = new Chart(ctx, {
        type: 'line',
        data: { 
            labels, 
            datasets: [{ 
                label, 
                data: dataSet, 
                borderColor: '#36A2EB', 
                backgroundColor: 'rgba(54, 162, 235, 0.2)', 
                fill: true 
            }] 
        },
        options: { 
            responsive: true,
            plugins: { 
                title: { display: true, text: label }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderBar(canvasId, objDataOrLabels, title, overrideData = null) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    let labels, data;
    if (overrideData) {
        labels = objDataOrLabels;
        data = overrideData;
    } else {
        labels = Object.keys(objDataOrLabels);
        data = Object.values(objDataOrLabels);
    }
    if (window[canvasId]) window[canvasId].destroy();
    window[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: { 
            labels, 
            datasets: [{ 
                label: title, 
                data, 
                backgroundColor: '#36A2EB',
                borderColor: '#36A2EB',
                borderWidth: 1
            }] 
        },
        options: { 
            responsive: true,
            plugins: { 
                title: { display: true, text: title }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function generateColors(obj) {
    const palette = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#8A2BE2', '#00CED1', '#FF4500', '#2E8B57'];
    return Object.keys(obj).map((_, i) => palette[i % palette.length]);
}