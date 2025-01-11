#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>

#define PORT 8080
#define BUFFER_SIZE 1024

void handle_client(int client_socket) {
    char buffer[BUFFER_SIZE];
    char response[] = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello from C server!";
    
    // Read client request
    read(client_socket, buffer, BUFFER_SIZE);
    printf("Received request:\n%s\n", buffer);
    
    // Send response
    write(client_socket, response, strlen(response));
    
    // Close client socket
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
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt))) {
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