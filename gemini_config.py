import google.generativeai as genai
from datetime import datetime

# ===== CẤU HÌNH GEMINI =====
GEMINI_API_KEY = "AIzaSyCrCLsotI6rKauU08ZHi7o9nIXJdtRkGgQ"  # Thay bằng API key của bạn
ANALYSIS_INTERVAL = 30 * 60  # 30 phút (tính bằng giây)

# Khởi tạo Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

def analyze_environment(data):
    """
    Phân tích môi trường bằng Gemini AI - Phiên bản thực tế
    
    Args:
        data: Dict chứa dữ liệu cảm biến
        
    Returns:
        Dict chứa phân tích từ Gemini
    """
    
    # Xác định tình trạng từng chỉ số
    temp_status = "BT" if 20 <= data['temp'] <= 30 else "XẤU"
    humid_status = "BT" if 40 <= data['humid'] <= 70 else "XẤU"
    light_status = "BT" if data['light_lux'] >= 200 else "TỐI"
    gas_status = "NGUY HIỂM" if data['gas_ppm'] > 300 else "AN TOÀN"
    
    # Tạo prompt thực tế hơn
    prompt = f"""
Bạn là chuyên gia tư vấn môi trường sống. Hãy phân tích THỰC TẾ và đưa ra LỜI KHUYÊN CỤ THỂ.

📊 DỮ LIỆU HIỆN TẠI:
🌡️ Nhiệt độ: {data['temp']:.1f}°C [{temp_status}]
💧 Độ ẩm: {data['humid']:.1f}% [{humid_status}]
💡 Ánh sáng: {data['light_lux']:.0f} Lux [{light_status}]
☁️ Khí gas: {data['gas_ppm']:.1f} PPM [{gas_status}]
🔥 Chỉ số nhiệt: {data['heat_index']:.1f}°C (cảm giác như)
😊 Thoải mái: {data['comfort']}/100
🌀 Quạt: {'ĐANG BẬT' if data['fan'] else 'ĐANG TẮT'}

📏 NGƯỠNG LÝ TƯỞNG:
- Nhiệt độ: 20-26°C (thoải mái nhất)
- Độ ẩm: 40-60% (lý tưởng cho sức khỏe)
- Ánh sáng: 300-500 Lux (đủ sáng làm việc)
- Khí gas: <100 PPM (an toàn tuyệt đối)

YÊU CẦU PHÂN TÍCH (NGẮN GỌN - TỐI ĐA 200 TỪ):

1. 📝 ĐÁNH GIÁ (1-2 câu):
   - Tình trạng tổng thể: Tốt/Trung bình/Kém/Nguy hiểm
   - Chỉ số nào đang có vấn đề

2. ⚠️ VẤN ĐỀ CHÍNH (nếu có):
   - Chỉ nói vấn đề THỰC SỰ CẦN LO NGẠI
   - Tác động đến sức khỏe cụ thể

3. 💡 LỜI KHUYÊN HÀNH ĐỘNG (CỤ THỂ):
   {f"- Về nhiệt độ {data['temp']:.1f}°C: Nên làm gì?" if temp_status == "XẤU" else ""}
   {f"- Về độ ẩm {data['humid']:.1f}%: Nên làm gì?" if humid_status == "XẤU" else ""}
   {f"- Về ánh sáng {data['light_lux']:.0f} Lux: Nên làm gì?" if light_status == "TỐI" else ""}
   {f"- Về khí gas {data['gas_ppm']:.1f} PPM: PHẢI LÀM GÌ NGAY?" if gas_status == "NGUY HIỂM" else ""}
   - Các hành động cụ thể: Bật quạt? Mở cửa? Tắt điều hòa? Bật đèn?

4. 🎯 ƯU TIÊN:
   - THẤP: Mọi thứ OK, không cần làm gì
   - TRUNG BÌNH: Nên điều chỉnh trong vài giờ tới
   - CAO: Cần xử lý trong 30 phút
   - KHẨN CẤP: Hành động NGAY LẬP TỨC!

LƯU Ý: 
- Chỉ nói những gì THỰC SỰ QUAN TRỌNG
- Lời khuyên phải CỤ THỂ, DỄ LÀM được ngay
- Không dài dòng, không lý thuyết
- Dùng emoji để dễ đọc
"""

    try:
        # Gọi Gemini API
        response = model.generate_content(prompt)
        analysis_text = response.text.strip()
        
        # Xác định mức độ ưu tiên từ phân tích
        priority = "THẤP"
        analysis_upper = analysis_text.upper()
        
        if "KHẨN CẤP" in analysis_upper or "NGUY HIỂM" in analysis_upper or data['gas_ppm'] > 300:
            priority = "KHẨN CẤP"
        elif "CAO" in analysis_upper or data['temp'] > 35 or data['temp'] < 15:
            priority = "CAO"
        elif "TRUNG BÌNH" in analysis_upper or abs(data['temp'] - 25) > 5 or abs(data['humid'] - 55) > 15:
            priority = "TRUNG BÌNH"
        
        return {
            'success': True,
            'analysis': analysis_text,
            'priority': priority,
            'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'data_snapshot': {
                'temp': f"{data['temp']:.1f}°C",
                'humid': f"{data['humid']:.1f}%",
                'light': f"{data['light_lux']:.0f} Lux",
                'gas': f"{data['gas_ppm']:.1f} PPM",
                'comfort': f"{data['comfort']}/100"
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }

def get_short_summary(analysis_result):
    """
    Tạo tóm tắt ngắn gọn từ phân tích cho thông báo nhanh
    
    Args:
        analysis_result: Kết quả từ analyze_environment
        
    Returns:
        String tóm tắt ngắn gọn
    """
    if not analysis_result['success']:
        return "❌ Lỗi phân tích AI"
    
    # Lấy câu đầu tiên làm tóm tắt
    lines = [line.strip() for line in analysis_result['analysis'].split('\n') if line.strip()]
    
    # Tìm dòng đánh giá
    for line in lines:
        if any(keyword in line.lower() for keyword in ['đánh giá', 'tình trạng', 'môi trường']):
            summary = line.replace('📝', '').replace('ĐÁNH GIÁ', '').replace(':', '').strip()
            if len(summary) > 100:
                summary = summary[:100] + "..."
            return f"🤖 {summary}"
    
    # Nếu không tìm thấy, lấy dòng đầu
    if lines:
        summary = lines[0].replace('#', '').strip()
        if len(summary) > 100:
            summary = summary[:100] + "..."
        return f"🤖 {summary}"
    
    return "🤖 Đã phân tích xong môi trường"

def format_for_telegram(analysis_result):
    """
    Format phân tích để gửi qua Telegram với HTML đẹp
    
    Args:
        analysis_result: Kết quả từ analyze_environment
        
    Returns:
        String formatted cho Telegram
    """
    if not analysis_result['success']:
        return f"❌ <b>LỖI PHÂN TÍCH AI</b>\n\n{analysis_result['error']}"
    
    priority_emoji = {
        'KHẨN CẤP': '🚨',
        'CAO': '⚠️',
        'TRUNG BÌNH': '📊',
        'THẤP': '✅'
    }
    
    emoji = priority_emoji.get(analysis_result['priority'], '📊')
    
    # Format analysis với HTML
    analysis = analysis_result['analysis']
    
    # Highlight các section
    analysis = analysis.replace('📝 ĐÁNH GIÁ', '\n<b>📝 ĐÁNH GIÁ</b>')
    analysis = analysis.replace('⚠️ VẤN ĐỀ CHÍNH', '\n<b>⚠️ VẤN ĐỀ CHÍNH</b>')
    analysis = analysis.replace('💡 LỜI KHUYÊN', '\n<b>💡 LỜI KHUYÊN HÀNH ĐỘNG</b>')
    analysis = analysis.replace('🎯 ƯU TIÊN', '\n<b>🎯 ƯU TIÊN</b>')
    
    message = f"""
{emoji} <b>PHÂN TÍCH AI - MÔI TRƯỜNG</b>
{'━' * 30}

{analysis}

{'━' * 30}
📊 <b>DỮ LIỆU:</b>
🌡️ {analysis_result['data_snapshot']['temp']} | 💧 {analysis_result['data_snapshot']['humid']}
💡 {analysis_result['data_snapshot']['light']} | ☁️ {analysis_result['data_snapshot']['gas']}
😊 Thoải mái: {analysis_result['data_snapshot']['comfort']}

⏰ <i>{analysis_result['timestamp']}</i>
"""
    
    return message.strip()