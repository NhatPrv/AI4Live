#!/usr/bin/env python3
"""
Generate lesson + title from YouTube using transcript or ASR fallback.
- Try transcript via youtube_transcript_api.
- If missing subtitles, download audio via yt-dlp + faster-whisper (CPU).
- Generate title + lesson with Gemini (REST).
"""

import os
import sys
import argparse
import json
import re
import subprocess
import tempfile
import shutil
from urllib.parse import urlparse, parse_qs
from typing import List

from youtube_transcript_api import YouTubeTranscriptApi


# Mặc định lấy từ env, nếu không có sẽ dùng key mặc định như phiên bản cũ.
DEFAULT_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDgrWF9UqYd4pYMJBKdqrwTexM9vTycO0o"


def extract_video_id(url_or_id: str) -> str:
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", url_or_id):
        return url_or_id
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
    raise ValueError("Khong lay duoc video ID")


def get_transcript(video_id: str, language: str = "en") -> str:
    print(f"📹 Video ID: {video_id}")
    print(f"🌐 Đang lấy transcript (ngôn ngữ: {language})...")
    if language.startswith("vi"):
        langs = ["vi", "vi-VN", "en", "en-US", "en-GB"]
    else:
        langs = ["en", "en-US", "en-GB", "vi", "vi-VN"]
    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id, languages=langs)
    raw_entries = fetched.to_raw_data()
    text = " ".join(e.get("text", "") for e in raw_entries if e.get("text"))
    text = re.sub(r"\s+", " ", text).strip()
    wc = len(text.split())
    print(f"✅ Transcript {wc} từ\n")
    return text


def download_audio(video_id: str) -> str:
    url = f"https://www.youtube.com/watch?v={video_id}"
    tmp_dir = tempfile.mkdtemp(prefix="yt_audio_")
    out_path = os.path.join(tmp_dir, "audio.m4a")
    base_cmd = ["-f", "bestaudio/best", "-x", "--audio-format", "m4a", "-o", out_path, url]
    candidates = [
        ["yt-dlp"],
        [sys.executable, "-m", "yt_dlp"],
        ["py", "-3", "-m", "yt_dlp"],
    ]
    print("🎧 Đang tải audio bằng yt-dlp...")
    last_err = None
    for prefix in candidates:
        cmd = prefix + base_cmd
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return out_path
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            last_err = e
            continue
    raise RuntimeError(f"Tải audio thất bại (yt-dlp/ffmpeg?): {last_err}")


def transcribe_with_whisper(audio_path: str, language: str) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("Thiếu faster-whisper. Cài: pip install faster-whisper")
    print("🗣️ Đang nhận diện giọng nói (ASR)...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(
        audio_path,
        language=language if language.startswith("vi") else "en",
        beam_size=2,
        best_of=2,
        vad_filter=True,
    )
    parts = [seg.text.strip() for seg in segments]
    text = " ".join(parts).strip()
    if not text:
        raise RuntimeError("ASR không trả về nội dung.")
    print(f"✅ ASR ~{len(text.split())} từ\n")
    return text


def fetch_transcript_with_asr(video_id: str, language: str) -> str:
    audio_path = None
    try:
        audio_path = download_audio(video_id)
        return transcribe_with_whisper(audio_path, language)
    finally:
        if audio_path:
            shutil.rmtree(os.path.dirname(audio_path), ignore_errors=True)


def extract_key_points(transcript: str, max_points: int = 50) -> List[str]:
    print("🔎 Đang trích xuất key points...")
    sentences = re.split(r'[.!?]+', transcript)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    important = [
        'important', 'key', 'main', 'essential', 'critical', 'must', 'should',
        'step', 'first', 'second', 'next', 'then', 'finally',
        'example', 'for instance', 'such as', 'like',
        'because', 'reason', 'why', 'how', 'what', 'when', 'where',
        'define', 'definition', 'means', 'refers to',
        'remember', 'note', 'tip', 'trick', 'advice',
        'quan trọng', 'chính', 'cần', 'phải', 'nên',
        'bước', 'đầu tiên', 'thứ hai', 'tiếp theo', 'cuối cùng',
        'vì', 'tại sao', 'như thế nào', 'cái gì', 'khi nào',
    ]
    scored = []
    for sentence in sentences:
        score = 0
        lower = sentence.lower()
        for kw in important:
            if kw in lower:
                score += 1
        wc = len(sentence.split())
        if 10 <= wc <= 40:
            score += 2
        elif wc < 10:
            score -= 1
        if re.search(r'\d+', sentence):
            score += 1
        scored.append((score, sentence))
    scored.sort(reverse=True, key=lambda x: x[0])
    key_points = [s for sc, s in scored[:max_points] if sc > 0]
    print(f"✅ Đã trích {len(key_points)} key points\n")
    return key_points


def generate_title_with_gemini(key_points: List[str], language: str, api_key: str) -> str:
    import requests
    model_name = 'gemini-2.0-flash'
    key_points_text = "\n".join([f"- {p}" for p in key_points]) or "- (empty)"
    if language.startswith("vi"):
        prompt = f"Tao mot tieu de ngan gon (toi da 12 tu) bang Tieng Viet cho video nay, chi tra ve duy nhat tieu de.\n\nKey points:\n{key_points_text}"
        default_title = "Bai hoc"
    else:
        prompt = f"Create a short, engaging title (max 12 words) in English. Return ONLY the title.\n\nKey points:\n{key_points_text}"
        default_title = "Lesson"
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        r.raise_for_status()
        data = r.json()
        candidates = data.get("candidates", [])
        text_out = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for p in parts:
                t = p.get("text", "")
                if t:
                    text_out += t
        title = (text_out or "").strip().split("\n")[0]
        title = re.sub(r"^[#\\s]+", "", title).strip()
        return title or default_title
    except Exception:
        return default_title


def generate_lesson_with_gemini(video_title: str, key_points: List[str], language: str, api_key: str) -> str:
    import requests
    print("⚡ Đang tạo bài học với Gemini...")
    model_name = 'gemini-2.0-flash'
    key_points_text = "\n".join([f"- {p}" for p in key_points])
    if language.startswith("vi"):
        title_instruction = f"Su dung tieu de nay va bat dau bai hoc bang heading cap 1 (#): {video_title}" if video_title else "Tao tieu de ngan gon, bat dau bai hoc bang heading cap 1 (#) voi tieu de do."
        prompt = f"""
Ban la mot chuyen gia giao duc. Tu cac key points duoc trich xuat tu mot video YouTube,
hay tao mot BAI HOC HOAN CHINH bang tieng Viet voi cau truc sau:

# TIEU DE BAI HOC
{title_instruction}

## MUC TIEU HOC TAP
[Liet ke 4-6 muc tieu cu the ma nguoi hoc se dat duoc]

## CAC KHAI NIEM CHINH
[Giai thich chi tiet cac khai niem quan trong, co dinh nghia, vi du minh hoa]

## NOI DUNG CHI TIET
[Trinh bay noi dung theo tung phan logic, co the chia thanh cac muc con:
- Phan 1: ...
- Phan 2: ...
Giu day du thong tin ky thuat, code, cong thuc neu co]

## VI DU MINH HOA
[Dua ra cac vi du cu the, de hieu de minh hoa cac khai niem]

## CAC BUOC THUC HIEN (neu co)
[Neu video co huong dan thuc hanh, liet ke chi tiet tung buoc]

## TIPS & LUU Y
[Cac meo, best practices, dieu can tranh]

## TOM TAT
[Tom tat 5-7 diem chinh can nho]

## CAU HOI ON TAP
[5-7 cau hoi giup nguoi hoc kiem tra kien thuc]

---

KEY POINTS TU VIDEO:
{key_points_text}

Hay tao bai hoc CHI TIET, DE HIEU, CO CAU TRUC. Giu nguyen cac thuat ngu ky thuat quan trong.
Bai hoc phai DAY DU de nguoi doc co the hoc duoc kien thuc MA KHONG CAN XEM VIDEO.
"""
    else:
        title_instruction = f"Use this title and start the lesson with a level-1 heading (#): {video_title}" if video_title else "Create a short title and start the lesson with it as a level-1 heading (#)."
        prompt = f"""
You are an expert educator. From the key points extracted from a YouTube video,
create a COMPREHENSIVE LESSON in English with the following structure:

# LESSON TITLE
{title_instruction}

## LEARNING OBJECTIVES
[List 4-6 specific objectives learners will achieve]

## KEY CONCEPTS
[Explain important concepts in detail with definitions and examples]

## DETAILED CONTENT
[Present content in logical sections, can be divided into subsections:
- Part 1: ...
- Part 2: ...
Keep all technical information, code, formulas if any]

## EXAMPLES
[Provide specific, easy-to-understand examples to illustrate concepts]

## STEP-BY-STEP GUIDE (if applicable)
[If video has practical instructions, list detailed steps]

## TIPS & NOTES
[Tips, best practices, common mistakes to avoid]

## SUMMARY
[Summarize 5-7 key takeaways]

## REVIEW QUESTIONS
[5-7 questions to help learners test their knowledge]

---

KEY POINTS FROM VIDEO:
{key_points_text}

Create a DETAILED, CLEAR, WELL-STRUCTURED lesson. Keep important technical terms.
The lesson must be COMPLETE so readers can learn WITHOUT WATCHING THE VIDEO.
"""
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
    r.raise_for_status()
    data = r.json()
    lesson = ""
    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        for p in parts:
            t = p.get("text", "")
            if t:
                lesson += t
    if not lesson:
        raise RuntimeError(f"Phan hoi khong hop le tu Gemini: {data}")
    return lesson


def main() -> int:
    parser = argparse.ArgumentParser(description="Tao bai hoc tu YouTube bang Gemini AI")
    parser.add_argument("--url", required=True, help="URL hoac ID video YouTube")
    parser.add_argument("--language", "-l", default="en", help="Ngon ngu (en hoac vi)")
    parser.add_argument("--api-key", "-k", help="Gemini API key (hoac set bien moi truong GEMINI_API_KEY)")
    parser.add_argument("--output", "-o", help="File dau ra (neu khong chi dinh, chi in ra)")
    parser.add_argument("--transcript-json", help="Duong dan file JSON transcript neu co san")
    parser.add_argument("--max-points", type=int, default=50, help="So luong key points toi da (mac dinh 50)")
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("GEMINI_API_KEY") or DEFAULT_GEMINI_API_KEY
    if not api_key:
        print("Thiếu Gemini API key! Set GEMINI_API_KEY hoặc --api-key.")
        return 1

    print("=" * 70)
    print("TAO BAI HOC TU YOUTUBE BANG GEMINI AI")
    print("=" * 70)
    print()

    try:
        video_id = extract_video_id(args.url)
        if args.transcript_json and os.path.isfile(args.transcript_json):
            transcript = load_transcript_from_json(args.transcript_json)
        else:
            try:
                transcript = get_transcript(video_id, args.language)
            except Exception as e:
                print(f"❌ Lỗi transcript: {e}")
                print("➡ Thử nhận diện giọng nói từ audio (ASR fallback)...")
                transcript = fetch_transcript_with_asr(video_id, args.language)

        key_points = extract_key_points(transcript, args.max_points)
        title = generate_title_with_gemini(key_points, args.language, api_key)
        lesson = generate_lesson_with_gemini(title, key_points, args.language, api_key)

        print("=" * 70)
        print("BAI HOC HOAN CHINH")
        print("=" * 70)
        print()
        print(lesson)
        print()
        print("=" * 70)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(lesson)
            print(f"\nĐã lưu bài học vào: {args.output}")
        return 0
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
