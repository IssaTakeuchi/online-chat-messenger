import socket
import pathlib
import os
import random
import string

# チャットルームを保存する辞書を作成
chatroom = {}

# usernametokenとユーザー名を保存するための辞書
usernametoken_dict = {}

def random_password(): # ランダムなパスワードを生成する関数   
    length = 8  # パスワードの長さ
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def check_password(room_name, password): # チャットルームのパスワードを検証する関数
    if room_name in chatroom:
        if chatroom[room_name]['password'] == password:
            print(f"Password for room '{room_name}' is correct.")
            return True
        else:
            print(f"Incorrect password for room '{room_name}'.")
            return False
    else:
        print(f"Chat room '{room_name}' does not exist.")
        return False


def create_chatroom(room_name,state,username,password):
    # チャットルームが既に存在するか確認
    if room_name in chatroom:
        print(f"Chat room '{room_name}' already exists.")
        return None

    # passwordを設定
    password = random_password()
    # print(f"Generated password for chat room '{room_name}': {password}")

    # サーバの初期化（0）クライアントが新しいチャットルームを作成するリクエストを送信
    if state == 0:
        print(f"Creating chat room: {room_name} with password: {password}")
        # 辞書に新しいチャットルームのエントリを追加
        chatroom[room_name] = {
            'password': password,
            'host': username,  # ホストのユーザー名を保存
            'users': [username] # 初期ユーザーとしてホストのユーザー名を追加
        }
        
        # リクエストの応答（1）サーバーはステータスコードを含むペイロードで即座に応答する
        state = 1
        print(f"Chat room '{room_name}' created successfully.status: {state}")
    
        # リクエストの完了（2）サーバは特定の生成されたユニークなトークンをクライアントに送り、
        # このトークンにユーザー名を割り当てる
        # このトークンはクライアントをチャットルームのホストとして認識する
        # usernametokenを生成
        usernametoken = f"user_{random.randint(1000, 9999)}"

        # usernametokenとユーザー名を紐付ける
        usernametoken_dict[username] = usernametoken
        print(f"User '{username}' has been assigned token '{usernametoken}' in room '{room_name}'.")
        
        chatroom[room_name]['users'].append(usernametoken)
        state = 2
        return {
            'status': 'success',
            'room_name': room_name,
            'usernametoken': usernametoken,
        }

def enter_chatroom(room_name,state,username,password):
    # サーバの初期化（0）クライアントが既存のチャットルームに参加するリクエストを送信
    if state == 0:
        print(f"Joining chat room: {room_name} as user: {username}")
        if room_name in chatroom:
            chatroom[room_name]['users'].append(username)
            print(f"User '{username}' has joined chat room '{room_name}'.")
        else:
            print(f"Chat room '{room_name}' does not exist.")
            return None

        # リクエストの応答（1）サーバーはステータスコードを含むペイロードで即座に応答する
        state = 1
        print(f"Chat room '{room_name}' created successfully.status: {state}")
    
        # リクエストの完了（2）サーバは特定の生成されたユニークなトークンをクライアントに送り、
        # このトークンにユーザー名を割り当てる
        # このトークンはクライアントをチャットルームのホストとして認識する
        # usernametokenを生成
        usernametoken = f"user_{random.randint(1000, 9999)}"

        # usernametokenとユーザー名を紐付ける
        usernametoken_dict[username] = usernametoken
        print(f"User '{username}' has been assigned token '{usernametoken}' in room '{room_name}'.")
        
        chatroom[room_name]['users'].append(usernametoken)
        state = 2
        return {
            'status': 'success',
            'room_name': room_name,
            'usernametoken': usernametoken,
        }

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = '0.0.0.0'
    server_port = 9001

    print(f'Starting up on {server_address} port {server_port}')
    sock.bind((server_address, server_port))
    sock.listen(5)

    while True:
        # accpet() メソッドは、クライアントからの接続を待ち受けます。
        # 接続があると、接続されたソケットとクライアントのアドレスを返します。
        connection, client_address = sock.accept()
        try:
            print('connection from', client_address)
            header = connection.recv(32)
            room_name_size = int.from_bytes(header[0:1], 'big')
            operation = int.from_bytes(header[1:2], 'big')
            state = int.from_bytes(header[2:3], 'big')
            operation_payload_size = int.from_bytes(header[3:32], 'big')

            # ユーザー名を取得 operation_payloadの１バイト目
            operation_payload = connection.recv(operation_payload_size)
            username_length = int.from_bytes(operation_payload[0:1], 'big')
            username_bytes = operation_payload[1:1 + username_length]
            username = username_bytes.decode('utf-8')

            # パスワードを取得 (usernameの後に続く)
            password_offset = 1 + username_length
            password_length = int.from_bytes(operation_payload[password_offset:password_offset+1], 'big')
            password_bytes = operation_payload[password_offset+1: password_offset+1+ password_length]
            password = password_bytes.decode('utf-8')

            room_name = connection.recv(room_name_size).decode('utf-8')

            # response_data = {}

            if operation == 1: # create new chatroom
                print(f"Creating new chat room: {room_name}")

                # operation_payloadをデコード

                # ここで新しいチャットルームを作成するロジックを追加
                # response_data = create_chatroom(room_name,state,username,password)
                create_chatroom(room_name,state,username,password)
                response = f"Chat room '{room_name}' created successfully."
                connection.sendall(response.encode('utf-8'))
                connection.sendall(chatroom[room_name]['password'].encode('utf-8'))

            elif operation == 2: # join  existing chatroom
                print(f"Joining chat room: {room_name}")

                #　operation_payloadをデコード
                # パスワードの検証
                checkpass = check_password(room_name, password)
                if not checkpass:
                    response = f"Failed to join chat room '{room_name}': Incorrect password."
                    connection.sendall(response.encode('utf-8'))
                    continue

                # ここで既存のチャットルームに参加するロジックを追加
                enter_chatroom(room_name,state,username)

                response = f"Joined chat room '{room_name}' successfully."
                connection.sendall(response.encode('utf-8'))

        except Exception as e:
            print(f"Error: {e}")
            response = "An error occurred."
            connection.sendall(response.encode('utf-8'))

        finally:
            connection.close()



if __name__ == "__main__":
    main()

#     ヘッダー（32 バイト）: RoomNameSize（1 バイト） | Operation（1 バイト） | 
#  State（1 バイト） | OperationPayloadSize（29 バイト）
# ボディ: 最初の RoomNameSize バイトがルーム名で、その後に OperationPayloadSize バイトが
# 続きます。ルーム名の最大バイト数は 2の8乗 バイトであり、OperationPayloadSize の
# 最大バイト数は 2の29乗 バイトです。
