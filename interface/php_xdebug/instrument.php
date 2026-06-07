<?php
/**
 * MAC-DAST Xdebug Instrumentation Helper
 * 
 * This file is intended to be auto-prepended to PHP executions to capture
 * code coverage, session state, and request context.
 */

if (!function_exists('xdebug_start_code_coverage')) {
    fwrite(STDERR, "Error: Xdebug extension not loaded. Coverage will not be collected.\n");
    return;
}

/**
 * MAC-DAST: Mock request data if provided via environment
 */
// Set realistic web defaults for CLI execution
if (!isset($_SERVER['HTTP_HOST'])) $_SERVER['HTTP_HOST'] = 'localhost';
if (!isset($_SERVER['SERVER_NAME'])) $_SERVER['SERVER_NAME'] = 'localhost';
if (!isset($_SERVER['REMOTE_ADDR'])) $_SERVER['REMOTE_ADDR'] = '127.0.0.1';
if (!isset($_SERVER['REQUEST_URI'])) $_SERVER['REQUEST_URI'] = '/';

// Promote specific ENV vars to Cookies (Target compatibility)
if (getenv('security')) {
    $_COOKIE['security'] = getenv('security');
}

// Force Target-Specific Logic Bypasses
$GLOBALS['DBMS'] = 'SQLite';
$GLOBALS['SQLI_DB'] = 'sqlite';

// Force Authentication for MAC-DAST analysis
if (!isset($_SESSION)) $_SESSION = [];
if (!isset($_SESSION['dvwa'])) $_SESSION['dvwa'] = [];
$_SESSION['dvwa']['username'] = 'admin';
$_SESSION['dvwa']['logged_in'] = true;

$mock_params_json = getenv('ANOTA_REQUEST_PARAMS');
if ($mock_params_json) {
    $mock_data = json_decode($mock_params_json, true);
    if ($mock_data) {
        // Correctly route GET and POST parameters
        if (isset($mock_data['GET'])) {
            $_GET = array_merge($_GET, $mock_data['GET']);
        }
        if (isset($mock_data['POST'])) {
            $_POST = array_merge($_POST, $mock_data['POST']);
            // Set method to POST if POST data is injected
            $_SERVER['REQUEST_METHOD'] = 'POST';
        }
        $_REQUEST = array_merge($_REQUEST, $_GET, $_POST);
    }
}

xdebug_start_code_coverage(XDEBUG_CC_UNUSED | XDEBUG_CC_DEAD_CODE);

register_shutdown_function(function() {
    $coverage = xdebug_get_code_coverage();
    xdebug_stop_code_coverage();
    
    // Capture Full Context
    $state = [
        "session" => isset($_SESSION) ? $_SESSION : [],
        "cookies" => $_COOKIE,
        "get" => $_GET,
        "post" => $_POST,
        "server" => [
            "REQUEST_METHOD" => $_SERVER["REQUEST_METHOD"] ?? "CLI",
            "REQUEST_URI" => $_SERVER["REQUEST_URI"] ?? "",
            "PHP_SELF" => $_SERVER["PHP_SELF"] ?? ""
        ],
        "headers_out" => headers_list()
    ];

    $telemetry = [
        "type" => "telemetry",
        "coverage" => $coverage,
        "state" => $state
    ];

    // Emit to a file if requested via env, otherwise fallback to stdout with markers
    $target = getenv("ANOTA_TELEMETRY_TARGET");
    if ($target && $target !== "stdout") {
        file_put_contents($target, json_encode($telemetry));
    } else {
        echo "\n---ANOTA_TELEMETRY_START---\n";
        echo json_encode($telemetry);
        echo "\n---ANOTA_TELEMETRY_END---\n";
    }
});
?>
