#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <sys/stat.h>
#include <string.h>
#include <unistd.h>

void display_files(char* dirpath) {
    struct dirent *de;
    DIR *dr = opendir(dirpath);
    if (dr == NULL) {
        perror("Could not open directory");
        return;
    }
    while ((de = readdir(dr)) != NULL) {
        printf("%s\n", de->d_name);
    }
    closedir(dr);
}

void create_file(char* filename) {
    FILE* fp = fopen(filename, "w");
    if (fp == NULL) {
        perror("Error creating file");
        return;
    }
    printf("File created successfully: %s\n", filename);
    fclose(fp);
}

void delete_file(char* filename) {
    if (remove(filename) == 0) {
        printf("File deleted successfully\n");
    } else {
        perror("Error deleting file");
    }
}

void display_file_content(char* filename) {
    FILE* fp = fopen(filename, "r");
    if (fp == NULL) {
        perror("Error opening file");
        return;
    }
    char ch;
    printf("Contents of file:\n");
    while ((ch = fgetc(fp)) != EOF) {
        printf("%c", ch);
    }
    fclose(fp);
}

/* case 6 – tạo thư mục bằng mkdir() */
void create_dir(char* dirname) {
    if (mkdir(dirname, 0755) == 0) {
        printf("Directory created successfully: %s\n", dirname);
    } else {
        perror("Error creating directory");
    }
}

/* case 7 – đổi tên / di chuyển bằng rename() */
void rename_item(char* oldpath, char* newpath) {
    if (rename(oldpath, newpath) == 0) {
        printf("Renamed successfully: %s -> %s\n", oldpath, newpath);
    } else {
        perror("Error renaming");
    }
}

/* case 8 – xóa tạm: di chuyển vào trash_dir/.trash */
void move_to_trash(char* filepath, char* trash_dir) {
    mkdir(trash_dir, 0755);

    const char* base = strrchr(filepath, '/');
    base = base ? base + 1 : filepath;

    char dest[1024];
    snprintf(dest, sizeof(dest), "%s/%s", trash_dir, base);

    if (rename(filepath, dest) == 0) {
        printf("Moved to trash: %s\n", dest);
    } else {
        perror("Error moving to trash");
    }
}

/* case 9 – xóa vĩnh viễn: unlink() cho file, rmdir() cho thư mục */
void delete_permanent(char* path) {
    if (unlink(path) == 0) {
        printf("File deleted permanently: %s\n", path);
    } else if (rmdir(path) == 0) {
        printf("Directory deleted permanently: %s\n", path);
    } else {
        perror("Error deleting permanently");
    }
}

int main() {
    int choice;
    char arg1[1024];
    char arg2[1024];

    while (1) {
        if (scanf("%d", &choice) != 1) break;

        switch (choice) {
            case 1:
                scanf("%1023s", arg1);
                display_files(arg1);
                break;
            case 2:
                scanf("%1023s", arg1);
                create_file(arg1);
                break;
            case 3:
                scanf("%1023s", arg1);
                delete_file(arg1);
                break;
            case 4:
                scanf("%1023s", arg1);
                display_file_content(arg1);
                break;
            case 6:
                scanf("%1023s", arg1);
                create_dir(arg1);
                break;
            case 7:
                scanf("%1023s", arg1);
                scanf("%1023s", arg2);
                rename_item(arg1, arg2);
                break;
            case 8:
                scanf("%1023s", arg1);
                scanf("%1023s", arg2);
                move_to_trash(arg1, arg2);
                break;
            case 9:
                scanf("%1023s", arg1);
                delete_permanent(arg1);
                break;
            case 5:
                exit(0);
            default:
                printf("Invalid choice\n");
        }
    }
    return 0;
}
