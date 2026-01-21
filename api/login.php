<?php
require_once __DIR__ . '/db.php';
require_once __DIR__ . '/helpers.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
  respond(405, ['ok' => false, 'message' => 'Method not allowed']);
}

$in = json_input();
$username = clean_username((string)($in['username'] ?? ''));
$password = (string)($in['password'] ?? '');

if ($username === '' || $password === '') {
  respond(400, ['ok' => false, 'message' => 'Username dan password wajib diisi.']);
}

$pdo = db();

$stmt = $pdo->prepare("SELECT id, username, password_hash FROM users WHERE username = ?");
$stmt->execute([$username]);
$user = $stmt->fetch();

if (!$user || !password_verify($password, $user['password_hash'])) {
  respond(401, ['ok' => false, 'message' => 'Username atau password salah.']);
}

// generate token (7 hari)
$token = bin2hex(random_bytes(32));
$expires = (new DateTime('+7 days'))->format('Y-m-d H:i:s');

$stmt = $pdo->prepare("INSERT INTO user_tokens (user_id, token, expires_at) VALUES (?, ?, ?)");
$stmt->execute([(int)$user['id'], $token, $expires]);

respond(200, [
  'ok' => true,
  'message' => 'Login berhasil.',
  'token' => $token,
  'expires_at' => $expires,
  'user' => [
    'id' => (int)$user['id'],
    'username' => $user['username']
  ]
]);
