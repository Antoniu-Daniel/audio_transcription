#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define PORT 8080
#define MAX_FILE_SIZE 1048576

void send_file(int sock, const char* content, size_t content_size) {
    // Send size first
    write(sock, &content_size, sizeof(size_t));
    
    // Send content
    write(sock, content, content_size);
}

char* receive_response(int sock, size_t* response_size) {
    char* response = malloc(MAX_FILE_SIZE);
    if (!response) return NULL;
    
    // Receive size first
    read(sock, response_size, sizeof(size_t));
    
    // Receive content
    read(sock, response, *response_size);
    response[*response_size] = '\0';
    
    return response;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <input_file>\n", argv[0]);
        return 1;
    }
    
    // Read input file
    FILE* fp = fopen(argv[1], "r");
    if (!fp) {
        perror("File opening failed");
        return 1;
    }
    
    // Get file size
    fseek(fp, 0, SEEK_END);
    size_t file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    // Read file content
    char* file_content = malloc(file_size + 1);
    fread(file_content, 1, file_size, fp);
    file_content[file_size] = '\0';
    fclose(fp);
    
    // Create socket
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("Socket creation failed");
        free(file_content);
        return 1;
    }
    
    struct sockaddr_in serv_addr;
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
    
    if (inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr) <= 0) {
        perror("Invalid address");
        free(file_content);
        return 1;
    }
    
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        perror("Connection failed");
        free(file_content);
        return 1;
    }
    
    // Send file to server
    send_file(sock, file_content, file_size);
    free(file_content);
    
    // Receive response
    size_t response_size;
    char* response = receive_response(sock, &response_size);
    
    if (response) {
        printf("Server response:\n%s\n", response);
        free(response);
    }
    
    close(sock);
    return 0;
}