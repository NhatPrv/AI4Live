<?php
// Simple PHP frontend to run gemini_lesson.py and show result
// Ensure PHP 7.4+ and Python packages installed: youtube-transcript-api, google-generativeai

header('Content-Type: text/html; charset=utf-8');
mb_internal_encoding('UTF-8');
ini_set('default_charset', 'UTF-8');
set_time_limit(300);

$config = require __DIR__ . '/config.php';
$PYTHON = $config['python'] ?? 'python';
$DEFAULT_LANG = $config['default_language'] ?? 'vi';
$GEMINI_KEY = $config['gemini_api_key'] ?? '';

$repoRoot = realpath(__DIR__ . '/..');
$scriptPath = $repoRoot . DIRECTORY_SEPARATOR . 'gemini_lesson.py';

$url = isset($_POST['url']) ? trim($_POST['url']) : '';
$lang = isset($_POST['language']) ? trim($_POST['language']) : $DEFAULT_LANG;
$output = '';
$error = '';
$exitCode = null;
$debugInfo = '';

// Debug: Check if form was submitted
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  $debugInfo = "Form submitted! POST data received.";
}

// Process request on any POST (works with AJAX, no need for submit field)
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $debugInfo .= "\nChecking URL...";
    
    if ($url === '') {
        $error = 'Vui lòng nhập URL YouTube.';
    } elseif (!file_exists($scriptPath)) {
        $error = 'Không tìm thấy gemini_lesson.py tại: ' . $scriptPath;
    } else {
        $debugInfo .= "\nScript found!";
        
        // Helper: extract video ID
        $videoId = '';
        if (preg_match('~([a-zA-Z0-9_-]{11})~', $url, $m)) {
          $videoId = $m[1];
        }

        // Try to prefetch transcript via Python helper script (bypass PHP subprocess network issues)
        $transcriptJsonPath = '';
        if ($videoId !== '') {
          $tmpDir = __DIR__ . DIRECTORY_SEPARATOR . 'tmp';
          if (!is_dir($tmpDir)) { @mkdir($tmpDir, 0777, true); }
          
          $transcriptFile = $tmpDir . DIRECTORY_SEPARATOR . 'transcript_' . $videoId . '_' . $lang . '.json';
          $fetchScript = $repoRoot . DIRECTORY_SEPARATOR . 'fetch_transcript.py';
          
          if (file_exists($fetchScript)) {
            $debugInfo .= "\nFetching transcript using Python helper...";
            
            // Run Python fetch_transcript.py in a separate process
            $fetchCmd = escapeshellarg($PYTHON) . ' ' . escapeshellarg($fetchScript) . ' ' . 
                        escapeshellarg($videoId) . ' ' . escapeshellarg($lang) . ' ' . 
                        escapeshellarg($transcriptFile);
            
            $descriptorspec = [
              0 => ['pipe', 'r'],
              1 => ['pipe', 'w'],
              2 => ['pipe', 'w'],
            ];
            
            $proc = proc_open($fetchCmd, $descriptorspec, $pipes, $repoRoot);
            if (is_resource($proc)) {
              fclose($pipes[0]);
              $fetchOut = stream_get_contents($pipes[1]);
              fclose($pipes[1]);
              $fetchErr = stream_get_contents($pipes[2]);
              fclose($pipes[2]);
              $fetchExit = proc_close($proc);
              
              if ($fetchExit === 0 && file_exists($transcriptFile)) {
                $transcriptJsonPath = $transcriptFile;
                $debugInfo .= "\n✅ Transcript fetched successfully via Python helper!";
              } else {
                $debugInfo .= "\n❌ Transcript fetch failed. Exit: $fetchExit";
                if ($fetchErr) {
                  $debugInfo .= "\nError: " . substr($fetchErr, 0, 200);
                }
              }
            } else {
              $debugInfo .= "\n❌ Failed to run Python helper script";
            }
          } else {
            $debugInfo .= "\n⚠️ fetch_transcript.py not found";
          }
        }

        // Build base args
        $outputFile = $repoRoot . DIRECTORY_SEPARATOR . 'lesson_output.md';
        $baseArgs = [
          escapeshellarg($scriptPath),
          '--url ' . escapeshellarg($url),
          '--language ' . escapeshellarg($lang),
          '--output ' . escapeshellarg($outputFile),
        ];
        if ($transcriptJsonPath !== '') {
          $baseArgs[] = '--transcript-json ' . escapeshellarg($transcriptJsonPath);
        }
        if (!empty($GEMINI_KEY)) {
          $baseArgs[] = '--api-key ' . escapeshellarg($GEMINI_KEY);
        }

        // Define attempts: configured python, Windows py launcher, Windows py -3
        $attemptDefs = [
          ['exe' => escapeshellarg($PYTHON), 'label' => 'configured'],
          ['exe' => 'py', 'label' => 'py'],
          ['exe' => 'py -3', 'label' => 'py -3'],
        ];

        $attemptLogs = [];
        $succeeded = false;
        $output = '';
        $exitCode = null;
        $command = '';

        foreach ($attemptDefs as $def) {
          $pythonExe = $def['exe'];
          $label = $def['label'];

          // Assemble command
          $cmdParts = array_merge([$pythonExe], $baseArgs);
          $command = implode(' ', $cmdParts);

          $debugInfo .= "\nAttempt with: $label";
          $debugInfo .= "\nCommand: $command";
          $debugInfo .= "\nExecuting Python...";

          // Prepare process
          $descriptorspec = [
            0 => ['pipe', 'r'],  // stdin
            1 => ['pipe', 'w'],  // stdout
            2 => ['pipe', 'w'],  // stderr
          ];
          
          // Create clean environment for Python subprocess to avoid network conflicts
          $env = [
            'PYTHONIOENCODING' => 'utf-8',
            'PYTHONDONTWRITEBYTECODE' => '1',
            'DISABLE_SOCKET_PATCH' => '1',
            'FORCE_GEMINI_REST' => '1',
            'SystemRoot' => getenv('SystemRoot') ?: 'C:\\Windows',
            'TEMP' => getenv('TEMP') ?: sys_get_temp_dir(),
            'TMP' => getenv('TMP') ?: sys_get_temp_dir(),
            'USERPROFILE' => getenv('USERPROFILE'),
            'APPDATA' => getenv('APPDATA'),
            'LOCALAPPDATA' => getenv('LOCALAPPDATA'),
          ];
          
          // Ensure Python can see site-packages even when running under PHP
          $pythonExePath = $PYTHON; // unescaped path from config
          $pythonHome = dirname($pythonExePath);
          $systemSite = $pythonHome . DIRECTORY_SEPARATOR . 'Lib' . DIRECTORY_SEPARATOR . 'site-packages';
          $userSite = '';
          if (preg_match('/Python(\d{3})/i', $pythonExePath, $m)) {
            $pyVerDigits = $m[1]; // e.g., 313
            $appData = getenv('APPDATA'); // e.g., C:\\Users\\<User>\\AppData\\Roaming
            if ($appData) {
              $userSite = $appData . DIRECTORY_SEPARATOR . 'Python' . DIRECTORY_SEPARATOR . 'Python' . $pyVerDigits . DIRECTORY_SEPARATOR . 'site-packages';
            }
          }
          $paths = [];
          if (is_dir($systemSite)) { $paths[] = $systemSite; }
          if ($userSite && is_dir($userSite)) { $paths[] = $userSite; }
          if (!empty($paths)) {
            $env['PYTHONPATH'] = implode(PATH_SEPARATOR, $paths);
          }
          
          // Thêm thư mục Python vào PATH để đảm bảo DLL loading
          $pythonDir = dirname($pythonExePath);
          $systemPath = getenv('PATH') ?: 'C:\\Windows\\System32;C:\\Windows';
          $env['PATH'] = $pythonDir . PATH_SEPARATOR . $systemPath;

          $proc = proc_open($command, $descriptorspec, $pipes, $repoRoot, $env);
          if (is_resource($proc)) {
            fclose($pipes[0]);
            $stdout = stream_get_contents($pipes[1]);
            fclose($pipes[1]);
            $stderr = stream_get_contents($pipes[2]);
            fclose($pipes[2]);
            $exitCode = proc_close($proc);

            $attemptLogs[] = [
              'label' => $label,
              'exit' => $exitCode,
              'stdout_len' => strlen($stdout),
              'stderr_len' => strlen($stderr),
              'stdout' => $stdout,
              'stderr' => $stderr,
            ];

            $debugInfo .= "\nExit code: $exitCode";
            $debugInfo .= "\nStdout length: " . strlen($stdout);
            $debugInfo .= "\nStderr length: " . strlen($stderr);

            if ($exitCode === 0 && file_exists($outputFile)) {
              $output = file_get_contents($outputFile);
              $succeeded = true;
              break;
            }

            // Heuristic: if python not found, try next attempt
            if (stripos($stderr, 'is not recognized') !== false || stripos($stderr, 'not found') !== false) {
              $debugInfo .= "\nPython not found for attempt '$label', trying next...";
              continue;
            }
          } else {
            $attemptLogs[] = [
              'label' => $label,
              'exit' => null,
              'stdout_len' => 0,
              'stderr_len' => 0,
              'stderr' => 'proc_open failed',
            ];
            $debugInfo .= "\nproc_open failed for attempt '$label'";
          }
        }

        if (!$succeeded) {
          // Build helpful error message
          $msg = "Không thể chạy Python.\n\nCác lần thử:\n";
          foreach ($attemptLogs as $log) {
            $msg .= "- " . $log['label'] . ": exit=" . var_export($log['exit'], true) . ", stdout_len=" . $log['stdout_len'] . ", stderr_len=" . $log['stderr_len'] . "\n";
            if (!empty($log['stdout'])) {
              $msg .= "  stdout: " . $log['stdout'] . "\n";
            }
            if (!empty($log['stderr'])) {
              $msg .= "  stderr: " . $log['stderr'] . "\n";
            }
          }
          $msg .= "\nCách sửa: Mở file web/config.php và đặt 'python' = đường dẫn đầy đủ tới python.exe.\nVí dụ: C:\\Users\\<User>\\AppData\\Local\\Programs\\Python\\Python312\\python.exe\nHoặc đặt biến môi trường hệ thống PYTHON_EXE trỏ tới python.exe.\nBạn cũng có thể cài Python Launcher và để trống để dùng 'py'/'py -3'.";
          $error = $msg;
        }
    }
}
?>
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tạo bài học từ YouTube (Gemini)</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; background: #f7f7fb; color: #222; }
    .container { max-width: 900px; margin: 0 auto; background: #fff; padding: 20px 24px; border-radius: 12px; box-shadow: 0 6px 20px rgba(0,0,0,0.08); }
    h1 { margin-top: 0; font-size: 20px; }
    label { display: block; margin: 12px 0 6px; font-weight: 600; }
    input[type=text], input[type=password], select { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
    .row { display: flex; gap: 12px; }
    .row > div { flex: 1; }
    button { margin-top: 16px; background: #2d6cdf; color: white; border: 0; border-radius: 8px; padding: 10px 16px; font-size: 14px; cursor: pointer; }
    button:disabled { opacity: .7; cursor: not-allowed; }
    .note { color: #666; font-size: 12px; }
    .error { background: #ffe9e9; color: #930; padding: 10px 12px; border-radius: 8px; margin-top: 12px; white-space: pre-wrap; }
    .ok { background: #e9f7ef; color: #145a32; padding: 10px 12px; border-radius: 8px; margin-top: 12px; }
    textarea { width: 100%; height: 480px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; padding: 12px; border-radius: 8px; border: 1px solid #ddd; background: #fafafa; }
    .footer { margin-top: 16px; color: #666; font-size: 12px; }
    
    /* Loading Spinner */
    .loading-overlay { 
      display: none; 
      position: fixed; 
      top: 0; 
      left: 0; 
      right: 0; 
      bottom: 0; 
      background: rgba(0,0,0,0.7); 
      z-index: 9999; 
      align-items: center; 
      justify-content: center;
      flex-direction: column;
    }
    .loading-overlay.show { display: flex; }
    .spinner { 
      width: 60px; 
      height: 60px; 
      border: 6px solid #f3f3f3; 
      border-top: 6px solid #2d6cdf; 
      border-radius: 50%; 
      animation: spin 1s linear infinite; 
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .loading-text { 
      color: white; 
      margin-top: 20px; 
      font-size: 16px; 
      font-weight: 600; 
    }
    .loading-subtext {
      color: #ccc;
      margin-top: 8px;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <!-- Loading Overlay -->
  <div class="loading-overlay" id="loadingOverlay">
    <div class="spinner"></div>
    <div class="loading-text">🤖 Đang tạo bài học với Gemini AI...</div>
    <div class="loading-subtext">Quá trình này có thể mất 30-90 giây. Vui lòng chờ...</div>
  </div>

  <div class="container">
    <h1>📚 Tạo bài học từ YouTube bằng Gemini</h1>
    
    <?php if ($debugInfo !== ''): ?>
      <div style="background: #fff3cd; color: #856404; padding: 10px; border-radius: 8px; margin-bottom: 12px;">
        <?= htmlspecialchars($debugInfo, ENT_QUOTES, 'UTF-8') ?>
      </div>
    <?php endif; ?>

    <form method="post" action="">
      <label for="url">URL YouTube</label>
      <input type="text" id="url" name="url" placeholder="https://www.youtube.com/watch?v=..." value="<?= htmlspecialchars($url, ENT_QUOTES, 'UTF-8') ?>" required />

      <label for="language">Ngôn ngữ</label>
      <select id="language" name="language">
        <option value="vi" <?= $lang === 'vi' ? 'selected' : '' ?>>Tiếng Việt</option>
        <option value="en" <?= $lang === 'en' ? 'selected' : '' ?>>English</option>
      </select>

      <button type="submit" name="submit">Tạo bài học</button>
    </form>

    <?php if ($error !== ''): ?>
      <div class="error"><strong>Lỗi:</strong><br><?= nl2br(htmlspecialchars($error, ENT_QUOTES, 'UTF-8')) ?></div>
    <?php endif; ?>
    
    <?php if ($_SERVER['REQUEST_METHOD'] === 'POST' && $exitCode !== null): ?>
      <div class="note" style="margin-top: 12px; padding: 10px; background: #f0f0f0; border-radius: 8px;">
        <strong>Debug Info:</strong><br>
        Exit Code: <?= $exitCode ?><br>
        Command: <code><?= htmlspecialchars($command ?? 'N/A', ENT_QUOTES, 'UTF-8') ?></code><br>
        Python Path: <code><?= htmlspecialchars($PYTHON, ENT_QUOTES, 'UTF-8') ?></code><br>
        Script Path: <code><?= htmlspecialchars($scriptPath, ENT_QUOTES, 'UTF-8') ?></code><br>
        Script Exists: <?= file_exists($scriptPath) ? '✅ Yes' : '❌ No' ?>
      </div>
    <?php endif; ?>

    <?php if ($output !== ''): ?>
      <div class="ok">✅ Hoàn tất. Kết quả hiển thị bên dưới.</div>
      <label for="result">Kết quả</label>
      <textarea id="result" readonly><?= htmlspecialchars($output, ENT_QUOTES, 'UTF-8') ?></textarea>
    <?php endif; ?>

    <div class="footer">
      Yêu cầu: Python (đã cài <code>youtube-transcript-api</code>, <code>google-generativeai</code>) và mạng Internet.<br>
      API key đã được cấu hình trong code.
    </div>
  </div>

  <script>
    // AJAX form submission - no page reload
    const form = document.querySelector('form');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const errorDiv = document.querySelector('.error');
    
    form?.addEventListener('submit', async (e) => {
      e.preventDefault(); // Prevent page reload
      console.log('Form submitting via AJAX...');
      
      // Get form data
      const formData = new FormData(form);
      
      // Show loading overlay
      loadingOverlay.classList.add('show');
      
      // Hide previous errors/results
      const oldError = document.querySelector('.error');
      const oldResult = document.querySelector('.ok');
      const oldDebug = document.querySelectorAll('.note');
      if (oldError) oldError.remove();
      if (oldResult) oldResult.parentElement.querySelectorAll('.ok, label[for="result"], textarea#result').forEach(el => el.remove());
      oldDebug.forEach(el => el.remove());
      
      // Update loading text every 10 seconds
      let seconds = 0;
      const interval = setInterval(() => {
        seconds += 10;
        const loadingText = document.querySelector('.loading-text');
        if (loadingText) {
          if (seconds < 30) {
            loadingText.textContent = '📥 Đang tải transcript từ YouTube...';
          } else if (seconds < 60) {
            loadingText.textContent = '🔍 Đang phân tích nội dung...';
          } else {
            loadingText.textContent = '✨ Đang tạo bài học với Gemini AI...';
          }
        }
      }, 10000);
      
      try {
        // Send AJAX request
        console.log('Sending request to server...');
        const response = await fetch('', {
          method: 'POST',
          body: formData
        });
        
        console.log('Response received. Status:', response.status);
        const html = await response.text();
        console.log('Response length:', html.length, 'bytes');
        
        // Parse response
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
                // Extract debug info first (for troubleshooting)
                const debugInfoEl = doc.querySelector('div[style*="fff3cd"]'); // Yellow debug box
                if (debugInfoEl) {
                  console.log('Debug Info:', debugInfoEl.textContent);
                  form.insertAdjacentHTML('afterend', debugInfoEl.outerHTML);
                }
        
        
        // Extract error if exists
        const errorEl = doc.querySelector('.error');
        if (errorEl) {
                    console.log('Error found:', errorEl.textContent);
          form.insertAdjacentHTML('afterend', errorEl.outerHTML);
        }
        
        // Extract debug info box (technical details)
        const debugEl = doc.querySelector('.note');
        if (debugEl) {
                    console.log('Debug box found');
          form.insertAdjacentHTML('afterend', debugEl.outerHTML);
        }
        
        // Extract result if exists
        const resultOk = doc.querySelector('.ok');
        const resultLabel = doc.querySelector('label[for="result"]');
        const resultTextarea = doc.querySelector('textarea#result');
        
        if (resultOk && resultTextarea) {
                    console.log('✅ Result received! Length:', resultTextarea.value?.length || resultTextarea.textContent?.length, 'chars');
          form.insertAdjacentHTML('afterend', resultOk.outerHTML);
          form.insertAdjacentHTML('beforeend', resultLabel.outerHTML);
          form.insertAdjacentHTML('beforeend', resultTextarea.outerHTML);
                } else {
                  console.log('⚠️ No result found in response');
        }
        
      } catch (error) {
        console.error('❌ AJAX error:', error);
        form.insertAdjacentHTML('afterend', 
          '<div class="error"><strong>Lỗi:</strong> Không thể kết nối đến server. ' + error.message + '</div>'
        );
      } finally {
        // Hide loading
        clearInterval(interval);
        loadingOverlay.classList.remove('show');
      }
    });
  </script>
</body>
</html>
