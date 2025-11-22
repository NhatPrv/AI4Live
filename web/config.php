<?php
return [
    // Update this if your Python is elsewhere; falls back to env PYTHON_EXE in index.php.
    'python' => 'C:\\Python313\\python.exe',
    'default_language' => 'vi',
    // Leave empty to use GEMINI_API_KEY from environment or form input.
    'gemini_api_key' => getenv('GEMINI_API_KEY') ?: '',
];
