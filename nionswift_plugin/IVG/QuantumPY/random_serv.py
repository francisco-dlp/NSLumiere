import socket
import numpy as np
import threading
import time
import json

# Function to generate a random NumPy array
def generate_random_array(shape):
    return (100.0*np.random.rand(*shape)).astype('uint32').tobytes()

class ConfigBytes():
    def __init__(self, data: bytes):
        self.binning = bool(data[0])

        if data[1] == 0:
            self.__bytedepth = 1
        elif data[1] == 1:
            self.__bytedepth = 2
        elif data[1] == 2:
            self.__bytedepth = 4
        elif data[1] == 4:
            self.__bytedepth = 8
        else:
            raise ValueError

        self.__cumul = bool(data[2])

    def get_integer(self, value: bytes, start_index: int, end_index: int):
        return int.from_bytes(bytes[start_index:end_index], "little")

    def create_header(self) -> bytes:
        timeatframe = 0
        frameNumber = 0
        bitDepth = 32
        if self.binning:
            data_size = 1025 * 4
            width = 1025
            height = 1
        else:
            data_size = 1025 * 4 * 256
            width = 1025
            height = 256


        string = "{{\"timeAtFrame\":{},\"frameNumber\":{},\"measurementID\":Null,\"dataSize\":{},\"bitDepth\":{},\"width\":{},\"height\":{}}}\n"\
            .format(timeatframe, frameNumber, data_size, bitDepth, width, height)

        return string.encode()

# Function to handle client connections
def client_handler(client_socket):
    bytes_config = client_socket.recv(512)
    config = ConfigBytes(bytes_config)

    try:
        while True:
            # Generate a random NumPy array
            if config.binning:
                data = generate_random_array((1025,))
            else:
                data = generate_random_array((1025, 256,))


            # Send the JSON data to the client
            header = config.create_header()
            client_socket.send(header)
            client_socket.send(data)

            # Simulate some delay
            #time.sleep(0.01)

    except KeyboardInterrupt:
        print("Server shutting down...")
        client_socket.close()
    except Exception as e:
        print(f"Error: {str(e)}")
        client_socket.close()
    finally:
        client_socket.close()

# Create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to a specific address and port
server_address = ('localhost', 8088)
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen(5)
print(f"Server listening on {server_address[0]}:{server_address[1]}")

try:
    while True:
        # Accept a client connection
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address[0]}:{client_address[1]}")

        # Create a thread to handle the client
        #client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        #client_thread.start()
        client_handler(client_socket)
except KeyboardInterrupt:
    print("Server shutting down...")
finally:
    server_socket.close()
