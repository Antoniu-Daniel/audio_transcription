#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <ctype.h>

#define PORT 8080
#define BUFFER_SIZE 4096
#define MAX_FILE_SIZE 1048576  // 1MB max file size
#define MIN(a,b) ((a) < (b) ? (a) : (b))

// Your custom processing function - replace the contents with your logic
char* process_request(const char* input, size_t input_len, size_t* output_len) {
    // Example: converts text to uppercase
    // Replace this with your actual processing logic
    char* result = malloc(input_len + 1);
    if (!result) return NULL;
    
    for (size_t i = 0; i < input_len; i++) {
        result[i] = toupper(input[i]);
    }
    result[input_len] = '\0';
    *output_len = input_len;
    
    return result;
}

// Receives the complete file from client
char* receive_file(int client_socket, size_t* file_size) {
    char* file_content = malloc(MAX_FILE_SIZE);
    if (!file_content) {
        return NULL;
    }
    
    // First receive the file size
    ssize_t size_read = read(client_socket, file_size, sizeof(size_t));
    if (size_read != sizeof(size_t) || *file_size > MAX_FILE_SIZE) {
        free(file_content);
        return NULL;
    }
    
    // Then receive the file content
    size_t total_bytes = 0;
    while (total_bytes < *file_size) {
        ssize_t bytes_received = read(client_socket, 
                                    file_content + total_bytes,
                                    MIN(BUFFER_SIZE, *file_size - total_bytes));
        
        if (bytes_received <= 0) {
            free(file_content);
            return NULL;
        }
        total_bytes += bytes_received;
    }
    
    file_content[*file_size] = '\0';
    return file_content;
}

// Sends the response file back to client
void send_response(int client_socket, const char* response, size_t response_size) {
    // First send the size
    write(client_socket, &response_size, sizeof(size_t));
    
    // Then send the content in chunks if necessary
    size_t total_sent = 0;
    while (total_sent < response_size) {
        ssize_t sent = write(client_socket, 
                            response + total_sent,
                            MIN(BUFFER_SIZE, response_size - total_sent));
        
        if (sent <= 0) break;
        total_sent += sent;
    }
}

// Handles each client connection
void handle_client(int client_socket) {
    size_t request_size;
    char* request = receive_file(client_socket, &request_size);
    
    if (!request) {
        const char* error = "Error receiving file";
        size_t error_len = strlen(error);
        send_response(client_socket, error, error_len);
        close(client_socket);
        return;
    }
    
    // Process the request
    size_t response_size;
    char* response = process_request(request, request_size, &response_size);
    
    if (!response) {
        const char* error = "Error processing request";
        size_t error_len = strlen(error);
        send_response(client_socket, error, error_len);
        free(request);
        close(client_socket);
        return;
    }
    
    // Send the response
    send_response(client_socket, response, response_size);
    
    // Clean up
    free(request);
    free(response);
    close(client_socket);
}

int main() {
    int server_fd, client_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);
    
    // Create socket file descriptor
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }
    
    // Set socket options
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, 
                   &opt, sizeof(opt))) {
        perror("Setsockopt failed");
        exit(EXIT_FAILURE);
    }
    
    // Setup server address structure
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);
    
    // Bind socket to the specified port
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("Bind failed");
        exit(EXIT_FAILURE);
    }
    
    // Listen for incoming connections
    if (listen(server_fd, 3) < 0) {
        perror("Listen failed");
        exit(EXIT_FAILURE);
    }
    
    printf("Server listening on port %d...\n", PORT);
    
    while(1) {
        // Accept incoming connection
        if ((client_socket = accept(server_fd, (struct sockaddr *)&address, 
                                  (socklen_t*)&addrlen)) < 0) {
            perror("Accept failed");
            continue;
        }
        
        // Handle client connection
        handle_client(client_socket);
    }
    
    return 0;
}