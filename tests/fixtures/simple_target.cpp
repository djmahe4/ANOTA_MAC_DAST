#include <iostream>
#include <string>
#include <unistd.h>

// A specific function we want to trace
void target_function(const char* message) {
    std::cout << "Target function called with: " << message << std::endl;
}

int main(int argc, char** argv) {
    std::string msg = "Hello from C++";
    if (argc > 1) {
        msg = argv[1];
    }
    
    std::cout << "Process PID: " << getpid() << std::endl;
    
    // Wait a bit for the monitor to attach
    sleep(1);
    
    target_function(msg.c_str());
    
    return 0;
}
