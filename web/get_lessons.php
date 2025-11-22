<?php
header('Content-Type: application/json; charset=utf-8');

$lessonsDir = __DIR__ . DIRECTORY_SEPARATOR . 'lessons';
if (!is_dir($lessonsDir)) {
    echo json_encode([]);
    exit;
}

$files = glob($lessonsDir . DIRECTORY_SEPARATOR . '*.md');
usort($files, function ($a, $b) {
    return filemtime($b) <=> filemtime($a);
});

$lessons = [];
foreach ($files as $file) {
    $content = @file($file);
    $firstLine = $content && count($content) > 0 ? trim($content[0]) : '';
    $title = $firstLine !== '' ? $firstLine : pathinfo($file, PATHINFO_FILENAME);
    $lessons[] = [
        'title' => $title,
        'link' => 'lessons/' . basename($file),
        'modifiedTime' => date(DATE_ISO8601, filemtime($file)),
    ];
}

echo json_encode($lessons);
