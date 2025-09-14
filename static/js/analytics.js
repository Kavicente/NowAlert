// Shared JavaScript functions for analytics pages
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    sidebar.classList.toggle('active');
    mainContent.classList.toggle('shifted');
}

function showSection(type) {
    const roadHeader = document.getElementById('letterR');
    const roadSection = document.getElementById('roadSection');
    const fireHeader = document.getElementById('letterF');
    const fireSection = document.getElementById('fireSection');

    if (type === 'road') {
        roadHeader.classList.remove('hidden');
        roadSection.classList.remove('hidden');
        fireHeader.classList.add('hidden');
        fireSection.classList.add('hidden');
    } else if (type === 'fire') {
        roadHeader.classList.add('hidden');
        roadSection.classList.add('hidden');
        fireHeader.classList.remove('hidden');
        fireSection.classList.remove('hidden');
    }

    // Trigger data refresh for the active time period
    const activeTab = document.querySelector('.tab.active');
    if (activeTab) {
        filterData(activeTab.textContent.toLowerCase());
    }
}

function setActiveTab(tabElement) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    tabElement.classList.add('active');
}

// Ensure tabs trigger data refresh
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        setActiveTab(tab);
        filterData(tab.textContent.toLowerCase());
    });
});

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    // Set default tab
    const defaultTab = document.querySelector('.tab');
    if (defaultTab) {
        defaultTab.classList.add('active');
        filterData('today');
    }
});
// Initial load and update charts
function updateCharts(timeFilter, submittedData = null) {
    const role = window.location.pathname.includes('bfp') ? 'bfp' :
                 window.location.pathname.includes('cdrrmo') ? 'cdrrmo' :
                 window.location.pathname.includes('pnp') ? 'pnp' : 'barangay';
    const location = role === 'barangay' || role === 'bfp' ? '{{ barangay }}'.toLowerCase() :
                     '{{ municipality }}'.toLowerCase();
    const url = `/api/${role}_analytics_data?time=${timeFilter}&${role === 'barangay' || role === 'bfp' ? 'barangay' : 'municipality'}=${location}`;

    fetch(submittedData ? null : url)
        .then(response => submittedData ? Promise.resolve({ json: () => Promise.resolve({ data: submittedData }) }) : response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching data:', data.error);
                return;
            }
            const d = data.data || data;
            if (role === 'barangay' || role === 'cdrrmo' || role === 'pnp') {
                renderLine('roadIncidentTrendsChart', d.trends.labels, d.trends.total, 'Incident Trends');
                renderPie('roadAccidentDistributionChart', d.distribution, 'Accident Distribution');
                renderPie('roadRespondedAlertsChart', d.responded, 'Responded Alerts');
                renderBar('roadCauseAnalysisChart', d.causes.road, 'Accident Cause');
                renderBar('roadAccidentTypeChart', d.accident_types, 'Accident Type');
                renderBar('roadConditionChart', d.road_conditions, 'Road Condition');
                renderBar('roadWeatherChart', d.weather, 'Weather Condition');
                renderBar('roadVehicleTypesChart', d.vehicle_types, 'Vehicle Types');
                renderBar('roadDriverAgeChart', d.driver_age, 'Driver\'s Age');
                renderBar('roadDriverGenderChart', d.driver_gender, 'Driver\'s Gender');
            }
            if (role === 'barangay' || role === 'bfp') {
                renderLine('fireIncidentTrendsChart', d.trends.labels, d.trends.total, 'Incident Trends');
                renderPie('fireIncidentDistributionChart', d.distribution, 'Incident Distribution');
                renderPie('fireRespondedAlertsChart', d.responded, 'Responded Alerts');
                renderBar('fireCauseAnalysisChart', d.causes.fire, 'Fire Cause Analysis');
                renderBar('fireWeatherChart', d.weather, 'Weather Impact');
                renderBar('firePropertyTypeChart', d.property_types, 'Property Type');
                renderBar('fireCauseChart', d.causes.fire, 'Fire Cause');
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