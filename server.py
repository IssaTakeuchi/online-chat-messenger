import socket
import pathlib
import os
import random
import string
import json

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


def create_chatroom(room_name,state,username):
    # チャットルームが既に存在するか確認
    if room_name in chatroom:
        print(f"Chat room '{room_name}' already exists.")
        return {
            'status': 'error',
            'message': f"Chat room '{room_name}' already exists."
        }

    # passwordを設定
    generated_password = random_password()
    print(f"Generated password for chat room '{room_name}': {generated_password}")

    # サーバの初期化（0）クライアントが新しいチャットルームを作成するリクエストを送信
    if state == 0:
        print(f"Creating chat room: {room_name} with host: {username}")
        # 辞書に新しいチャットルームのエントリを追加
        chatroom[room_name] = {
            'password': generated_password,
            'host': username,  # ホストのユーザー名を保存
            'users': [username] # 初期ユーザーとしてホストのユーザー名を追加
        }
        
        # リクエストの応答（1）サーバーはステータスコードを含むペイロードで即座に応答する
        current_state = 1
        print(f"Chat room '{room_name}' created successfully.status: {current_state}")
    
        # リクエストの完了（2）サーバは特定の生成されたユニークなトークンをクライアントに送り、
        # このトークンにユーザー名を割り当てる
        # このトークンはクライアントをチャットルームのホストとして認識する
        # usernametokenを生成
        usernametoken = f"user_{random.randint(1000, 9999)}"

        usernametoken = usernametoken[:255] # 255バイトまでに制限

        # usernametokenとユーザー名を紐付ける
        usernametoken_dict[username] = usernametoken
        print(f"User '{username}' has been assigned token '{usernametoken}' in room '{room_name}'.")
        
        current_state = 2
        return {
            'status': 'success',
            'room_name': room_name,
            'password': generated_password,
            'usernametoken': usernametoken,
            'state':current_state,
        }
    return {'status':'erroe', 'message':'Invalid state for creating chat room.'}

def enter_chatroom(room_name,state,username):
    # サーバの初期化（0）クライアントが既存のチャットルームに参加するリクエストを送信
    if state == 0:
        print(f"Joining chat room: {room_name} as user: {username}")
        if room_name in chatroom:
            if username not in chatroom[room_name]['users']: # すでに参加していないか確認
                chatroom[room_name]['users'].append(username)
                print(f"User '{username}' has joined chat room '{room_name}'.")
            else:
                print(f"Chat room '{room_name}' does not exist.")
                return None

            # リクエストの応答（1）サーバーはステータスコードを含むペイロードで即座に応答する
            current_state = 1
            print(f"Chat room '{room_name}' created successfully.status: {current_state}")
    
            # リクエストの完了（2）サーバは特定の生成されたユニークなトークンをクライアントに送り、
            # このトークンにユーザー名を割り当てる
            # このトークンはクライアントをチャットルームのホストとして認識する
            # usernametokenを生成
            usernametoken = f"user_{random.randint(1000, 9999)}"

            # usernametokenとユーザー名を紐付ける
            usernametoken_dict[username] = usernametoken
            print(f"User '{username}' has been assigned token '{usernametoken}' in room '{room_name}'.")
            
            current_state = 2
            return {
                'status': 'success',
                'room_name': room_name,
                'usernametoken': usernametoken,
                'state': current_state,
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
        # ここのclient_addressがトークンとなり、チャットルームの識別子として使用されます。
        connection, client_address = sock.accept()
        try:
            print('connection from', client_address)
            header = connection.recv(32)
            room_name_size = int.from_bytes(header[0:1], 'big')
            operation = int.from_bytes(header[1:2], 'big')
            state = int.from_bytes(header[2:3], 'big')
            operation_payload_size = int.from_bytes(header[3:32], 'big')
            print(f"Headder parsed: RoomNameSize={room_name_size}, Operation={operation}, State={state}, OperationPayloadSize={operation_payload_size}")

            room_name_bytes = connection.recv(room_name_size)
            room_name = room_name_bytes.decode('utf-8')
            print(f"Room name received: {room_name}")

            operation_payload = connection.recv(operation_payload_size)

            # operation_payloadからユーザー名とパスワードをパース
            username = ""
            password = ""
            current_offset = 0

            # ユーザー名のパース
            if len(operation_payload) > current_offset:
                username_length = int.from_bytes(operation_payload[current_offset:current_offset+1],'big')
                current_offset += 1
                if len(operation_payload) >= current_offset + username_length:
                    username_bytes = operation_payload[current_offset:current_offset + username_length]
                    username = username_bytes.decode('utf-8')
                    current_offset += username_length
                    print(f"parsed username: '{username}' (length: {username_length})")
                else:
                    print("Error: Username length exceeds operation payload size.")
                    raise ValueError("Username length exceeds operation payload size.")
            else:
                print("Error: Operation payload is empty or too short for username.")
                raise ValueError("Operation payload is empty or too short for username.")
            
            # パスワードのパース(operation == 2 の場合)
            if operation == 2:
                if len(operation_payload) > current_offset:
                    password_length = int.from_bytes(operation_payload[current_offset:current_offset+1],'big')
                    current_offset += 1
                    if len(operation_payload) >= current_offset + password_length:
                        password_bytes = operation_payload[current_offset:current_offset + password_length]
                        password = password_bytes.decode('utf-8')
                        print(f"parsed password: '{password}' (length: {password_length})")
                    else:
                        print("Error: Password length exceeds operation payload size.")
                        raise ValueError("Password length exceeds operation payload size.")
                else:
                    print("Error: Operation payload is empty or too short for password.")
                    raise ValueError("Operation payload is empty or too short for password.")

            response_data = {}

            if operation == 1: # create new chatroom
                print(f"Creating new chat room: {room_name}")
                response_data = create_chatroom(room_name,state,username)

            elif operation == 2: # join  existing chatroom
                print(f"Joining chat room: {room_name}")

                #　operation_payloadをデコード
                # パスワードの検証
                checkpass = check_password(room_name, password)
                if not checkpass:
                    response_data = {
                        'status': 'error',
                        'message': f"Incorrect password for room '{room_name}'."
                    }
                else:
                    # 既存のチャットルームに参加する
                    response_data = enter_chatroom(room_name,state,username)
            else:
                response_data = {
                    'status': 'error',
                    'message': f"Invalid operation: {operation}"
                }

            #  クライアントへの応答をJSON形式で送信
            response_json = json.dumps(response_data)
            connection.sendall(response_json.encode('utf-8'))

        except Exception as e:
            print(f"Error handling client {client_address}:{e}")
            response_data = {
                'status': 'error',
                'message': str(e)
            } 
            connection.sendall(json.dumps(response_data).encode('utf-8'))

        finally:
            print(f"Closing connection to {client_address}.")
            connection.close()



if __name__ == "__main__":
    main()
