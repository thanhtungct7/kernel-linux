#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>

void list_processes() {
    system("ps -ax");
}

void signal_process() {
    pid_t pid;
    int sig;
    scanf("%d", &pid);
    scanf("%d", &sig);
    if (kill(pid, sig) == -1) {
        perror("Error sending signal");
    } else {
        printf("Signal sent to process %d\n", pid);
    }
}

int main() {
    int choice;
    while (1) {
        scanf("%d", &choice);
        switch (choice) {
            case 1:
                list_processes();
                break;
            case 2:
                signal_process();
                break;
            case 3:
                exit(0);
            default:
                printf("Invalid choice\n");
        }
    }
    return 0;
}
