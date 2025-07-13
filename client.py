import socket
import sys 
import os

# サーバーに送信されるプロトコルヘッダーを定義
def protocol_header(room_name_size,operation,state,operation_payload_size):
    return (room_name_size.to_bytes(1, "big") +
            operation.to_bytes(1, "big") +
            state.to_bytes(1, "big") +
            operation_payload_size.to_bytes(29, "big"))

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # サーバーのアドレスとポートを指定
    server_address = input("Type in the server's address to connect to: ")
    server_port = 9001

    print('connecting to {} port {}'.format(server_address, server_port))
    
    sock.connect((server_address, server_port))

    room_name = input('Type the chat room name: ')
    operation = int(input('Choose operation (1: Create, 2: Join): '))
    state = int(input('Choose state (0: Initial, 1: Response, 2: Complete): '))
    
    if operation == 2:
        # ユーザー名とパスワードを入力
        username = input('Type your name: ')
        password = input('Type your password: ')

        # ヘッダーのサイズを計算
        room_name_size = len(room_name.encode('utf-8'))
        operation_payload_size = len(username.encode('utf-8')) + 2  # +2 for lengths

        header = protocol_header(room_name_size, operation, state, operation_payload_size)
        
        # ヘッダーを送信
        sock.sendall(header)

        # チャットルーム名を送信
        sock.sendall(room_name.encode('utf-8'))

        # ユーザー名とパスワードを送信
        username_bytes = username.encode('utf-8')
        password_bytes = password.encode('utf-8')
        
        sock.sendall(len(username_bytes).to_bytes(1, "big") + username_bytes)
        sock.sendall(len(password_bytes).to_bytes(1, "big") + password_bytes)

        response = sock.recv(1024)
        print("Server response:", response.decode('utf-8'))

    elif operation == 1:
        # ユーザー名を入力
        username = input('Type your name: ')

        # ヘッダーのサイズを計算
        room_name_size = len(room_name.encode('utf-8'))
        operation_payload_size = len(username.encode('utf-8'))

        header = protocol_header(room_name_size, operation, state, operation_payload_size)
        
        # ヘッダーを送信
        sock.sendall(header)

        # チャットルーム名を送信
        sock.sendall(room_name.encode('utf-8'))

        # ユーザー名を送信
        username_bytes = username.encode('utf-8')
        
        sock.sendall(len(username_bytes).to_bytes(1, "big") + username_bytes)

        response = sock.recv(1024)
        print("Server response:", response.decode('utf-8'))

if __name__ == "__main__":
    main()
