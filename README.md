# Youtube-transcript-summarizer

Tóm tắt transcript video YouTube tự động bằng AI. Hỗ trợ 2 chế độ:
- **Plain mode**: Tóm tắt nhanh, đơn giản
- **Lesson mode**: Bài học có cấu trúc (tiêu đề, mục tiêu, khái niệm chính, câu hỏi ôn tập)

## 🚀 Cài đặt

```bash
pip install youtube-transcript-api transformers torch
```

## 📖 Cách sử dụng

### 🎓 TẠO BÀI HỌC BẰNG GEMINI AI - NHANH & CHẤT LƯỢNG CAO! ⭐⭐⭐⭐⭐
```bash
# Cần Gemini API key (miễn phí): https://makersuite.google.com/app/apikey
set GEMINI_API_KEY=your_api_key_here

# Tạo bài học (10-30 giây, chất lượng xuất sắc!)
gemini_lesson.bat "youtube_url" en lesson.md
# hoặc
python gemini_lesson.py --url "youtube_url" --language vi --output my_lesson.md
```
**Xem hướng dẫn chi tiết:** [GEMINI_GUIDE.md](GEMINI_GUIDE.md)

### 🎓 Tạo bài học với mô hình local (chậm hơn, không cần API)
```bash
create_lesson.bat "youtube_url" en lesson.md
# hoặc
python create_lesson.py --url "youtube_url" --language vi --output my_lesson.md
```
**Bài học bao gồm:**
- 📚 Tiêu đề hấp dẫn
- 🎯 Mục tiêu học tập cụ thể (4-6 mục)
- 💡 Các khái niệm chính (chi tiết, có ví dụ)
- 📝 Các bước thực hiện / Quy trình
- 🔍 Ví dụ minh họa cụ thể
- 📌 Tóm tắt (4-6 điểm chính)
- ❓ Câu hỏi ôn tập (5-7 câu, nhiều cấp độ)

**→ Người học có thể bỏ qua xem video và học trực tiếp từ bài học!**

---

### 1. Tóm tắt nhanh - ngắn gọn (~200 từ)
```bash
run_fast.bat "youtube_url"
# Phù hợp: Xem nhanh nội dung chính
```

### 2. Tóm tắt chi tiết - giữ nhiều ý (~800-1200 từ)
```bash
run_detailed.bat "youtube_url"
# Phù hợp: Ghi chép học tập, ôn tập
```

### 3. Tóm tắt tùy chỉnh độ dài
```bash
run_custom.bat "youtube_url" 1000
# Tham số thứ 2: số từ mong muốn (500, 1000, 1500,...)
```

### 4. Chỉ lấy transcript (không tóm tắt)
```bash
python simple_transcript.py --url "youtube_url" --output transcript.txt
# Rất nhanh, lấy toàn bộ phụ đề
```

### 5. Tùy chỉnh với tham số
```bash
# Tóm tắt đơn giản
run.bat --url <youtube_url> --combine

# Bài học có cấu trúc (chậm hơn)
run.bat --url <youtube_url> --mode lesson --combine

# Chỉ lấy transcript (không tóm tắt)
python simple_transcript.py --url <youtube_url> --output transcript.txt
```

### 3. Các tùy chọn nâng cao
```bash
python quickstart.py --url <youtube_url> \
  --model sshleifer/distilbart-cnn-12-6 \
  --mode plain \
  --combine \
  --chunk-words 300 \
  --max-length 120 \
  --min-length 30 \
  --language en
```

## ⚙️ Các mô hình hỗ trợ

| Mô hình | Tốc độ | Chất lượng | Khuyến nghị |
|---------|--------|------------|-------------|
| `sshleifer/distilbart-cnn-12-6` | ⚡⚡⚡ Nhanh | ⭐⭐⭐ Tốt | ✅ Mặc định |
| `t5-small` | ⚡⚡⚡ Nhanh | ⭐⭐ Trung bình | CPU yếu |
| `facebook/bart-large-cnn` | ⚡ Chậm | ⭐⭐⭐⭐ Xuất sắc | GPU hoặc có thời gian |

## 📊 So sánh các chế độ

| Chế độ | Script | Độ dài output | Thời gian | Phù hợp cho |
|--------|--------|---------------|-----------|-------------|
| **Bài học hoàn chỉnh** | `create_lesson.bat` | ~2000-3000 từ | ⚡⚡⚡ Chậm (5-15 phút) | **Thay thế xem video** ⭐⭐⭐ |
| **Chi tiết** | `run_detailed.bat` | ~30-40% gốc (~800-1200 từ) | ⚡⚡ Trung bình | Học tập, ghi chép |
| **Nhanh** | `run_fast.bat` | ~10-15% gốc (~200 từ) | ⚡ Nhanh | Xem nhanh nội dung |
| **Tùy chỉnh** | `run_custom.bat url 1000` | Tùy chọn | ⚡⚡ Tùy thuộc | Linh hoạt theo nhu cầu |

## 📊 Tham số tối ưu

**Cho CPU (nhanh nhất - ngắn gọn):**
```bash
--model t5-small --chunk-words 250 --max-length 100 --mode plain
```

**Chi tiết hơn (giữ nhiều ý chính):**
```bash
--model sshleifer/distilbart-cnn-12-6 --chunk-words 500 --max-length 300 --min-length 100 --mode plain
# Không dùng --combine để giữ tất cả các tóm tắt
```

**Cân bằng (khuyến nghị):**
```bash
--model sshleifer/distilbart-cnn-12-6 --chunk-words 300 --max-length 120 --mode plain
```

**Chất lượng cao (cần GPU hoặc thời gian chờ):**
```bash
--model facebook/bart-large-cnn --chunk-words 400 --max-length 180 --mode lesson
```

## 🛠️ Cải tiến mới (v2.0)

✅ Mô hình mặc định nhỏ hơn 40% (distilbart thay vì bart-large)  
✅ Chunk size giảm 25% (300 từ thay vì 400)  
✅ Output length giảm 33% (120 tokens thay vì 180)  
✅ Thêm `num_beams=2` và `early_stopping=True` cho nhanh hơn 50%  
✅ Thêm thanh tiến trình để theo dõi  
✅ Tối ưu Plain mode làm mặc định (nhanh hơn Lesson mode)  
✅ File `run_fast.bat` với cấu hình tối ưu sẵn  

**Kết quả:** Nhanh hơn **3-5 lần** so với phiên bản cũ!

## 📝 Ví dụ

```bash
# ⭐ TẠO BÀI HỌC HOÀN CHỈNH - Học không cần xem video!
create_lesson.bat "https://www.youtube.com/watch?v=abc123" en lesson.md
# hoặc tiếng Việt
python create_lesson.py --url "url" --language vi --output bai_hoc.md

# Tóm tắt nhanh (~200 từ)
run_fast.bat "https://www.youtube.com/watch?v=8Jx6gN7ZFKk"

# Tóm tắt chi tiết (~1000 từ) - KHUYẾN NGHỊ cho học tập
run_detailed.bat "https://www.youtube.com/watch?v=8Jx6gN7ZFKk"

# Tóm tắt 1500 từ
run_custom.bat "https://www.youtube.com/watch?v=8Jx6gN7ZFKk" 1500

# Chỉ lấy transcript
python simple_transcript.py --url "url" --output transcript.txt
```

## 🎯 Khi nào dùng gì?

### 📚 Bài học hoàn chỉnh (`create_lesson.bat`) - Dùng khi:
- ✅ Bạn muốn học mà **KHÔNG XEM VIDEO**
- ✅ Cần tài liệu học tập đầy đủ, có cấu trúc
- ✅ Cần ghi chú để ôn tập sau
- ✅ Muốn hiểu sâu về nội dung
- ⏱️ Có thời gian chờ 5-15 phút

**Ví dụ:** Video tutorial lập trình, video giảng bài, khóa học online

### 📝 Tóm tắt chi tiết (`run_detailed.bat`) - Dùng khi:
- ✅ Cần tóm tắt chi tiết nhưng nhanh hơn
- ✅ Muốn nắm được các ý chính
- ⏱️ Có thời gian chờ 2-5 phút

### ⚡ Tóm tắt nhanh (`run_fast.bat`) - Dùng khi:
- ✅ Chỉ cần xem nhanh video nói về gì
- ✅ Quyết định có nên xem video không
- ⏱️ Muốn kết quả ngay lập tức

## 💡 Giải thích tham số quan trọng

### `--chunk-words` (Số từ mỗi chunk)
- **250**: Nhanh, tóm tắt ngắn gọn
- **500**: Cân bằng, giữ nhiều chi tiết hơn ⭐
- **700**: Chi tiết nhất, chậm hơn

### `--max-length` (Độ dài output mỗi chunk - tokens)
- **100**: Tóm tắt rất ngắn (~75 từ)
- **200**: Tóm tắt trung bình (~150 từ)
- **300**: Tóm tắt chi tiết (~225 từ) ⭐
- **400**: Tóm tắt rất chi tiết (~300 từ)

### `--combine` (Gộp tất cả thành 1 tóm tắt cuối)
- **Có `--combine`**: Tóm tắt rất ngắn gọn
- **Không có**: Giữ nhiều ý chính hơn ⭐

**Công thức ước tính:**
```
Số từ output ≈ (Số từ gốc / chunk_words) × (max_length × 0.75)
```

Ví dụ: 4000 từ gốc, chunk=500, max=300
→ Output ≈ (4000/500) × (300×0.75) = 8 × 225 = **~1800 từ**

## 🔧 Xử lý lỗi

**Lỗi: Python was not found**
- Giải pháp: Dùng `run.bat` hoặc vô hiệu hóa Python alias trong Settings

**Lỗi: Model chạy quá chậm**
- Giải pháp: Dùng `run_fast.bat` hoặc mô hình `t5-small`

**Lỗi: Out of memory**
- Giải pháp: Giảm `--chunk-words` xuống 200-250

---

## 📚 High-Level Approach

1. Get transcripts/subtitles for a given YouTube video Id using a Python API
2. Perform text summarization on obtained transcripts using HuggingFace transformers
3. Build a Flask backend REST API to expose the summarization service to the client
4. Develop a chrome extension which will utilize the backend API to display summarized text to the user

---

**Repository:** AI4Live  
**Author:** cuongnk2005
