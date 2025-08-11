import socket
import sys 
import os
import json
from udp_chatroom import ChatRoom 

# サーバーに送信されるプロトコルヘッダーを定義
def protocol_header_tcp(room_name_size,operation,state,operation_payload_size):
    return (room_name_size.to_bytes(1, "big") +
            operation.to_bytes(1, "big") +
            state.to_bytes(1, "big") +
            operation_payload_size.to_bytes(29, "big"))

def protocol_header_udp(room_name_size, usernametoken_size):
    return (room_name_size.to_bytes(1, "big") +
            usernametoken_size.to_bytes(1, "big"))

# UDPメッセージのプロトコルヘッダー
def protocol_header_udp_message(username_bytes,message_bytes):
    username_size = len(username_bytes)
    message_size = len(message_bytes)
    return (username_size).to_bytes(1,'big') + (message_size).to_bytes(4,'big')

def tcp_connect():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # サーバーのアドレスとポートを指定
    server_address = input("Type in the server's address to connect to: ")
    server_port = 9001

    print('connecting to {} port {}'.format(server_address, server_port))
    
    sock.connect((server_address, server_port))

    room_name = input('Type the chat room name: ')
    # ルーム名をUTF-8でエンコードしバイト数を取得
    room_name_bytes = room_name.encode('utf-8')
    room_name_size = len(room_name_bytes)

    # ルーム名の最大バイト数のチェック
    if room_name_size > 255:
        print("Room name exceeds 255 bytes limit.")
        sock.close()
        sys.exit(1)
    
    operation = int(input('Choose operation (1: Create, 2: Join): '))
    state = int(input('Choose state (0: Initial, 1: Response, 2: Complete): '))
    
    username = input('Type your name: ')
    username_bytes = username.encode('utf-8')

    # OperationPayLoadSizeの初期化
    operation_payload = b''

    if operation == 2:
        # パスワードを入力
        password = input('Type your password: ')
        password_bytes = password.encode('utf-8')

        # operation_payload_sizeを計算
        # (ユーザー名の長さを示す１バイト＋ユーザー名自体のバイト数)
        # ＋（パスワードの長さを示す１バイト＋パスワード自体のバイト数）
        # これはルーム名のあとに続くボディ全体のサイズを表す
        operation_payload = (len(username_bytes).to_bytes(1,"big") + username_bytes +len(password_bytes).to_bytes(1,"big") + password_bytes)

    elif operation == 1:
        operation_payload = (len(username_bytes).to_bytes(1,"big") + username_bytes)
    
    else:
        print("Invalid operation chosen.")
        sock.close()
        return (None,None,None,None,None)
    
    operation_payload_size = len(operation_payload)

    header = protocol_header_tcp(room_name_size, operation, state, operation_payload_size)
        
    try:
        sock.sendall(header)
        sock.sendall(operation_payload)
        sock.sendall(room_name_bytes)

        response_len_bytes = sock.recv(4)
        if not response_len_bytes:
            raise socket.error("Server disconnected or sent no response length.")
        response_len = int.from_bytes(response_len_bytes,"big")
        response_bytes = sock.recv(response_len)
        response_data = json.loads(response_bytes.decode('utf-8'))
        print("Server response:", response_data)
        return (server_address, server_port, username, room_name, response_data)
    except socket.error as e:
        print(f"Error during TCP communication: {e}")
        return (server_address, server_port, username, room_name, None)
    except json.JSONDecodeError as e:
        print("Error decoding JSON response from server: {e}")
        return (server_address, server_port, username, room_name, None)
    finally:
        sock.close()
    
def udp_connect(server_address, server_port, username,room_name, usernametoken):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if not all([server_address, server_port, username, room_name, usernametoken]):
        print("Invalid connection parameters for UDP chat. Aborting.")
        return
    
    print('connecting to room : {}'.format(room_name))

    chat_instance = ChatRoom()
    chat_instance.enter_room(sock, server_address, server_port, username, room_name, usernametoken)


def main():
    server_address, server_port, username, room_name, response_data = tcp_connect()
    if response_data is None:
        print("Failed to connect to the server or retrieve response data.")
        sys.exit(1)
        
    usernametoken = response_data.get('usernametoken', None)

    if response_data.get('status') == 'success' and response_data.get('password'):
        print(f"Your room password is : {response_data['password']}")

    udp_connect(server_address, server_port, username, room_name, usernametoken)


if __name__ == "__main__":
    main()
