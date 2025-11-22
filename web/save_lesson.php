<?php
header('Content-Type: application/json; charset=utf-8');

$lessonsDir = __DIR__ . DIRECTORY_SEPARATOR . 'lessons';
if (!is_dir($lessonsDir) && !@mkdir($lessonsDir, 0777, true)) {
    echo json_encode(['success' => false, 'error' => 'Khong tao duoc thu muc luu bai hoc']);
    exit;
}

$rawTitle = isset($_POST['title']) ? trim($_POST['title']) : '';
$content = isset($_POST['content']) ? $_POST['content'] : '';

if ($content === '') {
    echo json_encode(['success' => false, 'error' => 'Khong co noi dung bai hoc de luu']);
    exit;
}

$title = $rawTitle !== '' ? $rawTitle : 'Bai hoc';
$safeName = preg_replace('/[^A-Za-z0-9\-\_\ ]+/', '', $title);
$safeName = trim(str_replace(' ', '-', $safeName), '-_');
if ($safeName === '') {
    $safeName = 'bai-hoc';
}

$filename = $safeName . '-' . time() . '.md';
$filepath = $lessonsDir . DIRECTORY_SEPARATOR . $filename;

if (file_put_contents($filepath, $content) === false) {
    echo json_encode(['success' => false, 'error' => 'Khong luu duoc bai hoc xuong may']);
    exit;
}

echo json_encode([
    'success' => true,
    'title' => $title,
    'link' => 'lessons/' . $filename,
    'modifiedTime' => date(DATE_ISO8601, filemtime($filepath)),
]);
