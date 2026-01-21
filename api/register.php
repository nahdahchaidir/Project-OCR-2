<?php
require_once __DIR__ . '/db.php';
require_once __DIR__ . '/helpers.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
  respond(405, ['ok' => false, 'message' => 'Method not allowed']);
}

$in = json_input();
$username = clean_username((string)($in['username'] ?? ''));
$password = (string)($in['password'] ?? '');

if (!validate_username($username)) {
  respond(400, ['ok' => false, 'message' => 'Username tidak valid (3-30, huruf/angka/underscore/dot).']);
}
if (!validate_password($password)) {
  respond(400, ['ok' => false, 'message' => 'Password minimal 6 karakter.']);
}

$pdo = db();

// cek duplicate
$stmt = $pdo->prepare("SELECT id FROM users WHERE username = ?");
$stmt->execute([$username]);
if ($stmt->fetch()) {
  respond(409, ['ok' => false, 'message' => 'Username sudah terdaftar.']);
}

$hash = password_hash($password, PASSWORD_BCRYPT);

$stmt = $pdo->prepare("INSERT INTO users (username, password_hash) VALUES (?, ?)");
$stmt->execute([$username, $hash]);

respond(201, [
  'ok' => true,
  'message' => 'User berhasil dibuat.',
  'user' => [
    'id' => (int)$pdo->lastInsertId(),
    'username' => $username
  ]
]);
