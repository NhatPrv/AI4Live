#!/usr/bin/env python3
"""
Quickstart: Summarize a YouTube video's transcript using HuggingFace.

Usage examples:
  python quickstart.py --url https://www.youtube.com/watch?v=9aULhzn37DE
  python quickstart.py --id 9aULhzn37DE --model facebook/bart-large-cnn

Requirements (install first):
  pip install youtube-transcript-api transformers torch

Notes:
  - Downloads a summarization model on first run (needs internet).
  - Splits long transcripts into chunks and summarizes each, then optionally
    re-summarizes the combined result for a concise final output.
"""

import argparse
import re
import sys
from typing import List

from urllib.parse import urlparse, parse_qs

# DÙNG API MỚI: tạo instance rồi .fetch()
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize a YouTube transcript using HuggingFace Transformers"
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", type=str, help="YouTube video URL")
    src.add_argument("--id", dest="video_id", type=str, help="YouTube video ID")

    parser.add_argument(
        "--language",
        "-l",
        default="en",
        help="Preferred transcript language (e.g., en, en-US, vi)",
    )
    parser.add_argument(
        "--model",
        default="facebook/bart-large-cnn",
        help="Transformers summarization model (e.g., t5-small, facebook/bart-large-cnn)",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=60,
        help="Minimum tokens for each summary chunk",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=180,
        help="Maximum tokens for each summary chunk",
    )
    parser.add_argument(
        "--chunk-words",
        type=int,
        default=800,
        help="Approx word count per chunk before summarization",
    )
    parser.add_argument(
        "--combine",
        action="store_true",
        help="Re-summarize the concatenated chunk summaries into a final short summary",
    )
    return parser.parse_args()


def extract_video_id(url_or_id: str) -> str:
    # If it already looks like a video ID, return it.
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", url_or_id):
        return url_or_id

    # Try to parse as URL.
    try:
        parsed = urlparse(url_or_id)
        host = (parsed.netloc or "").lower()
        if "youtube.com" in host or "youtu.be" in host:
            # youtu.be/<id>
            if host.endswith("youtu.be") and parsed.path:
                vid = parsed.path.strip("/")
                if re.fullmatch(r"[a-zA-Z0-9_-]{11}", vid):
                    return vid

            # youtube.com/watch?v=<id>
            qs = parse_qs(parsed.query)
            v = qs.get("v", [None])[0]
            if v and re.fullmatch(r"[a-zA-Z0-9_-]{11}", v):
                return v

            # youtube.com/shorts/<id>
            m = re.search(r"/shorts/([a-zA-Z0-9_-]{11})", parsed.path or "")
            if m:
                return m.group(1)
    except Exception:
        pass

    raise ValueError("Could not extract a valid YouTube video ID from input.")


def fetch_transcript_text(video_id: str, preferred_language: str) -> str:
    """
    Lấy transcript bằng youtube-transcript-api 1.2.3:
    - Dùng YouTubeTranscriptApi().fetch(video_id, languages=[...])
    - Trả về 1 chuỗi text nối từ các snippet.
    """
    # Danh sách ngôn ngữ ưu tiên (theo thứ tự)
    langs: List[str] = []
    if preferred_language:
        langs.append(preferred_language)
    for l in ("vi", "vi-VN", "en", "en-US", "en-GB"):
        if l not in langs:
            langs.append(l)

    api = YouTubeTranscriptApi()

    try:
        # API mới: fetch trả về FetchedTranscript
        fetched = api.fetch(video_id, languages=langs)
        raw_entries = fetched.to_raw_data()
        return " ".join(
            _clean_text(e.get("text", "")) for e in raw_entries if e.get("text")
        )
    except (NoTranscriptFound, TranscriptsDisabled):
        # Để main() biết transcript không dùng được
        raise
    except Exception as e:
        # Các lỗi khác (mạng, bị chặn IP, v.v.)
        raise RuntimeError(f"No usable transcript found: {e}")


def _clean_text(s: str) -> str:
    # Collapse whitespace and trim
    s = re.sub(r"\s+", " ", s).strip()
    return s


def chunk_by_words(text: str, chunk_words: int) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    for i in range(0, len(words), chunk_words):
        chunks.append(" ".join(words[i : i + chunk_words]))
    return chunks


def build_summarizer(model_name: str):
    from transformers import pipeline

    device = -1
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            device = 0
    except Exception:
        device = -1

    return pipeline("summarization", model=model_name, device=device)


def summarize_text(
    text: str,
    model_name: str,
    min_length: int,
    max_length: int,
    chunk_words: int,
    combine: bool,
) -> str:
    if not text or not text.strip():
        return ""

    summarizer = build_summarizer(model_name)
    chunks = chunk_by_words(text, chunk_words)
    if not chunks:
        return ""

    summaries = []
    is_t5_like = "t5" in model_name.lower()
    for idx, chunk in enumerate(chunks, 1):
        try:
            res = summarizer(
                ("summarize: " + chunk) if is_t5_like else chunk,
                max_length=max_length,
                min_length=min_length,
                truncation=True,
            )
            summaries.append(res[0]["summary_text"].strip())
        except Exception as e:
            raise RuntimeError(f"Summarization failed on chunk {idx}: {e}")

        # Nếu không muốn nén thêm lần nữa thì trả về toàn bộ các đoạn tóm tắt con
    if not combine:
        return "\n\n".join(summaries)

    # Nếu chỉ có 1 đoạn thì khỏi combine
    if len(summaries) == 1:
        return summaries[0] if summaries else ""

    combined = " ".join(summaries)

    # Heuristic cho lần tóm tắt cuối
    final_max = max(max_length, min(300, max_length * 2))
    final_min = min_length
    try:
        res = summarizer(
            ("summarize: " + combined) if is_t5_like else combined,
            max_length=final_max,
            min_length=final_min,
            truncation=True,
        )
        return res[0]["summary_text"].strip()
    except Exception:
        # Nếu combine fail thì trả luôn phần ghép
        return combined


def main():
    args = parse_args()
    try:
        video_id = extract_video_id(args.url or args.video_id)
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(2)

    try:
        transcript_text = fetch_transcript_text(video_id, args.language)
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        sys.stderr.write(f"Transcript unavailable: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Failed to fetch transcript: {e}\n")
        sys.exit(1)

    if not transcript_text:
        sys.stderr.write("Empty transcript or failed to assemble text.\n")
        sys.exit(1)

    try:
        summary = summarize_text(
            transcript_text,
            model_name=args.model,
            min_length=args.min_length,
            max_length=args.max_length,
            chunk_words=args.chunk_words,
            combine=args.combine,
        )
    except Exception as e:
        sys.stderr.write(f"Summarization failed: {e}\n")
        sys.exit(1)

    print("\n=== SUMMARY ===\n")
    print(summary)


if __name__ == "__main__":
    main()
