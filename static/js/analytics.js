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
    const crimeHeader = document.getElementById('letterC');
    const crimeSection = document.getElementById('crimeSection');

    if (type === 'road') {
        roadHeader?.classList.remove('hidden');
        roadSection?.classList.remove('hidden');
        fireHeader?.classList.add('hidden');
        fireSection?.classList.add('hidden');
        crimeHeader?.classList.add('hidden');
        crimeSection?.classList.add('hidden');
    } else if (type === 'fire') {
        roadHeader?.classList.add('hidden');
        roadSection?.classList.add('hidden');
        fireHeader?.classList.remove('hidden');
        fireSection?.classList.remove('hidden');
        crimeHeader?.classList.add('hidden');
        crimeSection?.classList.add('hidden');
    } else if (type === 'crime') {
        roadHeader?.classList.add('hidden');
        roadSection?.classList.add('hidden');
        fireHeader?.classList.add('hidden');
        fireSection?.classList.add('hidden');
        crimeHeader?.classList.remove('hidden');
        crimeSection?.classList.remove('hidden');
    }

    const activeTab = document.querySelector('.tab.active');
    if (activeTab) {
        if (activeTab.textContent.toLowerCase() === 'daily') {
            filterDaily();
        } else if (activeTab.textContent.toLowerCase() === 'weekly') {
            filterWeekly();
        } else {
            filterData(activeTab.textContent.toLowerCase());
        }
    }
}

function setActiveTab(tabElement) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    tabElement.classList.add('active');
}

document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        setActiveTab(tab);
        if (tab.textContent.toLowerCase() === 'daily') {
            filterDaily();
        } else if (tab.textContent.toLowerCase() === 'weekly') {
            filterWeekly();
        } else {
            filterData(tab.textContent.toLowerCase());
        }
    });
});

function filterData(timeFilter) {
    const role = window.location.pathname.includes('bfp') ? 'bfp' :
                 window.location.pathname.includes('cdrrmo') ? 'cdrrmo' :
                 window.location.pathname.includes('pnp') ? 'pnp' : 'barangay';
    const location = role === 'barangay' || role === 'bfp' ? '{{ barangay }}'.toLowerCase() :
                     '{{ municipality }}'.toLowerCase();
    const url = `/api/${role}_analytics_data?time=${timeFilter}&${role === 'barangay' || role === 'bfp' ? 'barangay' : 'municipality'}=${location}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching data:', data.error);
                alert('Failed to load analytics data');
                return;
            }
            updateCharts(data);
        })
        .catch(err => {
            console.error('Analytics load error:', err);
            alert('Failed to load analytics data');
        });
}

function filterDaily() {
    const role = window.location.pathname.includes('bfp') ? 'bfp' :
                 window.location.pathname.includes('cdrrmo') ? 'cdrrmo' :
                 window.location.pathname.includes('pnp') ? 'pnp' : 'barangay';
    const location = role === 'barangay' || role === 'bfp' ? '{{ barangay }}'.toLowerCase() :
                     '{{ municipality }}'.toLowerCase();
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const dateStr = yesterday.toISOString().split('T')[0];
    document.getElementById('dailySelector').style.display = 'block';
    document.getElementById('weekSelector').style.display = 'none';
    document.getElementById('yesterdayDate').textContent = dateStr;

    const url = `/api/${role}_analytics_data?time=daily&${role === 'barangay' || role === 'bfp' ? 'barangay' : 'municipality'}=${location}&date=${dateStr}`;
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching data:', data.error);
                alert('Failed to load analytics data');
                return;
            }
            updateCharts(data);
        })
        .catch(err => {
            console.error('Analytics load error:', err);
            alert('Failed to load analytics data');
        });
}

function filterWeekly() {
    const role = window.location.pathname.includes('bfp') ? 'bfp' :
                 window.location.pathname.includes('cdrrmo') ? 'cdrrmo' :
                 window.location.pathname.includes('pnp') ? 'pnp' : 'barangay';
    const location = role === 'barangay' || role === 'bfp' ? '{{ barangay }}'.toLowerCase() :
                     '{{ municipality }}'.toLowerCase();
    document.getElementById('dailySelector').style.display = 'none';
    document.getElementById('weekSelector').style.display = 'block';
    const today = new Date();
    const weeks = [];
    for (let i = 0; i < 4; i++) {
        const weekStart = new Date(today);
        weekStart.setDate(today.getDate() - today.getDay() - (i * 7));
        weeks.push(weekStart.toISOString().split('T')[0]);
    }
    const weekButtons = document.getElementById('weekButtons');
    weekButtons.innerHTML = '';
    weeks.forEach((week, index) => {
        const btn = document.createElement('button');
        btn.textContent = `Week ${index + 1}`;
        btn.onclick = () => loadWeek(week);
        weekButtons.appendChild(btn);
    });
    loadWeek(weeks[0]);
}

function loadWeek(weekStart) {
    const role = window.location.pathname.includes('bfp') ? 'bfp' :
                 window.location.pathname.includes('cdrrmo') ? 'cdrrmo' :
                 window.location.pathname.includes('pnp') ? 'pnp' : 'barangay';
    const location = role === 'barangay' || role === 'bfp' ? '{{ barangay }}'.toLowerCase() :
                     '{{ municipality }}'.toLowerCase();
    const url = `/api/${role}_analytics_data?time=weekly&${role === 'barangay' || role === 'bfp' ? 'barangay' : 'municipality'}=${location}&week_start=${weekStart}`;
    
    document.getElementById('dateButtons').style.display = 'block';
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching weekly data:', data.error);
                alert('Failed to load weekly data');
                return;
            }
            const dateButtons = document.getElementById('dateButtons');
            dateButtons.innerHTML = '';
            data.dates.forEach(date => {
                const btn = document.createElement('button');
                btn.textContent = date;
                btn.onclick = () => {
                    const dailyUrl = `/api/${role}_analytics_data?time=daily&${role === 'barangay' || role === 'bfp' ? 'barangay' : 'municipality'}=${location}&date=${date}`;
                    fetch(dailyUrl)
                        .then(response => response.json())
                        .then(dayData => {
                            if (dayData.error) {
                                console.error('Error fetching daily data:', dayData.error);
                                alert('Failed to load daily data');
                                return;
                            }
                            updateCharts(dayData);
                        });
                };
                dateButtons.appendChild(btn);
            });
            const summaryDiv = document.getElementById('weeklySummary');
            summaryDiv.innerHTML = role === 'barangay' || role === 'bfp' ? `
                <h3>Week Summary</h3>
                <p>Total Alerts Received: ${data.summary.total_alerts}</p>
                <p>Total Responded Alerts: ${data.summary.total_responded}</p>
                <p>Total Road Accidents: ${data.summary.total_road_accidents}</p>
                <p>Most Common Accident Type: ${data.summary.most_common_accident_type}</p>
                <p>Most Common Cause: ${data.summary.most_common_cause}</p>
                <p>Most Common Weather: ${data.summary.most_common_weather}</p>
                <p>Most Common Road Condition: ${data.summary.most_common_road_condition}</p>
                <p>Most Common Vehicle Type: ${data.summary.most_common_vehicle_type}</p>
                <p>Most Common Driver Age: ${data.summary.most_common_driver_age}</p>
                <p>Most Common Driver Gender: ${data.summary.most_common_driver_gender}</p>
            ` : `
                <h3>Week Summary</h3>
                <p>Total Alerts Received: ${data.summary.total_alerts}</p>
                <p>Total Responded Alerts: ${data.summary.total_responded}</p>
                <p>Most Common Barangay: ${data.summary.most_common_barangay}</p>
                <p>Total Road Accidents: ${data.summary.total_road_accidents}</p>
                <p>Most Common Accident Type: ${data.summary.most_common_accident_type}</p>
                <p>Most Common Cause: ${data.summary.most_common_cause}</p>
                <p>Most Common Weather: ${data.summary.most_common_weather}</p>
                <p>Most Common Road Condition: ${data.summary.most_common_road_condition}</p>
                <p>Most Common Vehicle Type: ${data.summary.most_common_vehicle_type}</p>
                <p>Most Common Driver Age: ${data.summary.most_common_driver_age}</p>
                <p>Most Common Driver Gender: ${data.summary.most_common_driver_gender}</p>
            `;
            if (data.dates.length > 0) {
                const dailyUrl = `/api/${role}_analytics_data?time=daily&${role === 'barangay' || role === 'bfp' ? 'barangay' : 'municipality'}=${location}&date=${data.dates[0]}`;
                fetch(dailyUrl)
                    .then(response => response.json())
                    .then(dayData => {
                        if (dayData.error) {
                            console.error('Error fetching daily data:', dayData.error);
                            alert('Failed to load daily data');
                            return;
                        }
                        updateCharts(dayData);
                    });
            }
        })
        .catch(error => {
            console.error('Error fetching weekly data:', error);
            alert('Failed to load weekly data');
        });
}

function updateCharts(data) {
    const role = window.location.pathname.includes('bfp') ? 'bfp' :
                 window.location.pathname.includes('cdrrmo') ? 'cdrrmo' :
                 window.location.pathname.includes('pnp') ? 'pnp' : 'barangay';
    if (window.charts) {
        Object.values(window.charts).forEach(chart => chart.destroy());
    }
    window.charts = {};

    if (role === 'barangay' || role === 'cdrrmo' || role === 'pnp' || role === 'bfp') {
        renderLine('roadIncidentTrendsChart', data.trends.labels, [
            { label: 'Total Incidents', data: data.trends.total, borderColor: '#36A2EB', backgroundColor: 'rgba(54, 162, 235, 0.2)' },
            { label: 'Responded Incidents', data: data.trends.responded, borderColor: '#FF6384', backgroundColor: 'rgba(255, 99, 132, 0.2)' }
        ], 'Incident Trends');
        renderPie('roadAccidentDistributionChart', Object.keys(data.distribution).reduce((acc, k) => ({ ...acc, [k]: data.distribution[k].total }), {}), 'Accident Distribution');
        renderBar('roadRespondedAlertsChart', Object.keys(data.distribution), Object.values(data.distribution).map(d => d.responded), 'Responded Alerts');
        renderBar('roadCauseAnalysisChart', data.causes.road, 'Accident Cause');
        renderBar('roadAccidentTypeChart', data.types, 'Accident Type');
        renderPie('roadConditionChart', data.road_conditions, 'Road Condition');
        renderPie('roadWeatherChart', data.weather, 'Weather Condition');
        renderPie('roadVehicleTypesChart', data.vehicle_types, 'Vehicle Types');
        renderBar('roadDriverAgeChart', data.driver_age, 'Driver\'s Age');
        renderPie('roadDriverGenderChart', data.driver_gender, 'Driver\'s Gender');
    }

    if (role === 'barangay' || role === 'bfp') {
        renderLine('fireIncidentTrendsChart', data.trends.labels, [
            { label: 'Total Incidents', data: data.trends.total, borderColor: '#36A2EB', backgroundColor: 'rgba(54, 162, 235, 0.2)' },
            { label: 'Responded Incidents', data: data.trends.responded, borderColor: '#FF6384', backgroundColor: 'rgba(255, 99, 132, 0.2)' }
        ], 'Incident Trends');
        renderPie('fireIncidentDistributionChart', Object.keys(data.distribution).reduce((acc, k) => ({ ...acc, [k]: data.distribution[k].total }), {}), 'Incident Distribution');
        renderBar('fireRespondedAlertsChart', Object.keys(data.distribution), Object.values(data.distribution).map(d => d.responded), 'Responded Alerts');
        renderBar('fireCauseAnalysisChart', data.causes.fire, 'Fire Cause Analysis');
        renderPie('fireWeatherChart', data.weather, 'Weather Impact');
        renderPie('firePropertyTypeChart', data.property_types || {}, 'Property Type');
        renderBar('fireCauseChart', data.causes.fire, 'Fire Cause');
    }

    if (role === 'pnp') {
        renderLine('crimeIncidentTrendsChart', data.trends.labels, [
            { label: 'Total Incidents', data: data.trends.total, borderColor: '#36A2EB', backgroundColor: 'rgba(54, 162, 235, 0.2)' },
            { label: 'Responded Incidents', data: data.trends.responded, borderColor: '#FF6384', backgroundColor: 'rgba(255, 99, 132, 0.2)' }
        ], 'Incident Trends');
        renderPie('crimeIncidentDistributionChart', Object.keys(data.distribution).reduce((acc, k) => ({ ...acc, [k]: data.distribution[k].total }), {}), 'Incident Distribution');
        renderBar('crimeRespondedAlertsChart', Object.keys(data.distribution), Object.values(data.distribution).map(d => d.responded), 'Responded Alerts');
        renderBar('crimeTypeAnalysisChart', data.causes.road, 'Crime Type Analysis');
    }
}

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

function renderLine(canvasId, labels, datasets, title) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    if (window[canvasId]) window[canvasId].destroy();
    window[canvasId] = new Chart(ctx, {
        type: 'line',
        data: { 
            labels, 
            datasets: datasets.map(ds => ({
                label: ds.label,
                data: ds.data,
                borderColor: ds.borderColor,
                backgroundColor: ds.backgroundColor,
                fill: true
            }))
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

function renderBar(canvasId, objDataOrLabels, data, title) {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    let labels = Array.isArray(objDataOrLabels) ? objDataOrLabels : Object.keys(objDataOrLabels);
    let dataset = Array.isArray(data) ? data : Object.values(objDataOrLabels);
    if (window[canvasId]) window[canvasId].destroy();
    window[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: { 
            labels, 
            datasets: [{ 
                label: title, 
                data: dataset, 
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

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    const defaultTab = document.querySelector('.tab');
    if (defaultTab) {
        defaultTab.classList.add('active');
        filterData('today');
    }
});