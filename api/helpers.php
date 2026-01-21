<?php

function json_input(): array {
  $raw = file_get_contents('php://input');
  $data = json_decode($raw, true);
  return is_array($data) ? $data : [];
}

function respond(int $code, array $payload): void {
  http_response_code($code);
  header('Content-Type: application/json; charset=utf-8');

  // Jika kamu akses dari domain yang sama (localhost/pln-login), ini tidak wajib.
  // Kalau butuh CORS (misal beda port/domain), uncomment:
  // header('Access-Control-Allow-Origin: http://localhost');
  // header('Access-Control-Allow-Headers: Content-Type, Authorization');
  // header('Access-Control-Allow-Methods: GET, POST, OPTIONS');

  echo json_encode($payload, JSON_UNESCAPED_UNICODE);
  exit;
}

function clean_username(string $u): string {
  return trim($u);
}

function validate_username(string $u): bool {
  // 3-30 karakter: huruf/angka/underscore/dot
  return (bool)preg_match('/^[a-zA-Z0-9_.]{3,30}$/', $u);
}

function validate_password(string $p): bool {
  return strlen($p) >= 6 && strlen($p) <= 72;
}

function bearer_token(): string {
  $hdr = '';

  if (!empty($_SERVER['HTTP_AUTHORIZATION'])) {
    $hdr = $_SERVER['HTTP_AUTHORIZATION'];
  } elseif (!empty($_SERVER['REDIRECT_HTTP_AUTHORIZATION'])) {
    $hdr = $_SERVER['REDIRECT_HTTP_AUTHORIZATION'];
  } elseif (function_exists('getallheaders')) {
    $headers = getallheaders();
    foreach ($headers as $k => $v) {
      if (strtolower($k) === 'authorization') {
        $hdr = $v;
        break;
      }
    }
  }

  if (preg_match('/Bearer\s+(\S+)/i', $hdr, $m)) return $m[1];
  return '';
}
  
