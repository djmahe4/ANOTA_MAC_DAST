#include <stdio.h>
#include <unistd.h>

void secret_logic(const char* data) {
    printf("Logic called with: %s\n", data);
}

int main() {
    printf("Test program started. PID: %d\n", getpid());
    while(1) {
        secret_logic("sensitive_query_123");
        sleep(2);
    }
    return 0;
}
