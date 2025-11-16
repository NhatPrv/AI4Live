# HƯỚNG DẪN SỬ DỤNG GEMINI AI TẠO BÀI HỌC

## 🚀 Ưu điểm so với mô hình local:

| Tiêu chí | Gemini AI | Mô hình Local (HuggingFace) |
|----------|-----------|------------------------------|
| **Tốc độ** | ⚡ 10-30 giây | 🐌 5-15 phút |
| **Chất lượng** | ⭐⭐⭐⭐⭐ Xuất sắc | ⭐⭐ Trung bình |
| **Chi phí** | 🆓 Miễn phí | 🆓 Miễn phí (nhưng cần GPU mạnh) |
| **Cài đặt** | ✅ Đơn giản | ❌ Phức tạp |
| **Tiếng Việt** | ✅ Rất tốt | ⚠️ Yếu |
| **Yêu cầu** | Internet + API key | CPU/GPU mạnh + RAM lớn |

---

## 📝 BƯỚC 1: Lấy Gemini API Key (MIỄN PHÍ)

1. Truy cập: https://makersuite.google.com/app/apikey
2. Đăng nhập bằng Google account
3. Click "Create API Key"
4. Copy API key (dạng: AIzaSy...)

**Lưu ý:** API key MIỄN PHÍ với quota:
- 15 requests/phút
- 1500 requests/ngày
- Đủ cho hầu hết nhu cầu cá nhân!

---

## 📝 BƯỚC 2: Cài đặt thư viện

```bash
pip install google-generativeai
```

Hoặc nếu chưa có các thư viện khác:
```bash
pip install youtube-transcript-api google-generativeai
```

---

## 📝 BƯỚC 3: Set API Key

### Cách 1: Set biến môi trường (Khuyến nghị)

**Windows CMD:**
```bash
set GEMINI_API_KEY=AIzaSy_your_key_here
```

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY="AIzaSy_your_key_here"
```

**Linux/Mac:**
```bash
export GEMINI_API_KEY=AIzaSy_your_key_here
```

### Cách 2: Truyền qua tham số
```bash
python gemini_lesson.py --url "..." --api-key "AIzaSy_your_key_here"
```

---

## 🎯 CÁCH SỬ DỤNG

### Cách 1: Dùng file batch (Đơn giản nhất)

```bash
# Hiển thị trên terminal (tiếng Anh)
gemini_lesson.bat "https://www.youtube.com/watch?v=VIDEO_ID"

# Hiển thị trên terminal (tiếng Việt)
gemini_lesson.bat "https://www.youtube.com/watch?v=VIDEO_ID" vi

# Lưu vào file (tiếng Anh)
gemini_lesson.bat "https://www.youtube.com/watch?v=VIDEO_ID" en lesson.md

# Lưu vào file (tiếng Việt)
gemini_lesson.bat "https://www.youtube.com/watch?v=VIDEO_ID" vi bai_hoc.md
```

### Cách 2: Dùng Python trực tiếp

```bash
# Hiển thị trên terminal
python gemini_lesson.py --url "https://youtube.com/watch?v=VIDEO_ID" --language vi

# Lưu vào file
python gemini_lesson.py --url "URL" --language en --output lesson.md

# Tùy chỉnh số lượng key points
python gemini_lesson.py --url "URL" --max-points 100 --output lesson.md
```

---

## 📋 VÍ DỤ CỤ THỂ

```bash
# Video học Python - tiếng Anh
gemini_lesson.bat "https://www.youtube.com/watch?v=kqtD5dpn9C8" en python_lesson.md

# Video học JavaScript - tiếng Việt
gemini_lesson.bat "https://www.youtube.com/watch?v=abc123" vi js_lesson.md

# Video TED Talk - chỉ xem trên terminal
gemini_lesson.bat "https://www.youtube.com/watch?v=xyz789"
```

---

## 🎓 CẤU TRÚC BÀI HỌC TỰ ĐỘNG

Bài học được tạo tự động gồm:

1. 📚 **Tiêu đề bài học** - Hấp dẫn, súc tích
2. 🎯 **Mục tiêu học tập** - 4-6 mục tiêu cụ thể
3. 💡 **Các khái niệm chính** - Định nghĩa, giải thích chi tiết
4. 📝 **Nội dung chi tiết** - Phân chia thành các phần logic
5. 🔍 **Ví dụ minh họa** - Code, case studies cụ thể
6. 📋 **Các bước thực hiện** - Hướng dẫn từng bước (nếu có)
7. 💡 **Tips & Lưu ý** - Best practices, điều cần tránh
8. 📌 **Tóm tắt** - 5-7 điểm chính
9. ❓ **Câu hỏi ôn tập** - 5-7 câu kiểm tra kiến thức

---

## 🔧 XỬ LÝ LỖI THƯỜNG GẶP

### Lỗi: "Thiếu Gemini API key"
**Giải pháp:** Set biến môi trường `GEMINI_API_KEY`

### Lỗi: "API key không hợp lệ"
**Giải pháp:** Kiểm tra lại API key, tạo key mới nếu cần

### Lỗi: "Rate limit exceeded"
**Giải pháp:** Đợi 1 phút, quota sẽ reset (15 requests/phút)

### Lỗi: "Không thể lấy transcript"
**Giải pháp:** 
- Video không có phụ đề
- Hoặc phụ đề bị tắt bởi chủ video
- Thử video khác

---

## 💡 TIPS & TRICKS

1. **Tăng độ chi tiết:**
   ```bash
   python gemini_lesson.py --url "..." --max-points 100
   ```

2. **Tiết kiệm API calls:**
   - Lưu kết quả vào file để đọc lại
   - Không chạy lại cùng video nhiều lần

3. **Chất lượng tốt nhất:**
   - Chọn video có phụ đề chất lượng
   - Video dạy học, tutorial tốt hơn video chat/vlog

4. **Xử lý video dài:**
   - Script tự động trích xuất key points
   - Gemini xử lý được context dài

---

## 📊 SO SÁNH VỚI SCRIPT CŨ

| Tính năng | gemini_lesson.py | create_lesson.py (HuggingFace) |
|-----------|------------------|--------------------------------|
| Thời gian | 10-30 giây | 5-15 phút |
| Chất lượng | Xuất sắc | Trung bình |
| Tiếng Việt | Rất tốt | Yếu |
| Yêu cầu | API key + Internet | Không cần, nhưng chậm |
| Chi phí | Miễn phí | Miễn phí |
| Cài đặt | Đơn giản | Phức tạp (model lớn) |

---

## 🎉 KẾT LUẬN

**KHUYẾN NGHỊ SỬ DỤNG `gemini_lesson.py` cho:**
- ✅ Chất lượng bài học cao
- ✅ Tốc độ nhanh
- ✅ Hỗ trợ tiếng Việt tốt
- ✅ Không cần GPU/máy mạnh

**Chỉ dùng `create_lesson.py` (HuggingFace) khi:**
- ❌ Không có Internet
- ❌ Không muốn dùng API bên thứ 3

---

**Lấy API key ngay:** https://makersuite.google.com/app/apikey
