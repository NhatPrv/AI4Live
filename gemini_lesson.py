#!/usr/bin/env python3
"""
Tạo bài học hoàn chỉnh từ YouTube bằng Gemini API
- Lấy transcript từ YouTube
- Trích xuất key points chi tiết
- Generate bài học bằng Gemini AI
"""

import os
import sys

"""
Optional Windows networking patching
- Historically added to work around WinError 10106 under some hosts.
- This can interfere with certain domains (e.g., Google APIs) if IPs change.
- Respect env DISABLE_SOCKET_PATCH=1 to skip all monkey-patching.
"""
if sys.platform == 'win32' and os.getenv('DISABLE_SOCKET_PATCH') != '1':
    import socket
    # Keep IPv4 preference but DO NOT hardcode DNS for external services
    _original_getaddrinfo = socket.getaddrinfo

    def _patched_getaddrinfo(host, port, family=0, socktype=0, proto=0, flags=0):
        try:
            # Prefer IPv4 to avoid odd dual-stack issues on some Windows hosts
            return _original_getaddrinfo(host, port, socket.AF_INET, socktype, proto, flags)
        except Exception:
            return _original_getaddrinfo(host, port, family, socktype, proto, flags)

    try:
        socket.getaddrinfo = _patched_getaddrinfo
        import urllib3.util.connection
        urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET
    except Exception:
        pass

# Fix Windows socket error only if not forcing REST
if sys.platform == 'win32' and os.getenv('FORCE_GEMINI_REST') != '1':
    try:
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

import argparse
import json
import re
from urllib.parse import urlparse, parse_qs
from typing import List, Dict

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("❌ Thiếu thư viện! Cài đặt bằng lệnh:")
    print("pip install youtube-transcript-api")
    sys.exit(1)

# Trì hoãn import google.generativeai để tránh lỗi gRPC khi chạy dưới PHP
def _try_import_genai():
    try:
        import google.generativeai as _genai
        return _genai, None
    except Exception as e:
        return None, e


# ============================================================================
# CẤU HÌNH API KEY MẶC ĐỊNH
# ============================================================================
# Đặt API key của bạn vào đây để không cần nhập mỗi lần chạy
# Lấy API key miễn phí tại: https://makersuite.google.com/app/apikey
DEFAULT_GEMINI_API_KEY = "AIzaSyDgrWF9UqYd4pYMJBKdqrwTexM9vTycO0o"  # <-- Điền API key của bạn vào đây

# Ví dụ:
# DEFAULT_GEMINI_API_KEY = "AIzaSyABC123..."
# ============================================================================


def extract_video_id(url_or_id: str) -> str:
    """Trích xuất video ID từ URL YouTube"""
    import json
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", url_or_id):
        return url_or_id
    
    try:
        parsed = urlparse(url_or_id)
        host = (parsed.netloc or "").lower()
        
        if "youtube.com" in host or "youtu.be" in host:
            if host.endswith("youtu.be") and parsed.path:
                vid = parsed.path.strip("/")
                if re.fullmatch(r"[a-zA-Z0-9_-]{11}", vid):
                    return vid
            
            qs = parse_qs(parsed.query)
            v = qs.get("v", [None])[0]
            if v and re.fullmatch(r"[a-zA-Z0-9_-]{11}", v):
                return v
            
            m = re.search(r"/shorts/([a-zA-Z0-9_-]{11})", parsed.path or "")
            if m:
                return m.group(1)
    except Exception:
        pass
    
    raise ValueError("Không thể trích xuất video ID từ URL")


def get_transcript(video_id: str, language: str = "en") -> str:
    """Lấy transcript từ YouTube"""
    import json
    print(f"📹 Video ID: {video_id}")
    print(f"🌐 Đang lấy transcript (ngôn ngữ: {language})...")
    
    langs = []
    if language.startswith("vi"):
        langs = ["vi", "vi-VN", "en", "en-US"]
    else:
        langs = ["en", "en-US", "en-GB", "vi", "vi-VN"]
    
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=langs)
        raw_entries = fetched.to_raw_data()
        text = " ".join(e.get("text", "") for e in raw_entries if e.get("text"))
        text = re.sub(r"\s+", " ", text).strip()
        
        word_count = len(text.split())
        print(f"✅ Đã lấy được {word_count} từ\n")
        return text
    except Exception as e:
        raise RuntimeError(f"Không thể lấy transcript: {e}")


def load_transcript_from_json(path: str) -> str:
    """Load transcript JSON file (e.g., from youtubetranscript.com or fetch_transcript.py) and join to text"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Support multiple JSON formats:
        # 1. Wrapped format from fetch_transcript.py: {"success": true, "transcript": [...], "language": "vi"}
        # 2. Direct format: {"transcripts": [...]} or {"events": [...]} or {"segments": [...]}
        # 3. Simple array: [{"text": "...", ...}, ...]
        
        items = []
        if isinstance(data, dict):
            if 'transcript' in data:
                # Format from fetch_transcript.py
                items = data['transcript']
            else:
                # Try other common keys
                items = data.get('transcripts') or data.get('events') or data.get('segments') or []
        else:
            # Direct array
            items = data
        
        parts = []
        for it in items:
            if isinstance(it, dict):
                t = it.get('text') or it.get('utf8')
                if t:
                    parts.append(t)
        text = "\n".join(parts).strip()
        if not text:
            raise ValueError("Transcript JSON rỗng hoặc không có trường 'text'")
        wc = len(text.split())
        print(f"✅ Đã tải transcript từ file (khoảng {wc} từ)\n")
        return text
    except Exception as e:
        raise RuntimeError(f"Không thể đọc transcript từ file JSON: {e}")


def extract_key_points(transcript: str, max_points: int = 50) -> List[str]:
    """
    import json
    Trích xuất key points từ transcript
    Chia transcript thành các câu và lọc những câu quan trọng
    """
    print("🔍 Đang trích xuất key points chi tiết...")
    
    # Chia thành câu
    sentences = re.split(r'[.!?]+', transcript)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    # Lọc những từ khóa quan trọng
    important_keywords = [
        'important', 'key', 'main', 'essential', 'critical', 'must', 'should',
        'step', 'first', 'second', 'next', 'then', 'finally',
        'example', 'for instance', 'such as', 'like',
        'because', 'reason', 'why', 'how', 'what', 'when', 'where',
        'define', 'definition', 'means', 'refers to',
        'remember', 'note', 'tip', 'trick', 'advice',
        'quan trọng', 'chính', 'cần', 'phải', 'nên',
        'bước', 'đầu tiên', 'thứ hai', 'tiếp theo', 'cuối cùng',
        'ví dụ', 'chẳng hạn', 'như',
        'vì', 'tại sao', 'như thế nào', 'cái gì', 'khi nào',
        'định nghĩa', 'có nghĩa là', 'đề cập đến',
        'lưu ý', 'mẹo', 'lời khuyên'
    ]
    
    # Tính điểm cho mỗi câu
    scored_sentences = []
    for sentence in sentences:
        score = 0
        lower_sent = sentence.lower()
        
        # Điểm dựa trên từ khóa
        for keyword in important_keywords:
            if keyword in lower_sent:
                score += 1
        
        # Điểm dựa trên độ dài (ưu tiên câu trung bình)
        word_count = len(sentence.split())
        if 10 <= word_count <= 40:
            score += 2
        elif word_count < 10:
            score -= 1
        
        # Điểm dựa trên có số (có thể là steps, data)
        if re.search(r'\d+', sentence):
            score += 1
        
        scored_sentences.append((score, sentence))
    
    # Sắp xếp theo điểm và lấy top
    scored_sentences.sort(reverse=True, key=lambda x: x[0])
    key_points = [sent for score, sent in scored_sentences[:max_points] if score > 0]
    
    print(f"✅ Đã trích xuất {len(key_points)} key points\n")
    return key_points


def generate_lesson_with_gemini(
    video_title: str,
    key_points: List[str],
    language: str,
    api_key: str
) -> str:
    import json
    """Generate bài học hoàn chỉnh bằng Gemini API"""
    
    print("🤖 Đang kết nối với Gemini AI...")
    
    # LUÔN ƯU TIÊN REST API để tránh lỗi gRPC WinError 10106 trên Windows/PHP
    # Chỉ dùng gRPC nếu FORCE_GEMINI_GRPC=1
    use_rest = os.getenv("FORCE_GEMINI_GRPC") != "1"
    genai = None
    genai_err = None
    if not use_rest:
        genai, genai_err = _try_import_genai()
        if genai_err is not None:
            # Fallback sang REST nếu import thất bại
            use_rest = True
    
    # Sử dụng gemini-2.0-flash (model mới, nhanh, ổn định)
    model_name = 'gemini-2.0-flash'
    if not use_rest:
        # Dùng thư viện google-generativeai (nếu import được)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
    
    # Chuẩn bị key points
    key_points_text = "\n".join([f"- {point}" for point in key_points])
    
    # Tạo prompt
    if language.startswith("vi"):
        prompt = f"""
Bạn là một chuyên gia giáo dục. Từ các key points được trích xuất từ một video YouTube, 
hãy tạo một BÀI HỌC HOÀN CHỈNH bằng tiếng Việt với cấu trúc sau:

# 📚 TIÊU ĐỀ BÀI HỌC
[Tạo tiêu đề hấp dẫn, súc tích]

## 🎯 MỤC TIÊU HỌC TẬP
[Liệt kê 4-6 mục tiêu cụ thể mà người học sẽ đạt được]

## 💡 CÁC KHÁI NIỆM CHÍNH
[Giải thích chi tiết các khái niệm quan trọng, có định nghĩa, ví dụ minh họa]

## 📝 NỘI DUNG CHI TIẾT
[Trình bày nội dung theo từng phần logic, có thể chia thành các mục con:
- Phần 1: ...
- Phần 2: ...
Giữ đầy đủ thông tin kỹ thuật, code, công thức nếu có]

## 🔍 VÍ DỤ MINH HỌA
[Đưa ra các ví dụ cụ thể, dễ hiểu để minh họa các khái niệm]

## 📋 CÁC BƯỚC THỰC HIỆN (nếu có)
[Nếu video có hướng dẫn thực hành, liệt kê chi tiết từng bước]

## 💡 TIPS & LƯU Ý
[Các mẹo, best practices, điều cần tránh]

## 📌 TÓM TẮT
[Tóm tắt 5-7 điểm chính cần nhớ]

## ❓ CÂU HỎI ÔN TẬP
[5-7 câu hỏi giúp người học kiểm tra kiến thức]

---

KEY POINTS TỪ VIDEO:
{key_points_text}

Hãy tạo bài học CHI TIẾT, DỄ HIỂU, CÓ CẤU TRÚC. Giữ nguyên các thuật ngữ kỹ thuật quan trọng.
Bài học phải ĐẦY ĐỦ để người đọc có thể học được kiến thức MÀ KHÔNG CẦN XEM VIDEO.
"""
    else:
        prompt = f"""
You are an expert educator. From the key points extracted from a YouTube video,
create a COMPREHENSIVE LESSON in English with the following structure:

# 📚 LESSON TITLE
[Create an engaging, concise title]

## 🎯 LEARNING OBJECTIVES
[List 4-6 specific objectives learners will achieve]

## 💡 KEY CONCEPTS
[Explain important concepts in detail with definitions and examples]

## 📝 DETAILED CONTENT
[Present content in logical sections, can be divided into subsections:
- Part 1: ...
- Part 2: ...
Keep all technical information, code, formulas if any]

## 🔍 EXAMPLES
[Provide specific, easy-to-understand examples to illustrate concepts]

## 📋 STEP-BY-STEP GUIDE (if applicable)
[If video has practical instructions, list detailed steps]

## 💡 TIPS & NOTES
[Tips, best practices, common mistakes to avoid]

## 📌 SUMMARY
[Summarize 5-7 key takeaways]

## ❓ REVIEW QUESTIONS
[5-7 questions to help learners test their knowledge]

---

KEY POINTS FROM VIDEO:
{key_points_text}

Create a DETAILED, CLEAR, WELL-STRUCTURED lesson. Keep important technical terms.
The lesson must be COMPLETE so readers can learn WITHOUT WATCHING THE VIDEO.
"""
    
    print("✨ Đang tạo bài học với Gemini AI...")
    print("   (Quá trình này mất 10-30 giây...)\n")
    
    try:
        if use_rest:
            import json, requests
            # Sử dụng API v1 thay vì v1beta
            url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": prompt}]}
                ]
            }
            headers = {"Content-Type": "application/json"}
            r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
            r.raise_for_status()
            data = r.json()
            # Trích nội dung text từ response REST
            lesson = ""
            try:
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for p in parts:
                        t = p.get("text", "")
                        if t:
                            lesson += t
            except Exception:
                pass
            if not lesson:
                raise RuntimeError(f"Phản hồi không hợp lệ từ REST API: {data}")
        else:
            response = model.generate_content(prompt)
            lesson = response.text
        print("✅ Đã tạo bài học thành công!\n")
        return lesson
    except Exception as e:
        raise RuntimeError(f"Lỗi khi gọi Gemini API: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Tạo bài học từ YouTube bằng Gemini AI"
    )
    import json
    parser.add_argument(
        "--url",
        required=True,
        help="URL hoặc ID của video YouTube"
    )
    parser.add_argument(
        "--language", "-l",
        default="en",
        help="Ngôn ngữ (en hoặc vi)"
    )
    parser.add_argument(
        "--api-key", "-k",
        help="Gemini API key (hoặc set biến môi trường GEMINI_API_KEY)"
    )
    parser.add_argument(
        "--output", "-o",
        help="File đầu ra (nếu không chỉ định, chỉ in ra terminal)"
    )
    parser.add_argument(
        "--transcript-json",
        help="Đường dẫn file JSON transcript để bỏ qua bước tải từ YouTube"
    )
    parser.add_argument(
        "--max-points",
        type=int,
        default=50,
        help="Số lượng key points tối đa (mặc định: 50)"
    )
    
    args = parser.parse_args()
    
    # Lấy API key theo thứ tự ưu tiên:
    # 1. Từ tham số --api-key
    # 2. Từ biến môi trường GEMINI_API_KEY
    # 3. Từ DEFAULT_GEMINI_API_KEY trong code
    api_key = args.api_key or os.getenv("GEMINI_API_KEY") or DEFAULT_GEMINI_API_KEY
    if not api_key:
        print("❌ Thiếu Gemini API key!")
        print("\nCách 1: Đặt trực tiếp trong code (khuyến nghị):")
        print('  Mở file gemini_lesson.py và tìm dòng DEFAULT_GEMINI_API_KEY = ""')
        print('  Thay bằng: DEFAULT_GEMINI_API_KEY = "YOUR_KEY"')
        print("\nCách 2: Truyền qua tham số:")
        print('  python gemini_lesson.py --url "..." --api-key "YOUR_KEY"')
        print("\nCách 3: Set biến môi trường:")
        print('  set GEMINI_API_KEY=your_key_here')
        print("\nLấy API key miễn phí tại: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    print("=" * 70)
    print("TẠO BÀI HỌC TỪ YOUTUBE BẰNG GEMINI AI")
    print("=" * 70)
    print()
    
    try:
        # Bước 1: Lấy video ID
        video_id = extract_video_id(args.url)
        
        # Bước 2: Lấy transcript (ưu tiên từ file JSON nếu được cung cấp)
        if args.transcript_json and os.path.isfile(args.transcript_json):
            transcript = load_transcript_from_json(args.transcript_json)
        else:
            transcript = get_transcript(video_id, args.language)
        
        # Bước 3: Trích xuất key points
        key_points = extract_key_points(transcript, args.max_points)
        
        # Bước 4: Generate bài học với Gemini
        lesson = generate_lesson_with_gemini(
            video_title="",
            key_points=key_points,
            language=args.language,
            api_key=api_key
        )
        
        # Bước 5: Hiển thị và lưu kết quả
        print("=" * 70)
        print("BÀI HỌC HOÀN CHỈNH")
        print("=" * 70)
        print()
        print(lesson)
        print()
        print("=" * 70)
        
        # Lưu file nếu được chỉ định
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(lesson)
            print(f"\n✅ Đã lưu bài học vào: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
