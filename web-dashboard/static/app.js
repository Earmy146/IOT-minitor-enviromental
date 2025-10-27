// Kết nối Socket.IO
const ket_noi = io();

// Biểu đồ
let bieuDoNhiet, bieuDoAm;
const soLieuToiDa = 20;

// Ngưỡng
const NHIET_TOI_DA = 35.0;
const NHIET_TOI_THIEU = 15.0;
const NHIET_BAT_QUAT = 30.0;
const AM_TOI_DA = 80.0;
const AM_TOI_THIEU = 30.0;
const SANG_TOI_THIEU_LUX = 200.0;
const NGUONG_KHI_PPM = 300.0;

// Khởi tạo Biểu đồ
function khoiTaoBieuDo() {
    const cauHinhBieuDo = {
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

    const ngUCanh_nhiet = document.getElementById('tempChart').getContext('2d');
    bieuDoNhiet = new Chart(ngUCanh_nhiet, {
        ...cauHinhBieuDo,
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

    const ngUCanh_am = document.getElementById('humidChart').getContext('2d');
    bieuDoAm = new Chart(ngUCanh_am, {
        ...cauHinhBieuDo,
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
async function taiDuLieuThingSpeak() {
    try {
        console.log('📥 Dang tai du lieu ThingSpeak...');
        const phanHoi = await fetch('/api/thingspeak');
        const duLieu = await phanHoi.json();
        
        if (duLieu.feeds && duLieu.feeds.length > 0) {
            console.log(`✓ Da tai ${duLieu.feeds.length} ban ghi`);
            
            bieuDoNhiet.data.labels = [];
            bieuDoNhiet.data.datasets[0].data = [];
            bieuDoAm.data.labels = [];
            bieuDoAm.data.datasets[0].data = [];
            
            duLieu.feeds.slice().reverse().forEach(banGhi => {
                const thoiGian = new Date(banGhi.created_at).toLocaleTimeString();
                
                if (banGhi.field1) {
                    bieuDoNhiet.data.labels.push(thoiGian);
                    bieuDoNhiet.data.datasets[0].data.push(parseFloat(banGhi.field1));
                }
                
                if (banGhi.field2) {
                    bieuDoAm.data.labels.push(thoiGian);
                    bieuDoAm.data.datasets[0].data.push(parseFloat(banGhi.field2));
                }
            });
            
            bieuDoNhiet.update();
            bieuDoAm.update();
            
            hienThiThongBao('success', 'Đã tải dữ liệu', `Đã tải ${duLieu.feeds.length} bản ghi từ ThingSpeak`);
        } else {
            console.warn('⚠️ Khong co du lieu trong ThingSpeak');
            hienThiThongBao('warning', 'Không có dữ liệu', 'Không có dữ liệu lịch sử');
        }
    } catch (loi) {
        console.error('✗ Loi tai ThingSpeak:', loi);
        hienThiThongBao('danger', 'Lỗi', 'Không thể tải dữ liệu: ' + loi.message);
    }
}

// Cập nhật Biểu đồ với dữ liệu thời gian thực
function capNhatBieuDo(duLieu) {
    const thoiGian = new Date().toLocaleTimeString();

    if (bieuDoNhiet.data.labels.length >= soLieuToiDa) {
        bieuDoNhiet.data.labels.shift();
        bieuDoNhiet.data.datasets[0].data.shift();
    }
    bieuDoNhiet.data.labels.push(thoiGian);
    bieuDoNhiet.data.datasets[0].data.push(duLieu.nhiet_do);
    bieuDoNhiet.update('none');

    if (bieuDoAm.data.labels.length >= soLieuToiDa) {
        bieuDoAm.data.labels.shift();
        bieuDoAm.data.datasets[0].data.shift();
    }
    bieuDoAm.data.labels.push(thoiGian);
    bieuDoAm.data.datasets[0].data.push(duLieu.do_am);
    bieuDoAm.update('none');
}

// Cập nhật giao diện
function capNhatGiaoDien(duLieu) {
    console.log('🔄 Dang cap nhat giao dien:', duLieu);
    
    document.getElementById('timestamp').textContent = duLieu.thoi_gian || new Date().toLocaleTimeString();

    // Nhiệt độ
    document.getElementById('temp-value').textContent = `${duLieu.nhiet_do.toFixed(1)}°C`;
    const trangThaiNhiet = document.getElementById('temp-status');
    if (duLieu.nhiet_do > NHIET_TOI_DA) {
        trangThaiNhiet.textContent = '⚠️ Quá nóng';
        trangThaiNhiet.style.color = '#ef4444';
    } else if (duLieu.nhiet_do < NHIET_TOI_THIEU) {
        trangThaiNhiet.textContent = '❄️ Quá lạnh';
        trangThaiNhiet.style.color = '#3b82f6';
    } else {
        trangThaiNhiet.textContent = '✓ Bình thường';
        trangThaiNhiet.style.color = '#10b981';
    }

    // Độ ẩm
    document.getElementById('humid-value').textContent = `${duLieu.do_am.toFixed(1)}%`;
    const trangThaiAm = document.getElementById('humid-status');
    if (duLieu.do_am > AM_TOI_DA) {
        trangThaiAm.textContent = '⚠️ Quá ẩm';
        trangThaiAm.style.color = '#ef4444';
    } else if (duLieu.do_am < AM_TOI_THIEU) {
        trangThaiAm.textContent = '⚠️ Quá khô';
        trangThaiAm.style.color = '#f59e0b';
    } else {
        trangThaiAm.textContent = '✓ Bình thường';
        trangThaiAm.style.color = '#10b981';
    }

    // Ánh sáng
    const giaTriSang = duLieu.anh_sang_lux !== undefined ? duLieu.anh_sang_lux : duLieu.anh_sang;
    document.getElementById('light-value').textContent = `${parseFloat(giaTriSang).toFixed(1)} Lux`;
    const trangThaiSang = document.getElementById('light-status');
    if (giaTriSang < SANG_TOI_THIEU_LUX) {
        trangThaiSang.textContent = '💡 Tối';
        trangThaiSang.style.color = '#f59e0b';
    } else {
        trangThaiSang.textContent = '✓ Sáng';
        trangThaiSang.style.color = '#10b981';
    }

    // Khí gas
    const giaTriKhi = duLieu.khi_ppm !== undefined ? duLieu.khi_ppm : duLieu.khi;
    document.getElementById('gas-value').textContent = `${parseFloat(giaTriKhi).toFixed(1)} PPM`;
    const trangThaiKhi = document.getElementById('gas-status');
    if (giaTriKhi > NGUONG_KHI_PPM) {
        trangThaiKhi.textContent = '⚠️ Cảnh báo!';
        trangThaiKhi.style.color = '#ef4444';
        hienThiThongBao('danger', 'Phát hiện khí gas!', `Mức độ nguy hiểm: ${giaTriKhi.toFixed(1)} PPM`);
    } else {
        trangThaiKhi.textContent = '✓ An toàn';
        trangThaiKhi.style.color = '#10b981';
    }

    // Chỉ số nhiệt
    document.getElementById('heat-value').textContent = `${duLieu.chi_so_nhiet.toFixed(1)}°C`;

    // Chỉ số thoải mái
    document.getElementById('comfort-value').textContent = `${duLieu.thoai_mai}/100`;
    const trangThaiThoaiMai = document.getElementById('comfort-status');
    if (duLieu.thoai_mai >= 80) {
        trangThaiThoaiMai.textContent = '😊 Tuyệt vời';
        trangThaiThoaiMai.style.color = '#10b981';
    } else if (duLieu.thoai_mai >= 60) {
        trangThaiThoaiMai.textContent = '🙂 Tốt';
        trangThaiThoaiMai.style.color = '#3b82f6';
    } else {
        trangThaiThoaiMai.textContent = '😟 Kém';
        trangThaiThoaiMai.style.color = '#f59e0b';
    }

    // Trạng thái quạt
    document.getElementById('fan-status').textContent = `Quạt: ${duLieu.quat ? 'BẬT 🟢' : 'TẮT 🔴'}`;
    document.getElementById('fan-status').style.color = duLieu.quat ? '#10b981' : '#ef4444';

    // Trạng thái cảnh báo
    const huyHieuCanhBao = document.getElementById('alert-badge');
    if (duLieu.canh_bao) {
        huyHieuCanhBao.textContent = 'CẢNH BÁO';
        huyHieuCanhBao.className = 'status-badge alert';
    } else {
        huyHieuCanhBao.textContent = 'OK';
        huyHieuCanhBao.className = 'status-badge connected';
    }

    // Cập nhật biểu đồ
    if (bieuDoNhiet.data.labels.length > 0) {
        capNhatBieuDo(duLieu);
    }
}

// Hiển thị thông báo
function hienThiThongBao(loai, tieuDe, noiDung) {
    const hopThongBao = document.getElementById('alerts-container');
    const thongBao = document.createElement('div');
    thongBao.className = `alert alert-${loai}`;
    thongBao.innerHTML = `
        <strong>${tieuDe}</strong><br>
        ${noiDung}
    `;
    hopThongBao.appendChild(thongBao);

    setTimeout(() => {
        thongBao.style.opacity = '0';
        setTimeout(() => thongBao.remove(), 300);
    }, 5000);
}

// Sự kiện Socket
ket_noi.on('connect', () => {
    console.log('✓ Da ket noi may chu');
    document.getElementById('connection-status').textContent = 'Đã kết nối';
    document.getElementById('connection-status').className = 'status-badge connected';
    hienThiThongBao('success', 'Đã kết nối', 'Đã kết nối máy chủ!');
});

ket_noi.on('disconnect', () => {
    console.log('✗ Mat ket noi');
    document.getElementById('connection-status').textContent = 'Mất kết nối';
    document.getElementById('connection-status').className = 'status-badge disconnected';
    hienThiThongBao('danger', 'Mất kết nối', 'Đã mất kết nối!');
});

ket_noi.on('sensor_update', (duLieu) => {
    console.log('📊 Cap nhat cam bien:', duLieu);
    capNhatGiaoDien(duLieu);
});

ket_noi.on('status_update', (duLieu) => {
    console.log('📢 Trang thai:', duLieu);
    hienThiThongBao('info', 'Cập nhật trạng thái', duLieu.trang_thai);
});

// Khởi tạo
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dang khoi tao bang dieu khien...');
    khoiTaoBieuDo();
    
    taiDuLieuThingSpeak();
    
    fetch('/api/data')
        .then(phanHoi => phanHoi.json())
        .then(duLieu => {
            console.log('📥 Du lieu ban dau:', duLieu);
            capNhatGiaoDien(duLieu);
        })
        .catch(loi => console.error('Loi:', loi));
    
    // Tải lại dữ liệu ThingSpeak mỗi 5 phút
    setInterval(taiDuLieuThingSpeak, 5 * 60 * 1000);
});