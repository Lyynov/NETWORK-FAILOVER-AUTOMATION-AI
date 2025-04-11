// dashboard/static/js/charts.js

// Global variables
let metricsChart = null;
let currentMetricType = 'latency';
let interfaceData = {};

// Initialize the dashboard
function initDashboard() {
    Promise.all([
        fetch('/api/status').then(response => response.json()),
        fetch('/api/metrics').then(response => response.json())
    ])
    .then(([statusData, metricsData]) => {
        // Process and store metrics data
        processMetricsData(metricsData);
        
        // Update interface status cards
        updateInterfaceStatusCards(statusData.interfaces);
        
        // Update events table
        updateEventsTable(statusData.recent_events);
        
        // Initialize metrics chart
        initMetricsChart();
    })
    .catch(error => {
        console.error('Error initializing dashboard:', error);
    });
}

// Process metrics data
function processMetricsData(metricsData) {
    // Group metrics by interface
    interfaceData = {};
    
    metricsData.forEach(metric => {
        const interfaceName = metric.interface;
        
        if (!interfaceData[interfaceName]) {
            interfaceData[interfaceName] = {
                timestamps: [],
                latency: [],
                packet_loss: [],
                bandwidth_usage: []
            };
        }
        
        // Convert timestamp to readable format
        const date = new Date(metric.timestamp);
        const formattedTime = date.toLocaleTimeString();
        
        interfaceData[interfaceName].timestamps.push(formattedTime);
        interfaceData[interfaceName].latency.push(metric.latency);
        interfaceData[interfaceName].packet_loss.push(metric.packet_loss);
        interfaceData[interfaceName].bandwidth_usage.push(metric.bandwidth_usage);
    });
    
    // Sort data by timestamp for each interface
    for (const interfaceName in interfaceData) {
        const indices = Array.from(interfaceData[interfaceName].timestamps.keys());
        indices.sort((a, b) => {
            return new Date(interfaceData[interfaceName].timestamps[a]) - 
                   new Date(interfaceData[interfaceName].timestamps[b]);
        });
        
        // Reorder all arrays based on sorted indices
        interfaceData[interfaceName].timestamps = indices.map(i => interfaceData[interfaceName].timestamps[i]);
        interfaceData[interfaceName].latency = indices.map(i => interfaceData[interfaceName].latency[i]);
        interfaceData[interfaceName].packet_loss = indices.map(i => interfaceData[interfaceName].packet_loss[i]);
        interfaceData[interfaceName].bandwidth_usage = indices.map(i => interfaceData[interfaceName].bandwidth_usage[i]);
    }
}

// Update dashboard data
function updateDashboard() {
    Promise.all([
        fetch('/api/status').then(response => response.json()),
        fetch('/api/metrics').then(response => response.json())
    ])
    .then(([statusData, metricsData]) => {
        // Process and store metrics data
        processMetricsData(metricsData);
        
        // Update interface status cards
        updateInterfaceStatusCards(statusData.interfaces);
        
        // Update events table
        updateEventsTable(statusData.recent_events);
        
        // Update metrics chart
        updateMetricsChart(currentMetricType);
    })
    .catch(error => {
        console.error('Error updating dashboard:', error);
    });
}

// Update interface status cards
function updateInterfaceStatusCards(interfaces) {
    const statusCardsContainer = document.getElementById('interface-status-cards');
    
    // Clear existing cards
    statusCardsContainer.innerHTML = '';
    
    // Create a card for each interface
    interfaces.forEach(interface => {
        const statusColor = interface.status === 'up' ? 'success' : 
                            interface.status === 'down' ? 'danger' : 'warning';
        
        const card = document.createElement('div');
        card.className = 'col-md-4 mb-3';
        
        card.innerHTML = `
            <div class="card h-100 border-${statusColor}">
                <div class="card-header bg-${statusColor} bg-opacity-25">
                    <h5 class="card-title mb-0">${interface.interface}</h5>
                </div>
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-2">
                        <span>Status:</span>
                        <span class="badge bg-${statusColor}">${interface.status.toUpperCase()}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Latency:</span>
                        <span>${interface.latency ? interface.latency.toFixed(2) + ' ms' : 'N/A'}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Packet Loss:</span>
                        <span>${interface.packet_loss ? interface.packet_loss.toFixed(2) + '%' : 'N/A'}</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span>Last Update:</span>
                        <span>${new Date(interface.timestamp).toLocaleString()}</span>
                    </div>
                </div>
            </div>
        `;
        
        statusCardsContainer.appendChild(card);
    });
}

// Update events table
function updateEventsTable(events) {
    const eventsTable = document.getElementById('events-table');
    
    // Clear existing rows
    eventsTable.innerHTML = '';
    
    if (events.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="4" class="text-center">No failover events recorded</td>';
        eventsTable.appendChild(row);
        return;
    }
    
    // Create a row for each event
    events.forEach(event => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${new Date(event.timestamp).toLocaleString()}</td>
            <td>${event.from_interface}</td>
            <td>${event.to_interface}</td>
            <td>${event.reason}</td>
        `;
        
        eventsTable.appendChild(row);
    });
}

// Initialize metrics chart
function initMetricsChart() {
    const ctx = document.getElementById('metrics-chart').getContext('2d');
    
    // Create datasets for each interface
    const datasets = [];
    const colors = ['#0d6efd', '#dc3545', '#198754', '#ffc107', '#6f42c1', '#fd7e14'];
    
    let colorIndex = 0;
    for (const interfaceName in interfaceData) {
        const color = colors[colorIndex % colors.length];
        colorIndex++;
        
        datasets.push({
            label: interfaceName,
            data: interfaceData[interfaceName][currentMetricType],
            backgroundColor: color,
            borderColor: color,
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 3
        });
    }
    
    // Create the chart
    metricsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Object.values(interfaceData)[0]?.timestamps || [],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: getMetricTitle(currentMetricType)
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: getMetricUnit(currentMetricType)
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

// Update metrics chart with new data
function updateMetricsChart(metricType) {
    currentMetricType = metricType;
    
    if (!metricsChart) return;
    
    // Update chart title
    metricsChart.options.plugins.title.text = getMetricTitle(metricType);
    
    // Update y-axis label
    metricsChart.options.scales.y.title.text = getMetricUnit(metricType);
    
    // Update labels (timestamps)
    metricsChart.data.labels = Object.values(interfaceData)[0]?.timestamps || [];
    
    // Update datasets
    metricsChart.data.datasets.forEach((dataset, index) => {
        const interfaceName = dataset.label;
        if (interfaceData[interfaceName]) {
            dataset.data = interfaceData[interfaceName][metricType];
        }
    });
    
    // Update the chart
    metricsChart.update();
}

// Get metric title based on metric type
function getMetricTitle(metricType) {
    switch(metricType) {
        case 'latency':
            return 'Network Latency Over Time';
        case 'packet_loss':
            return 'Packet Loss Over Time';
        case 'bandwidth_usage':
            return 'Bandwidth Usage Over Time';
        default:
            return 'Network Metrics';
    }
}

// Get metric unit based on metric type
function getMetricUnit(metricType) {
    switch(metricType) {
        case 'latency':
            return 'Latency (ms)';
        case 'packet_loss':
            return 'Packet Loss (%)';
        case 'bandwidth_usage':
            return 'Bandwidth (KB/s)';
        default:
            return '';
    }
}