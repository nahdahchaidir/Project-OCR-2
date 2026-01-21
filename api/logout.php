<?php
require_once __DIR__ . '/db.php';
require_once __DIR__ . '/helpers.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
  respond(405, ['ok' => false, 'message' => 'Method not allowed']);
}

$token = bearer_token();
if ($token === '') {
  respond(400, ['ok' => false, 'message' => 'Token tidak ada.']);
}

$pdo = db();
$stmt = $pdo->prepare("DELETE FROM user_tokens WHERE token = ?");
$stmt->execute([$token]);

respond(200, ['ok' => true, 'message' => 'Logout berhasil.']);
