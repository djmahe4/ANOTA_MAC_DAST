<?php
/**
 * MAC-DAST Xdebug Instrumentation Helper
 * 
 * CORE RESPONSIBILITY: GROUND TRUTH TELEMETRY & LOGIC STUBBING
 */

// 0. Environment Hardening
ini_set('display_errors', '0');
ini_set('log_errors', '1');
error_reporting(E_ALL & ~E_DEPRECATED & ~E_STRICT);

// Disable mysqli exceptions
if (function_exists('mysqli_report')) {
    mysqli_report(MYSQLI_REPORT_OFF);
}

// 1. Universal Database Stubs (Target-Agnostic)
// These allow the application to "boot" without a physical database.

// A. mysqli Stub (if extension missing or failed)
if (!function_exists('mysqli_connect')) {
    function mysqli_connect($h=null, $u=null, $p=null, $db=null, $port=null) {
        $mock = new stdClass();
        $mock->connect_error = null;
        return $mock;
    }
    function mysqli_query($link, $query) {
        return true;
    }
    function mysqli_error($link) {
        return "Mocked DB Error";
    }
    function mysqli_real_escape_string($link, $str) {
        return addslashes($str);
    }
    function mysqli_report($mode) {}
}

if (!class_exists('mysqli', false)) {
    class mysqli {
        public $connect_error = null;
        public $connect_errno = 0;
        public $errno = 0;
        public $error = "";
        public function __construct($h=null, $u=null, $p=null, $d=null, $port=null) {}
        public function query($q) { return new mysqli_result(); }
        public function select_db($d) { return true; }
        public function close() { return true; }
        public function set_charset($c) { return true; }
        public function real_escape_string($s) { return addslashes($s); }
        public function prepare($q) { return new mysqli_stmt(); }
    }
    class mysqli_result {
        public $num_rows = 1;
        public function fetch_assoc() { return ["id" => "1", "username" => "admin", "password" => "5f4dcc3b5aa765d61d8327deb882cf99"]; } 
        public function fetch_array() { return ["1", "admin", "5f4dcc3b5aa765d61d8327deb882cf99"]; }
        public function free() {}
    }
    class mysqli_stmt {
        public function bind_param($t, ...$v) { return true; }
        public function execute() { return true; }
        public function get_result() { return new mysqli_result(); }
        public function close() {}
    }
}

// B. PDO Stub (Minimal)
if (!class_exists('PDO', false)) {
    class PDO {
        public function __construct($dsn, $u=null, $p=null, $o=null) {}
        public function prepare($q) { return new PDOStatement(); }
        public function query($q) { return new PDOStatement(); }
        public function exec($q) { return 1; }
        public function setAttribute($a, $v) {}
    }
    class PDOStatement {
        public function execute($p=null) { return true; }
        public function fetch($m=null) { return ["id" => "1", "user" => "admin"]; }
        public function fetchAll($m=null) { return [["id" => "1", "user" => "admin"]]; }
        public function bindValue($p, $v, $t=null) {}
        public function rowCount() { return 1; }
    }
}

if (!function_exists('xdebug_start_code_coverage')) {
    return;
}

// 2. Dynamic State Reconstruction
function anota_init() {
    $params_json = $_SERVER['HTTP_X_ANOTA_REQUEST_PARAMS'] ?? getenv('ANOTA_REQUEST_PARAMS');
    if ($params_json) {
        $data = json_decode($params_json, true);
        if ($data) {
            // Handle ENV
            if (isset($data['ENV'])) {
                foreach ($data['ENV'] as $k => $v) {
                    putenv("$k=$v");
                    $_ENV[$k] = $v;
                    if (in_array(strtolower($k), ['security', 'debug'])) {
                        $_COOKIE[$k] = $v;
                    }
                }
            }
            // Handle GLOBALS (Deep injection)
            if (isset($data['GLOBALS'])) {
                foreach ($data['GLOBALS'] as $k => $v) {
                    if (is_array($v) && isset($GLOBALS[$k]) && is_array($GLOBALS[$k])) {
                        $GLOBALS[$k] = array_replace_recursive($GLOBALS[$k], $v);
                    } else {
                        $GLOBALS[$k] = $v;
                    }
                }
            }
            // Handle HTTP Method & Params
            if (isset($data['GET'])) $_GET = array_merge($_GET, $data['GET']);
            if (isset($data['POST'])) {
                $_POST = array_merge($_POST, $data['POST']);
                $_SERVER['REQUEST_METHOD'] = 'POST';
            }
            if (isset($data['COOKIE'])) {
                $_COOKIE = array_merge($_COOKIE, $data['COOKIE']);
                if (isset($_COOKIE['PHPSESSID'])) session_id($_COOKIE['PHPSESSID']);
            }
            $_REQUEST = array_merge($_REQUEST, $_GET, $_POST);
        }
    }
}

anota_init();

// 3. Start Instrumentation
xdebug_start_code_coverage(XDEBUG_CC_UNUSED | XDEBUG_CC_DEAD_CODE);

// 4. Final Context Capture on Shutdown
register_shutdown_function(function() {
    $coverage = xdebug_get_code_coverage();
    xdebug_stop_code_coverage();
    
    $telemetry = [
        "type" => "telemetry",
        "coverage" => $coverage,
        "state" => [
            "session" => (session_status() === PHP_SESSION_ACTIVE) ? $_SESSION : [],
            "cookies" => $_COOKIE,
            "get" => $_GET,
            "post" => $_POST,
            "server" => $_SERVER,
            "headers_out" => headers_list()
        ]
    ];

    $target = $_SERVER['HTTP_X_ANOTA_TELEMETRY_TARGET'] ?? getenv("ANOTA_TELEMETRY_TARGET");
    
    if ($target && $target !== "stdout") {
        file_put_contents($target, json_encode($telemetry), LOCK_EX);
        chmod($target, 0666);
    }
});
?>
