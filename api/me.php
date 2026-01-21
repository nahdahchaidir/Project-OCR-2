<?php
require_once __DIR__ . '/db.php';
require_once __DIR__ . '/helpers.php';

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
  respond(405, ['ok' => false, 'message' => 'Method not allowed']);
}

$token = bearer_token();
if ($token === '') {
  respond(401, ['ok' => false, 'message' => 'Token tidak ada.']);
}

$pdo = db();

$stmt = $pdo->prepare("
  SELECT u.id, u.username, t.expires_at
  FROM user_tokens t
  JOIN users u ON u.id = t.user_id
  WHERE t.token = ? AND t.expires_at > NOW()
  LIMIT 1
");
$stmt->execute([$token]);
$row = $stmt->fetch();

if (!$row) {
  respond(401, ['ok' => false, 'message' => 'Token tidak valid / expired.']);
}

respond(200, [
  'ok' => true,
  'user' => [
    'id' => (int)$row['id'],
    'username' => $row['username']
  ],
  'expires_at' => $row['expires_at']
]);
