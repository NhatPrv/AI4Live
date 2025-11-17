<?php
header('Content-Type: application/json; charset=utf-8');

$config = require __DIR__ . '/config.php';
$PYTHON = $config['python'] ?? 'python';
$repoRoot = realpath(__DIR__ . '/..');

$videoTitle = isset($_POST['title']) ? trim($_POST['title']) : 'Bài học';

$uploadScript = $repoRoot . DIRECTORY_SEPARATOR . 'upload_to_drive.py';
$command = escapeshellarg($PYTHON) . ' ' . escapeshellarg($uploadScript) . ' ' . escapeshellarg($videoTitle);

// Set up environment với PYTHONPATH để Python tìm được packages
$pythonExePath = $PYTHON;
$pythonHome = dirname($pythonExePath);
$systemSite = $pythonHome . DIRECTORY_SEPARATOR . 'Lib' . DIRECTORY_SEPARATOR . 'site-packages';

// User site-packages (nơi pip install --user lưu packages)
$userSite = '';
if (preg_match('/Python(\d{3})/i', $pythonExePath, $m)) {
    $pyVerDigits = $m[1];
    $appData = getenv('APPDATA');
    if ($appData) {
        $userSite = $appData . DIRECTORY_SEPARATOR . 'Python' . DIRECTORY_SEPARATOR . 'Python' . $pyVerDigits . DIRECTORY_SEPARATOR . 'site-packages';
    }
}

$paths = [];
if (is_dir($systemSite)) { $paths[] = $systemSite; }
if ($userSite && is_dir($userSite)) { $paths[] = $userSite; }

$env = [
    'PYTHONIOENCODING' => 'utf-8',
    'PYTHONPATH' => implode(PATH_SEPARATOR, $paths),
    'SystemRoot' => getenv('SystemRoot') ?: 'C:\\Windows',
    'APPDATA' => getenv('APPDATA'),
    'USERPROFILE' => getenv('USERPROFILE'),
];

$descriptorspec = [
    0 => ['pipe', 'r'],
    1 => ['pipe', 'w'],
    2 => ['pipe', 'w'],
];

$process = proc_open($command, $descriptorspec, $pipes, $repoRoot, $env);

if (is_resource($process)) {
    fclose($pipes[0]);
    $stdout = stream_get_contents($pipes[1]);
    $stderr = stream_get_contents($pipes[2]);
    fclose($pipes[1]);
    fclose($pipes[2]);
    $exitCode = proc_close($process);
    
    if ($exitCode === 0 && preg_match('/Link xem:\s*(https:\/\/[^\s]+)/', $stdout, $m)) {
        echo json_encode(['success' => true, 'link' => $m[1]]);
    } else {
        echo json_encode(['success' => false, 'error' => $stderr ?: 'Không thể upload']);
    }
} else {
    echo json_encode(['success' => false, 'error' => 'Không thể khởi động Python']);
}
?>
