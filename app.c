#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <ctype.h>

#define PORT 8080
#define BUFFER_SIZE 4096
#define MAX_FILE_SIZE 1048576

// Your custom processing function - Replace this with your own logic
char* process_request(const char* input, size_t input_len, size_t* output_len) {
    // Example processing (converts to uppercase)
    char* result = malloc(input_len + 1);
    if (!result) return NULL;
    
    for (size_t i = 0; i < input_len; i++) {
        result[i] = toupper(input[i]);
    }
    result[input_len] = '\0';
    *output_len = input_len;
    
    return result;
}

// Extract the POST data from HTTP request
char* get_post_data(const char* request, size_t* data_len) {
    const char* body = strstr(request, "\r\n\r\n");
    if (!body) return NULL;
    
    body += 4;  // Skip \r\n\r\n
    *data_len = strlen(body);
    
    char* data = malloc(*data_len + 1);
    if (!data) return NULL;
    
    strcpy(data, body);
    return data;
}

// Send HTTP response with headers and content
void send_http_response(int client_socket, const char* content, size_t content_len) {
    char header[512];
    snprintf(header, sizeof(header),
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: %zu\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "\r\n", content_len);
    
    write(client_socket, header, strlen(header));
    write(client_socket, content, content_len);
}

// Handle CORS preflight requests
void handle_options(int client_socket) {
    const char* response =
        "HTTP/1.1 200 OK\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Content-Length: 0\r\n"
        "\r\n";
    
    write(client_socket, response, strlen(response));
}

// Handle each client connection
void handle_client(int client_socket) {
    char buffer[MAX_FILE_SIZE];
    ssize_t bytes_received = read(client_socket, buffer, MAX_FILE_SIZE - 1);
    
    if (bytes_received <= 0) {
        close(client_socket);
        return;
    }
    
    buffer[bytes_received] = '\0';
    
    // Handle CORS preflight request
    if (strncmp(buffer, "OPTIONS", 7) == 0) {
        handle_options(client_socket);
        close(client_socket);
        return;
    }
    
    // Verify POST method
    if (strncmp(buffer, "POST", 4) != 0) {
        const char* error = "Only POST method is supported";
        send_http_response(client_socket, error, strlen(error));
        close(client_socket);
        return;
    }
    
    // Get POST data
    size_t data_len;
    char* data = get_post_data(buffer, &data_len);
    
    if (!data) {
        const char* error = "Error parsing request";
        send_http_response(client_socket, error, strlen(error));
        close(client_socket);
        return;
    }
    
    // Process the request using custom function
    size_t response_len;
    char* response = process_request(data, data_len, &response_len);
    
    if (!response) {
        const char* error = "Error processing request";
        send_http_response(client_socket, error, strlen(error));
        free(data);
        close(client_socket);
        return;
    }
    
    // Send response
    send_http_response(client_socket, response, response_len);
    
    // Clean up
    free(data);
    free(response);
    close(client_socket);
}

int main() {
    int server_fd, client_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);
    
    // Create socket
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
    
    // Configure server address
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);
    
    // Bind socket
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("Bind failed");
        exit(EXIT_FAILURE);
    }
    
    // Listen for connections
    if (listen(server_fd, 3) < 0) {
        perror("Listen failed");
        exit(EXIT_FAILURE);
    }
    
    printf("Server listening on port %d...\n", PORT);
    
    // Main server loop
    while(1) {
        if ((client_socket = accept(server_fd, (struct sockaddr *)&address, 
                                  (socklen_t*)&addrlen)) < 0) {
            perror("Accept failed");
            continue;
        }
        
        handle_client(client_socket);
    }
    
    return 0;
}