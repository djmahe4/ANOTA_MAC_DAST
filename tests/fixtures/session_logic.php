<?php
// tests/fixtures/session_logic.php
session_start();

if (!isset($_SESSION['step'])) {
    $_SESSION['step'] = 1;
    echo "Step 1 initiated";
} else {
    $_SESSION['step']++;
    echo "Advanced to step " . $_SESSION['step'];
}

setcookie("last_action", "increment", time() + 3600);
?>
