# Web UI (PHP) for Gemini Lesson Generator

This minimal PHP UI lets you paste a YouTube URL and generate a full lesson using `gemini_lesson.py`. The result prints into a textarea.

## Prerequisites
- PHP 7.4+ on Windows (check with `php -v`)
- Python 3.10+ with packages installed:
  - `pip install youtube-transcript-api google-generativeai`
- A valid Gemini API key (get one free at https://makersuite.google.com/app/apikey)

## Quick Start (Windows, cmd)
1. (Optional) Set your Python path and defaults in `web/config.php`.
   - Or set env var to point to your Python:
     ```cmd
     set PYTHON_EXE=C:\Users\<YOU>\AppData\Local\Programs\Python\Python3xx\python.exe
     ```
2. Set your API key once (optional if you prefer to paste it in the form):
   ```cmd
   set GEMINI_API_KEY=your_key_here
   ```
3. Start the built-in PHP server from the repo root:
   ```cmd
   cd e:\code\pyton\Youtube-transcript-summarizer
   php -S localhost:8000 -t web
   ```
4. Open http://localhost:8000 in your browser.
5. Paste a YouTube URL, choose language, optionally provide API key, then click "Tạo bài học".

## Notes
- The page executes `gemini_lesson.py` under the hood and captures stdout.
- If the button spins for a while, transcript fetch and model generation are running (10–30s typical).
- If you encounter encoding issues, ensure `PYTHONIOENCODING` is set to `utf-8` (we set it automatically for the process).
