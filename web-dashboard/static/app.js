// Kết nối Socket.IO
const socket = io();

// Biểu đồ
let tempChart, humidChart;
const maxDataPoints = 20;

// Ngưỡng
const TEMP_MAX = 35.0;
const TEMP_MIN = 15.0;
const TEMP_FAN_ON = 30.0;
const HUMID_MAX = 80.0;
const HUMID_MIN = 30.0;
const LIGHT_MIN_LUX = 200.0;
const GAS_THRESHOLD_PPM = 300.0;

// Khởi tạo Biểu đồ
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
                label: 'Nhiệt độ (°C)',
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
                label: 'Độ ẩm (%)',
                data: [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4
            }]
        }
    });
}

// Tải dữ liệu lịch sử ThingSpeak
async function loadThingSpeakData() {
    try {
        console.log('📥 Dang tai du lieu ThingSpeak...');
        const response = await fetch('/api/thingspeak');
        const data = await response.json();
        
        if (data.feeds && data.feeds.length > 0) {
            console.log(`✓ Da tai ${data.feeds.length} ban ghi`);
            
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
            
            showAlert('success', 'Đã tải dữ liệu', `Đã tải ${data.feeds.length} bản ghi từ ThingSpeak`);
        } else {
            console.warn('⚠️ Khong co du lieu trong ThingSpeak');
        }
    } catch (error) {
        console.error('✗ Loi tai ThingSpeak:', error);
    }
}

// Cập nhật Biểu đồ với dữ liệu thời gian thực
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

// Cập nhật giao diện
function updateUI(data) {
    console.log('🔄 Dang cap nhat giao dien:', data);
    
    document.getElementById('timestamp').textContent = data.timestamp || new Date().toLocaleTimeString();

    // Nhiệt độ
    document.getElementById('temp-value').textContent = `${data.temp.toFixed(1)}°C`;
    const tempStatus = document.getElementById('temp-status');
    if (data.temp > TEMP_MAX) {
        tempStatus.textContent = '⚠️ Quá nóng';
        tempStatus.style.color = '#ef4444';
    } else if (data.temp < TEMP_MIN) {
        tempStatus.textContent = '❄️ Quá lạnh';
        tempStatus.style.color = '#3b82f6';
    } else {
        tempStatus.textContent = '✓ Bình thường';
        tempStatus.style.color = '#10b981';
    }

    // Độ ẩm
    document.getElementById('humid-value').textContent = `${data.humid.toFixed(1)}%`;
    const humidStatus = document.getElementById('humid-status');
    if (data.humid > HUMID_MAX) {
        humidStatus.textContent = '⚠️ Quá ẩm';
        humidStatus.style.color = '#ef4444';
    } else if (data.humid < HUMID_MIN) {
        humidStatus.textContent = '⚠️ Quá khô';
        humidStatus.style.color = '#f59e0b';
    } else {
        humidStatus.textContent = '✓ Bình thường';
        humidStatus.style.color = '#10b981';
    }

    // Ánh sáng
    const lightValue = data.light_lux !== undefined ? data.light_lux : data.light;
    document.getElementById('light-value').textContent = `${parseFloat(lightValue).toFixed(1)} Lux`;
    const lightStatus = document.getElementById('light-status');
    if (lightValue < LIGHT_MIN_LUX) {
        lightStatus.textContent = '💡 Tối';
        lightStatus.style.color = '#f59e0b';
    } else {
        lightStatus.textContent = '✓ Sáng';
        lightStatus.style.color = '#10b981';
    }

    // Khí gas
    const gasValue = data.gas_ppm !== undefined ? data.gas_ppm : data.gas;
    document.getElementById('gas-value').textContent = `${parseFloat(gasValue).toFixed(1)} PPM`;
    const gasStatus = document.getElementById('gas-status');
    if (gasValue > GAS_THRESHOLD_PPM) {
        gasStatus.textContent = '⚠️ Cảnh báo!';
        gasStatus.style.color = '#ef4444';
        showAlert('danger', 'Phát hiện khí gas!', `Mức độ nguy hiểm: ${gasValue.toFixed(1)} PPM`);
    } else {
        gasStatus.textContent = '✓ An toàn';
        gasStatus.style.color = '#10b981';
    }

    // Chỉ số nhiệt
    document.getElementById('heat-value').textContent = `${data.heat_index.toFixed(1)}°C`;

    // Chỉ số thoải mái
    document.getElementById('comfort-value').textContent = `${data.comfort}/100`;
    const comfortStatus = document.getElementById('comfort-status');
    if (data.comfort >= 80) {
        comfortStatus.textContent = '😊 Tuyệt vời';
        comfortStatus.style.color = '#10b981';
    } else if (data.comfort >= 60) {
        comfortStatus.textContent = '🙂 Tốt';
        comfortStatus.style.color = '#3b82f6';
    } else {
        comfortStatus.textContent = '😟 Kém';
        comfortStatus.style.color = '#f59e0b';
    }

    // Trạng thái quạt
    document.getElementById('fan-status').textContent = `Quạt: ${data.fan ? 'BẬT 🟢' : 'TẮT 🔴'}`;
    document.getElementById('fan-status').style.color = data.fan ? '#10b981' : '#ef4444';

    // Trạng thái cảnh báo
    const alertBadge = document.getElementById('alert-badge');
    if (data.alert) {
        alertBadge.textContent = 'CẢNH BÁO';
        alertBadge.className = 'status-badge alert';
    } else {
        alertBadge.textContent = 'OK';
        alertBadge.className = 'status-badge connected';
    }

    // Cập nhật biểu đồ
    if (tempChart.data.labels.length > 0) {
        updateCharts(data);
    }
}

// Hiển thị thông báo
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

// ===== XỬ LÝ AI =====
function displayAIAnalysis(data) {
    const aiContent = document.getElementById('ai-content');
    const aiTimestamp = document.getElementById('ai-timestamp');
    
    // Xác định class priority
    let priorityClass = 'low';
    let priorityText = 'THẤP';
    const priority = data.priority.toUpperCase();
    
    if (priority.includes('KHẨN CẤP')) {
        priorityClass = 'critical';
        priorityText = '🚨 KHẨN CẤP';
    } else if (priority.includes('CAO')) {
        priorityClass = 'high';
        priorityText = '⚠️ CAO';
    } else if (priority.includes('TRUNG BÌNH')) {
        priorityClass = 'medium';
        priorityText = '📊 TRUNG BÌNH';
    } else {
        priorityText = '✅ THẤP';
    }
    
    // Parse analysis thành các section
    let analysis = data.analysis;
    
    // Highlight các phần quan trọng
    analysis = analysis.replace(/📝 ĐÁNH GIÁ/g, '<h3>📝 ĐÁNH GIÁ</h3>');
    analysis = analysis.replace(/⚠️ VẤN ĐỀ CHÍNH/g, '<h3 class="warning">⚠️ VẤN ĐỀ CHÍNH</h3>');
    analysis = analysis.replace(/💡 LỜI KHUYÊN/g, '<h3 class="advice">💡 LỜI KHUYÊN HÀNH ĐỘNG</h3>');
    analysis = analysis.replace(/🎯 ƯU TIÊN/g, '<h3>🎯 MỨC ĐỘ ƯU TIÊN</h3>');
    
    // Thay bullet points
    analysis = analysis.replace(/^- (.+)$/gm, '<li>$1</li>');
    analysis = analysis.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Thay line breaks
    analysis = analysis.replace(/\n\n/g, '</p><p>');
    analysis = analysis.replace(/\n/g, '<br>');
    
    // Highlight các số liệu
    analysis = analysis.replace(/(\d+\.?\d*)(°C|%|Lux|PPM)/g, '<strong class="metric">$1$2</strong>');
    
    aiContent.innerHTML = `
        <div class="ai-analysis">
            <div class="ai-priority ${priorityClass}">
                ${priorityText}
            </div>
            <div class="analysis-content">
                <p>${analysis}</p>
            </div>
            ${data.data_snapshot ? `
            <div class="data-snapshot">
                <h4>📊 Dữ liệu phân tích:</h4>
                <div class="snapshot-grid">
                    <span>🌡️ ${data.data_snapshot.temp}</span>
                    <span>💧 ${data.data_snapshot.humid}</span>
                    <span>💡 ${data.data_snapshot.light}</span>
                    <span>☁️ ${data.data_snapshot.gas}</span>
                    <span>😊 ${data.data_snapshot.comfort}</span>
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    aiTimestamp.textContent = `⏰ Cập nhật: ${data.timestamp}`;
    
    // Hiển thị alert dựa trên mức độ ưu tiên
    if (priorityClass === 'critical') {
        showAlert('danger', '🚨 AI: KHẨN CẤP!', data.summary || 'Cần hành động ngay lập tức!');
    } else if (priorityClass === 'high') {
        showAlert('warning', '⚠️ AI: Cảnh báo', data.summary || 'Cần chú ý môi trường');
    } else {
        showAlert('info', '🤖 Phân tích AI', data.summary || 'Đã hoàn thành phân tích');
    }
}

async function requestAIAnalysis() {
    const aiContent = document.getElementById('ai-content');
    const btnAiNow = document.getElementById('btn-ai-now');
    
    // Disable button và hiển thị loading
    btnAiNow.disabled = true;
    btnAiNow.textContent = 'Đang phân tích...';
    
    aiContent.innerHTML = `
        <div class="ai-loading">
            <div class="spinner"></div>
        </div>
    `;
    
    try {
        const response = await fetch('/api/ai/now', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayAIAnalysis(data);
        } else {
            aiContent.innerHTML = `
                <div class="ai-placeholder">
                    <span class="ai-icon">❌</span>
                    <p>Lỗi: ${data.error}</p>
                </div>
            `;
        }
    } catch (error) {
        aiContent.innerHTML = `
            <div class="ai-placeholder">
                <span class="ai-icon">❌</span>
                <p>Không thể kết nối đến AI: ${error.message}</p>
            </div>
        `;
    } finally {
        btnAiNow.disabled = false;
        btnAiNow.textContent = 'Phân tích ngay';
    }
}

async function loadAISettings() {
    try {
        const response = await fetch('/api/ai/config');
        const data = await response.json();
        
        document.getElementById('ai-enabled').checked = data.enabled;
        document.getElementById('ai-interval').value = data.interval_minutes;
    } catch (error) {
        console.error('Lỗi tải cài đặt AI:', error);
    }
}

async function saveAISettings() {
    const enabled = document.getElementById('ai-enabled').checked;
    const interval = parseInt(document.getElementById('ai-interval').value);
    
    if (interval < 10 || interval > 120) {
        showAlert('danger', 'Lỗi', 'Chu kỳ phải từ 10-120 phút');
        return;
    }
    
    try {
        const response = await fetch('/api/ai/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                enabled: enabled,
                interval: interval
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('success', 'Đã lưu', `Chu kỳ AI: ${data.interval_minutes} phút`);
            document.getElementById('ai-settings-modal').style.display = 'none';
        }
    } catch (error) {
        showAlert('danger', 'Lỗi', 'Không thể lưu cài đặt');
    }
}

// Sự kiện Socket
socket.on('connect', () => {
    console.log('✓ Da ket noi may chu');
    document.getElementById('connection-status').textContent = 'Đã kết nối';
    document.getElementById('connection-status').className = 'status-badge connected';
    showAlert('success', 'Đã kết nối', 'Đã kết nối máy chủ!');
});

socket.on('disconnect', () => {
    console.log('✗ Mat ket noi');
    document.getElementById('connection-status').textContent = 'Mất kết nối';
    document.getElementById('connection-status').className = 'status-badge disconnected';
    showAlert('danger', 'Mất kết nối', 'Đã mất kết nối!');
});

socket.on('sensor_update', (data) => {
    console.log('📊 Cap nhat cam bien:', data);
    updateUI(data);
});

socket.on('status_update', (data) => {
    console.log('📢 Trang thai:', data);
    showAlert('info', 'Cập nhật trạng thái', data.status);
});

socket.on('ai_analysis', (data) => {
    console.log('🤖 Phan tich AI:', data);
    displayAIAnalysis(data);
});

socket.on('ai_error', (data) => {
    console.error('❌ Loi AI:', data);
    showAlert('danger', 'Lỗi AI', data.error);
});

// Khởi tạo
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dang khoi tao bang dieu khien...');
    initCharts();
    
    loadThingSpeakData();
    
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            console.log('📥 Du lieu ban dau:', data);
            updateUI(data);
        })
        .catch(error => console.error('Loi:', error));
    
    // Tải phân tích AI mới nhất
    fetch('/api/ai/latest')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayAIAnalysis(data);
            }
        })
        .catch(error => console.error('Loi:', error));
    
    // Tải lại dữ liệu ThingSpeak mỗi 5 phút
    setInterval(loadThingSpeakData, 5 * 60 * 1000);
    
    // ===== EVENT LISTENERS =====
    // Nút phân tích AI
    document.getElementById('btn-ai-now').addEventListener('click', requestAIAnalysis);
    
    // Nút cài đặt AI
    const modal = document.getElementById('ai-settings-modal');
    const btnSettings = document.getElementById('btn-ai-settings');
    const closeModal = document.querySelector('.close');
    
    btnSettings.addEventListener('click', () => {
        loadAISettings();
        modal.style.display = 'block';
    });
    
    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Nút lưu cài đặt AI
    document.getElementById('btn-save-ai-settings').addEventListener('click', saveAISettings);
});