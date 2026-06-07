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
$mock_params_json = getenv('ANOTA_REQUEST_PARAMS');
if ($mock_params_json) {
    $mock_params = json_decode($mock_params_json, true);
    if ($mock_params) {
        // Merge into globals
        $_GET = array_merge($_GET, $mock_params);
        $_POST = array_merge($_POST, $mock_params);
        $_REQUEST = array_merge($_REQUEST, $mock_params);
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
