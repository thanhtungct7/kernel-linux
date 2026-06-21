#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <sys/stat.h>
#include <errno.h>

// Định nghĩa loại tin nhắn
#define MSG_TYPE_CHAT 1
#define MSG_TYPE_FILE 2
#define FILE_CHUNK_SIZE 1024

char ip_server[256] = "127.0.0.1"; // Nhập ip server vào đây

// Định nghĩa cấu trúc gói tin
struct MessagePacket {
    int type;           // Loại tin nhắn (1: chat, 2: file)
    char sender[100];   // Người gửi
    char content[1024]; // Nội dung tin nhắn hoặc chunk file
    int bytes_read;
    char filename[256]; // Tên file (nếu gửi file)
    int filesize;       // Kích thước file (nếu gửi file)
    int chunk_id;       // ID của chunk (nếu gửi file)
    int total_chunks;   // Tổng số chunk (nếu gửi file)
};

// Cấu trúc toàn cục để lưu file đang nhận
typedef struct {
    char filename[256];
    char sender[100];
    FILE* file;
    int received_chunks;
    int total_chunks;
    int active;
} ReceivedFile;

ReceivedFile current_files[10];
int file_count = 0;
pthread_mutex_t file_mutex = PTHREAD_MUTEX_INITIALIZER;

// Hàm nhận tin nhắn từ server
void* recvMsg(void* sock)
{
    int their_sock = *((int*)sock);
    struct MessagePacket packet;
    
    // Tạo thư mục để lưu file nhận được
    mkdir("received_files", 0777);
    
    while (recv(their_sock, &packet, sizeof(packet), MSG_WAITALL) > 0) 
    {
        if (packet.type == MSG_TYPE_CHAT) {
            // Xử lý tin nhắn chat
            printf("%s: %s", packet.sender, packet.content);
        } 
        else if (packet.type == MSG_TYPE_FILE) {
            // Xử lý nhận file
            pthread_mutex_lock(&file_mutex);
            
            // Tìm file trong danh sách nếu đã tồn tại
            int file_index = -1;
            for (int i = 0; i < file_count; i++) {
                if (current_files[i].active && 
                    strcmp(current_files[i].filename, packet.filename) == 0 &&
                    strcmp(current_files[i].sender, packet.sender) == 0) {
                    file_index = i;
                    break;
                }
            }
            
            // Nếu chunk đầu tiên, tạo file mới
            if (packet.chunk_id == 0) {
                // Nếu file_index đã tồn tại, đóng file cũ
                if (file_index >= 0 && current_files[file_index].file) {
                    fclose(current_files[file_index].file);
                } else {
                    // Tìm slot trống hoặc thêm mới vào mảng
                    file_index = -1;
                    for (int i = 0; i < file_count; i++) {
                        if (!current_files[i].active) {
                            file_index = i;
                            break;
                        }
                    }
                    
                    if (file_index == -1) {
                        file_index = file_count++;
                    }
                }
                
                // Khởi tạo thông tin file mới
                char filepath[512];
                sprintf(filepath, "received_files/%s", packet.filename);
                current_files[file_index].file = fopen(filepath, "wb");
                if (current_files[file_index].file == NULL) {
                    printf("\n[LỖI NGHIÊM TRỌNG]: Không thể tạo file '%s'!\n", filepath);
                    printf("[LÝ DO]: %s\n", strerror(errno));
                    continue; // Bỏ qua khối dữ liệu này
                }
                strcpy(current_files[file_index].filename, packet.filename);
                strcpy(current_files[file_index].sender, packet.sender);
                current_files[file_index].received_chunks = 0;
                current_files[file_index].total_chunks = packet.total_chunks;
                current_files[file_index].active = 1;
                
                printf("\nĐang nhận file '%s' từ %s (%d bytes)...\n", 
                       packet.filename, packet.sender, packet.filesize);
            }
            
            // Ghi chunk vào file
            if (file_index >= 0 && current_files[file_index].file) {
                fwrite(packet.content, 1, packet.bytes_read, current_files[file_index].file);
                current_files[file_index].received_chunks++;
                
                // Nếu đã nhận đủ chunks, đóng file
                if (current_files[file_index].received_chunks >= current_files[file_index].total_chunks) {
                    fclose(current_files[file_index].file);
                    current_files[file_index].file = NULL;
                    current_files[file_index].active = 0;
                    
                    printf("\nĐã nhận file hoàn tất: %s từ %s\n", 
                           current_files[file_index].filename, current_files[file_index].sender);
                }
            }
            
            pthread_mutex_unlock(&file_mutex);
        }
    }
    
    return NULL;
}

void sendFile(int sock, char* username, char* filepath) {

    FILE* file = fopen(filepath, "rb");
    if (!file) {
        printf("[LỖI]: Khong the mo file! He thong bao loi: %s\n", strerror(errno));
        printf("[GỢI Ý]: Co the sai duong dan hoac thieu quyen doc file.\n");
        return;
    }
    
    // Lấy kích thước file
    fseek(file, 0, SEEK_END);
    long filesize = ftell(file);
    fseek(file, 0, SEEK_SET);
    
    // Tính toán số chunk
    int total_chunks = (filesize + FILE_CHUNK_SIZE - 1) / FILE_CHUNK_SIZE;
    if (total_chunks == 0) total_chunks = 1; // Neu file 0 byte thi van tinh la 1 chunk
    
    // Lấy tên file (không có đường dẫn)
    char* filename = strrchr(filepath, '/');
    if (filename) {
        filename++;  // Bỏ qua dấu '/'
    } else {
        filename = filepath;
    }
    
    printf("Dang gui file '%s' (%ld bytes, %d chunks)\n", filename, filesize, total_chunks);
    
    // Gửi file theo từng chunk
    char buffer[FILE_CHUNK_SIZE];
    struct MessagePacket packet;
    int chunk_id = 0;
    
    while (!feof(file)) {
        memset(buffer, 0, FILE_CHUNK_SIZE);
        size_t bytes_read = fread(buffer, 1, FILE_CHUNK_SIZE, file);
        
        if (bytes_read <= 0 && chunk_id > 0) break; // Dung lai neu da het file
        
        // Chuẩn bị gói tin
        packet.type = MSG_TYPE_FILE;
        strcpy(packet.sender, username);
        
        // Dung memcpy de copy du lieu tho chu khong dung strcpy
        memset(packet.content, 0, sizeof(packet.content));
        memcpy(packet.content, buffer, bytes_read);
        packet.bytes_read = bytes_read; // Truyen thong tin so byte doc duoc
        
        // Copy ten file vao goi tin công khai
        memset(packet.filename, 0, sizeof(packet.filename));
        strcpy(packet.filename, filename);
        
        packet.filesize = filesize;
        packet.chunk_id = chunk_id++;
        packet.total_chunks = total_chunks;
        
        // Gửi gói tin
        send(sock, &packet, sizeof(packet), 0);
        
        usleep(10000);  // 10ms
        if (bytes_read < FILE_CHUNK_SIZE) break; // Doc xong chunk cuoi thi thoat
    }
    
    fclose(file);
    printf("Da gui file thanh cong!\n");
}

void showMenu() {
    printf("\n==== MENU ====\n");
    printf("1. Chat bình thường\n");
    printf("2. Gửi file\n");
    printf("0. Thoát\n");
    printf("Lựa chọn của bạn: ");
}

int main(int argc, char* argv[])
{
    struct sockaddr_in their_addr;
    pthread_t sendt, recvt;
    int my_sock;
    int portno;
    char username[100];
    char ip[INET_ADDRSTRLEN];
    
    if (argc < 3) 
    {
        printf("Sử dụng: %s <username> <port> [ip_server]\n", argv[0]);
        exit(1);
    }
    
    portno = atoi(argv[2]);
    strcpy(username, argv[1]);
    
    if (argc >= 4) {
        strncpy(ip_server, argv[3], sizeof(ip_server) - 1);
    }
    
    my_sock = socket(AF_INET, SOCK_STREAM, 0);
    if (my_sock < 0)
    {
        perror("Mở kênh không thành công...");
        exit(1);
    }
    
    memset(their_addr.sin_zero, '\0', sizeof(their_addr.sin_zero));
    their_addr.sin_family = AF_INET;
    their_addr.sin_port = htons(portno);
    their_addr.sin_addr.s_addr = inet_addr(ip_server);  // Sửa IP theo server của bạn
    
    if (connect(my_sock, (struct sockaddr*) &their_addr, sizeof(their_addr)) < 0)
    {
        perror("Kết nối không thành công...");
        exit(1);
    }
    
    inet_ntop(AF_INET, (struct sockaddr*) &their_addr, ip, INET_ADDRSTRLEN);
    printf("Đã kết nối tới %s, bắt đầu trò chuyện\n", ip);
    
    // Tạo thread để nhận tin nhắn
    pthread_create(&recvt, NULL, recvMsg, &my_sock);

    int choice;
    char input[1024];
    struct MessagePacket packet;
    
    while (1) {
        showMenu();
        
        // 1. Dùng scanf để đọc số lựa chọn của Menu
        if (scanf("%d", &choice) != 1) {
            // Nếu người dùng nhập chữ thay vì số, xóa bộ đệm rồi bỏ qua
            int c; while ((c = getchar()) != '\n' && c != EOF);
            continue;
        }
        
        // 2. XÓA NGAY KÝ TỰ ENTER THỪA SAU KHI NHẬP SỐ CHỌN MENU
        int c;
        while ((c = getchar()) != '\n' && c != EOF); 
        
        if (choice == 0) {
            break;  // Thoát
        }
        else if (choice == 1) {
            // Chế độ chat
            printf("Chế độ chat. Nhập tin nhắn (gõ 'menu' để quay lại menu):\n");
            while (1) {
                memset(input, 0, sizeof(input));
                fgets(input, sizeof(input), stdin);
                if (strcmp(input, "menu\n") == 0) {
                    break;
                }
                
                packet.type = MSG_TYPE_CHAT;
                strcpy(packet.sender, username);
                strcpy(packet.content, input);
                send(my_sock, &packet, sizeof(packet), 0);
            }
        }
        else if (choice == 2) {
            // Chế độ gửi file
            printf("Chế độ gửi file. Nhập đường dẫn đầy đủ đến file (hoặc 'menu' để quay lại):\n");
            
            memset(input, 0, sizeof(input));
            fgets(input, sizeof(input), stdin);
            input[strcspn(input, "\n")] = 0;  // Loại bỏ ký tự newline
            
            if (strcmp(input, "menu") == 0) {
                continue;
            }
            
            // Gửi file
            sendFile(my_sock, username, input);
        }
    }
    
    pthread_cancel(recvt);
    close(my_sock);
    return 0;
}
