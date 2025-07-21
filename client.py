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
    
    # OperationPayLoadSizeの初期化
    operation_payload_size = 0

    if operation == 2:
        # ユーザー名とパスワードを入力
        username = input('Type your name: ')
        password = input('Type your password: ')

        username_bytes = username.encode('utf-8')
        password_bytes = password.encode('utf-8')

        # operation_payload_sizeを計算
        # (ユーザー名の長さを示す１バイト＋ユーザー名自体のバイト数)
        # ＋（パスワードの長さを示す１バイト＋パスワード自体のバイト数）
        # これはルーム名のあとに続くボディ全体のサイズを表す
        operation_payload_size = (1 + len(username_bytes) + (1 + len(password_bytes)))

        header = protocol_header(room_name_size, operation, state, operation_payload_size)
        
        # ヘッダーを送信
        sock.sendall(header)

        # チャットルーム名を送信
        sock.sendall(room_name_bytes)

        # ユーザー名とパスワードを送信
        sock.sendall(len(username_bytes).to_bytes(1, "big") + username_bytes)
        sock.sendall(len(password_bytes).to_bytes(1, "big") + password_bytes)

        try:
            # サーバーからの応答を受信
            response = sock.recv(1024)
            print("Server response:", response.decode('utf-8'))
        except socket.error as e:
            print (f"Error receiving response: {e}")

    elif operation == 1:
        # ユーザー名を入力
        username = input('Type your name: ')
        username_bytes = username.encode('utf-8')

        # operatin_payload_sizeのサイズを計算
        operation_payload_size = 1 + len(username_bytes)

        header = protocol_header(room_name_size, operation, state, operation_payload_size)
        
        # ヘッダーを送信
        sock.sendall(header)

        # チャットルーム名を送信
        sock.sendall(room_name_bytes)

        # ユーザー名を送信
        # ユーザー名の前にその長さを１バイトで付加
        sock.sendall(len(username_bytes).to_bytes(1, "big") + username_bytes)

        try:
            response = sock.recv(1024)
            print("Server response:", response.decode('utf-8'))
        except socket.error as e:
            print(f"Error receiving response: {e}")

    else :
        # sokketを閉じる
        sock.close()

if __name__ == "__main__":
    main()
