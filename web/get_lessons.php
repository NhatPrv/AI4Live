<?php
header('Content-Type: application/json; charset=utf-8');

$python = 'C:\\Python313\\python.exe';
$script = dirname(__DIR__) . DIRECTORY_SEPARATOR . 'list_lessons.py';

if (!file_exists($script)) {
    echo json_encode([]);
    exit;
}

$command = escapeshellarg($python) . ' ' . escapeshellarg($script);

$descriptorspec = [
    0 => ['pipe', 'r'],
    1 => ['pipe', 'w'],
    2 => ['pipe', 'w'],
];

// Setup environment for Python
$env = [
    'PYTHONIOENCODING' => 'utf-8',
    'SystemRoot' => getenv('SystemRoot') ?: 'C:\\Windows',
    'TEMP' => getenv('TEMP') ?: sys_get_temp_dir(),
    'TMP' => getenv('TMP') ?: sys_get_temp_dir(),
    'USERPROFILE' => getenv('USERPROFILE'),
    'APPDATA' => getenv('APPDATA'),
    'LOCALAPPDATA' => getenv('LOCALAPPDATA'),
];

$process = proc_open($command, $descriptorspec, $pipes, dirname(__DIR__), $env);

if (is_resource($process)) {
    fclose($pipes[0]);
    $output = stream_get_contents($pipes[1]);
    $error = stream_get_contents($pipes[2]);
    fclose($pipes[1]);
    fclose($pipes[2]);
    $exitCode = proc_close($process);
    
    if ($exitCode === 0 && !empty($output)) {
        echo $output;
    } else {
        echo '[]';
    }
} else {
    echo '[]';
}
?>
