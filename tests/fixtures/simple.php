<?php
// tests/fixtures/simple.php
function greet($name) {
    if ($name) {
        echo "Hello, " . $name;
    } else {
        echo "Hello, Guest";
    }
}

greet("World");
?>
