@echo off
setlocal enabledelayedexpansion
REM Tạo bài học từ YouTube bằng Gemini AI
REM Usage: gemini_lesson.bat "youtube_url" [language] [output_file]

if "%~1"=="" (
    echo ============================================================
    echo TẠO BÀI HỌC TỪ YOUTUBE BẰNG GEMINI AI
    echo ============================================================
    echo.
    echo Usage: gemini_lesson.bat "youtube_url" [language] [output_file]
    echo.
    echo Tham số:
    echo   youtube_url   : Link video YouTube (bắt buộc)
    echo   language      : Ngôn ngữ (vi hoặc en, mặc định: en)
    echo   output_file   : File lưu kết quả (tùy chọn)
    echo.
    echo Lưu ý:
    echo   - Cần có Gemini API key (miễn phí)
    echo   - Set biến môi trường: set GEMINI_API_KEY=your_key
    echo   - Hoặc truyền qua tham số --api-key
    echo.
    echo Lấy API key miễn phí tại:
    echo   https://makersuite.google.com/app/apikey
    echo.
    echo Ví dụ:
    echo   gemini_lesson.bat "https://youtube.com/watch?v=abc123"
    echo   gemini_lesson.bat "https://youtube.com/watch?v=abc123" vi
    echo   gemini_lesson.bat "https://youtube.com/watch?v=abc123" en lesson.md
    echo.
    echo Ưu điểm:
    echo   ⚡ NHANH (10-30 giây thay vì 5-15 phút)
    echo   ✨ CHẤT LƯỢNG CAO (Gemini AI)
    echo   🆓 MIỄN PHÍ (Google cung cấp)
    echo   🌍 HỖ TRỢ TIẾNG VIỆT TỐT
    echo ============================================================
    exit /b 1
)

set URL=%~1
set LANGUAGE=%~2
set OUTPUT_FILE=%~3

if "%LANGUAGE%"=="" set LANGUAGE=en

echo ============================================================
echo TẠO BÀI HỌC BẰNG GEMINI AI
echo ============================================================
echo Video URL: %URL%
echo Language: %LANGUAGE%
if not "%OUTPUT_FILE%"=="" echo Output: %OUTPUT_FILE%
echo ============================================================
echo.

if "%OUTPUT_FILE%"=="" (
    "C:\Users\KHAC CUONG\AppData\Local\Programs\Python\Python314\python.exe" gemini_lesson.py --url "%URL%" --language %LANGUAGE%
) else (
    "C:\Users\KHAC CUONG\AppData\Local\Programs\Python\Python314\python.exe" gemini_lesson.py --url "%URL%" --language %LANGUAGE% --output "%OUTPUT_FILE%"
)

endlocal
