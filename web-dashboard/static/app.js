// Socket.IO Connection
const socket = io();

// Charts
let tempChart, humidChart;
const maxDataPoints = 20;

// Thresholds
const TEMP_MAX = 35.0;
const TEMP_MIN = 15.0;
const TEMP_FAN_ON = 30.0;
const HUMID_MAX = 80.0;
const HUMID_MIN = 30.0;
const LIGHT_MIN_LUX = 200.0;
const GAS_THRESHOLD_PPM = 300.0;

// Initialize Charts
function initCharts() {
    const chartConfig = {
        type: 'line',
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 500
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: true
                }
            }
        }
    };

    const tempCtx = document.getElementById('tempChart').getContext('2d');
    tempChart = new Chart(tempCtx, {
        ...chartConfig,
        data: {
            labels: [],
            datasets: [{
                label: 'Temperature (°C)',
                data: [],
                borderColor: 'rgb(239, 68, 68)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.4
            }]
        }
    });

    const humidCtx = document.getElementById('humidChart').getContext('2d');
    humidChart = new Chart(humidCtx, {
        ...chartConfig,
        data: {
            labels: [],
            datasets: [{
                label: 'Humidity (%)',
                data: [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4
            }]
        }
    });
}

// Load ThingSpeak Historical Data
async function loadThingSpeakData() {
    try {
        console.log('📥 Loading ThingSpeak data...');
        const response = await fetch('/api/thingspeak');
        const data = await response.json();
        
        if (data.feeds && data.feeds.length > 0) {
            console.log(`✓ Loaded ${data.feeds.length} records`);
            
            tempChart.data.labels = [];
            tempChart.data.datasets[0].data = [];
            humidChart.data.labels = [];
            humidChart.data.datasets[0].data = [];
            
            data.feeds.slice().reverse().forEach(feed => {
                const timestamp = new Date(feed.created_at).toLocaleTimeString();
                
                if (feed.field1) {
                    tempChart.data.labels.push(timestamp);
                    tempChart.data.datasets[0].data.push(parseFloat(feed.field1));
                }
                
                if (feed.field2) {
                    humidChart.data.labels.push(timestamp);
                    humidChart.data.datasets[0].data.push(parseFloat(feed.field2));
                }
            });
            
            tempChart.update();
            humidChart.update();
            
            showAlert('success', 'Data Loaded', `Loaded ${data.feeds.length} records from ThingSpeak`);
        } else {
            console.warn('⚠️ No data in ThingSpeak');
            showAlert('warning', 'No Data', 'No historical data available');
        }
    } catch (error) {
        console.error('✗ Error loading ThingSpeak:', error);
        showAlert('danger', 'Error', 'Failed to load data: ' + error.message);
    }
}

// Update Charts with Real-time Data
function updateCharts(data) {
    const time = new Date().toLocaleTimeString();

    if (tempChart.data.labels.length >= maxDataPoints) {
        tempChart.data.labels.shift();
        tempChart.data.datasets[0].data.shift();
    }
    tempChart.data.labels.push(time);
    tempChart.data.datasets[0].data.push(data.temp);
    tempChart.update('none');

    if (humidChart.data.labels.length >= maxDataPoints) {
        humidChart.data.labels.shift();
        humidChart.data.datasets[0].data.shift();
    }
    humidChart.data.labels.push(time);
    humidChart.data.datasets[0].data.push(data.humid);
    humidChart.update('none');
}

// Update UI
function updateUI(data) {
    console.log('🔄 Updating UI:', data);
    
    document.getElementById('timestamp').textContent = data.timestamp || new Date().toLocaleTimeString();

    // Temperature
    document.getElementById('temp-value').textContent = `${data.temp.toFixed(1)}°C`;
    const tempStatus = document.getElementById('temp-status');
    if (data.temp > TEMP_MAX) {
        tempStatus.textContent = '⚠️ Too Hot';
        tempStatus.style.color = '#ef4444';
    } else if (data.temp < TEMP_MIN) {
        tempStatus.textContent = '❄️ Too Cold';
        tempStatus.style.color = '#3b82f6';
    } else {
        tempStatus.textContent = '✓ Normal';
        tempStatus.style.color = '#10b981';
    }

    // Humidity
    document.getElementById('humid-value').textContent = `${data.humid.toFixed(1)}%`;
    const humidStatus = document.getElementById('humid-status');
    if (data.humid > HUMID_MAX) {
        humidStatus.textContent = '⚠️ Too Humid';
        humidStatus.style.color = '#ef4444';
    } else if (data.humid < HUMID_MIN) {
        humidStatus.textContent = '⚠️ Too Dry';
        humidStatus.style.color = '#f59e0b';
    } else {
        humidStatus.textContent = '✓ Normal';
        humidStatus.style.color = '#10b981';
    }

    // Light
    const lightValue = data.light_lux !== undefined ? data.light_lux : data.light;
    document.getElementById('light-value').textContent = `${parseFloat(lightValue).toFixed(1)} Lux`;
    const lightStatus = document.getElementById('light-status');
    if (lightValue < LIGHT_MIN_LUX) {
        lightStatus.textContent = '💡 Dark';
        lightStatus.style.color = '#f59e0b';
    } else {
        lightStatus.textContent = '✓ Bright';
        lightStatus.style.color = '#10b981';
    }

    // Gas
    const gasValue = data.gas_ppm !== undefined ? data.gas_ppm : data.gas;
    document.getElementById('gas-value').textContent = `${parseFloat(gasValue).toFixed(1)} PPM`;
    const gasStatus = document.getElementById('gas-status');
    if (gasValue > GAS_THRESHOLD_PPM) {
        gasStatus.textContent = '⚠️ Warning!';
        gasStatus.style.color = '#ef4444';
        showAlert('danger', 'Gas Detected!', `Dangerous gas level: ${gasValue.toFixed(1)} PPM`);
    } else {
        gasStatus.textContent = '✓ Safe';
        gasStatus.style.color = '#10b981';
    }

    // Heat Index
    document.getElementById('heat-value').textContent = `${data.heat_index.toFixed(1)}°C`;

    // Comfort Index
    document.getElementById('comfort-value').textContent = `${data.comfort}/100`;
    const comfortStatus = document.getElementById('comfort-status');
    if (data.comfort >= 80) {
        comfortStatus.textContent = '😊 Excellent';
        comfortStatus.style.color = '#10b981';
    } else if (data.comfort >= 60) {
        comfortStatus.textContent = '🙂 Good';
        comfortStatus.style.color = '#3b82f6';
    } else {
        comfortStatus.textContent = '😟 Poor';
        comfortStatus.style.color = '#f59e0b';
    }

    // Fan Status
    document.getElementById('fan-status').textContent = `Fan: ${data.fan ? 'ON 🟢' : 'OFF 🔴'}`;
    document.getElementById('fan-status').style.color = data.fan ? '#10b981' : '#ef4444';

    // Alert Status
    const alertBadge = document.getElementById('alert-badge');
    if (data.alert) {
        alertBadge.textContent = 'ALERT';
        alertBadge.className = 'status-badge alert';
    } else {
        alertBadge.textContent = 'OK';
        alertBadge.className = 'status-badge connected';
    }

    // Update charts
    if (tempChart.data.labels.length > 0) {
        updateCharts(data);
    }
}

// Show Alert
function showAlert(type, title, message) {
    const alertContainer = document.getElementById('alerts-container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <strong>${title}</strong><br>
        ${message}
    `;
    alertContainer.appendChild(alert);

    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

// Socket Events
socket.on('connect', () => {
    console.log('✓ Connected to server');
    document.getElementById('connection-status').textContent = 'Connected';
    document.getElementById('connection-status').className = 'status-badge connected';
    showAlert('success', 'Connected', 'Connected to server!');
});

socket.on('disconnect', () => {
    console.log('✗ Disconnected');
    document.getElementById('connection-status').textContent = 'Disconnected';
    document.getElementById('connection-status').className = 'status-badge disconnected';
    showAlert('danger', 'Disconnected', 'Connection lost!');
});

socket.on('sensor_update', (data) => {
    console.log('📊 Sensor update:', data);
    updateUI(data);
});

socket.on('status_update', (data) => {
    console.log('📢 Status:', data);
    showAlert('info', 'Status Update', data.status);
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing dashboard...');
    initCharts();
    
    loadThingSpeakData();
    
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            console.log('📥 Initial data:', data);
            updateUI(data);
        })
        .catch(error => console.error('Error:', error));
    
    setInterval(loadThingSpeakData, 5 * 60 * 1000);
});