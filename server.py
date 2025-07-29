import socket
import select
import time
import random
import string
import json
import subprocess
import bcrypt

# チャットルームを保存する辞書を作成(UDPとTCPの両方で使用)
# {roome_name: {'password': 'hashed_password', 'host': 'username', 'users': {'usernametoken': {'username': '...', 'address': (ip,port), 'last_activity': time.time()}}}}
chatrooms = {}

# # usernametokenとユーザー名を保存するための辞書
usernametoken_dict = {}

# TCPサーバのソケット設定
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.setblocking(False) # 非ブロッキングモード
tcp_sock.bind(('0.0.0.0', 9001))
tcp_sock.listen(5)

# UDPサーバのソケット設定
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setblocking(False) # 非ブロッキングモード
udp_sock.bind(('0.0.0.0', 9001))

# selectで監視するソケットリスト
inputs = [tcp_sock, udp_sock]


def random_password(): # ランダムなパスワードを生成する関数   
    length = 8  # パスワードの長さ
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def check_password(room_name, password): # チャットルームのパスワードを検証する関数
    if room_name in chatrooms:
        if chatrooms[room_name]['password'] == password:
            print(f"Password for room '{room_name}' is correct.")
            return True
        else:
            print(f"Incorrect password for room '{room_name}'.")
            return False
    else:
        print(f"Chat room '{room_name}' does not exist.")
        return False


def create_chatroom(room_name,username):
    # チャットルームが既に存在するか確認
    if room_name in chatrooms:
        print(f"Chat room '{room_name}' already exists.")
        return {
            'status': 'error',
            'message': f"Chat room '{room_name}' already exists."
        }

    # passwordを設定
    generated_password = random_password()
    hashed_password = bcrypt.hashpw(generated_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # usernametokenを生成
    usernametoken = f"user_{random.randint(1000, 9999)}"
    
    chatrooms[room_name] = {
        'password': hashed_password,
        'host': username,  # ホストのユーザー名を保存
        'users': {
            usernametoken: {'username': username, 'address':None, 'last_activity': time.time()} # UDPアドレスは後で設定
        }
    }
    print(f"Chat room '{room_name}' created with password: {generated_password} for host {username}. Token: {usernametoken}")
    return {
        'status': 'success',
        'room_name': room_name,
        'password': generated_password,
        'usernametoken': usernametoken,
        }

def enter_chatroom(room_name,username,password):
    # サーバの初期化（0）クライアントが既存のチャットルームに参加するリクエストを送信
    if username not in chatrooms:
        return {
            'status' :  'error',
            'message' : f"Chat room '{room_name}' does not exist."
        }

    if not bcrypt.checkpw(password.encode('utf-8'), chatrooms[room_name]['password'].encode('utf-8')):
        return {
            'status': 'error',
            'message': f"Incorrect password for room '{room_name}'."
        }

    # ユーザー名が既に存在しないか確認
    for token, user_info in chatrooms[room_name]['users'].items():
        if user_info['username'] == username:
            return {
                'status': 'error',
                'message': f"Username '{username}' already exists in room '{room_name}'."
            }
        
    # ユーザートークンを生成
    usernametoken = f"user_{random.randint(1000, 9999)}"
    chatrooms[room_name]['users'][usernametoken] = {'username': username, 'address': None, 'last_activity': time.time()} # UDPアドレスは後で設定
    print(f"User '{username}' joined room '{room_name}'. Token: {usernametoken}")

    return {
        'status': 'success',
        'room_name': room_name,
        'usernametoken': usernametoken,
    }

def protocol_header_udp_message(username_length, data_length):
    return username_length.to_bytes(1, 'big') + data_length.to_bytes(7, 'big')

# UDPメッセージをブロードキャストするヘルパー関数
def broadcast_udp_message(room_name,sender_username, message_text, exclude_addr = None):
    if room_name not in chatrooms:
        print(f"Error : Room '{room_name}' not found for broadcast." )
        return
    relay_message = f"[{sender_username}]: {message_text}"
    encoded_relay_message = relay_message.encode('utf-8')

    # ヘッダーは送信者ユーザー名とメッセージの長さを含む
    sender_username_bytes = sender_username.encode('utf-8')
    relay_header = protocol_header_udp_message(len(sender_username_bytes), len(encoded_relay_message))

    for token, user_info in list(chatrooms[room_name]['users'].items()):
        target_addr = user_info.get('address')
        if target_addr and target_addr != exclude_addr:
            try:
                # ヘッダー　＋　送信者ユーザー名バイト列　＋　メッセージバイト列を結合して送信
                full_packet = relay_header + sender_username_bytes + encoded_relay_message
                udp_sock.sendto(full_packet, target_addr)
                print(f"Relaying '{relay_message}' to {user_info['username']} at {target_addr}")
            except socket.error as e:
                print(f"Error broadcasting to {target_addr}: {e}")

def main():
    print(f'Starting up on {tcp_sock.getsockname()[0]} port {tcp_sock.getsockname()[1]} (TCP)')
    print(f'Starting up on {udp_sock.getsockname()[0]} port {udp_sock.getsockname()[1]} (UDP)')
    
    last_cleanup_time = time.time()
    CLEANUP_INTERVAL_SECONDS = 10
    CLIENT_TIMEOUT_SECONDS = 60

    while inputs:
        current_time = time.time()
        # 非アクティブなクライアントのクリーンアップを定期的に実行
        if current_time - last_cleanup_time > CLEANUP_INTERVAL_SECONDS:
            for room_name , room_info in list(chatrooms.items()):
                users_to_remove = []
                for token, user_info in list (room_info['users'].items()):
                    if user_info.get('address') and current_time - user_info['last_activity'] > CLIENT_TIMEOUT_SECONDS:
                        users_to_remove.append((token,user_info[' username']))

                for token, username_to_remove in users_to_remove:
                    if token in room_info['users']:
                        del room_info['users'][token]
                        print(f"Client timed out and removed from room'{room_name}' :{username_to_remove}({token}).")
                        # 他クライアントに通知
                        broadcast_udp_message(room_name, "Server", f"--- {username_to_remove} has time out ---")
            last_cleanup_time = current_time

        readable,_,_ = select.select(inputs,[],[],1.0) # タイムアウト１秒

        for s in readable:
            if s is tcp_sock:
                # TCP接続の処理（チャットルームの作成、参加）
                connection, client_address = tcp_sock.accept()
                print(f'TCP connection from {client_address}')
                try:
                    header = connection.recv(32)
                    room_name_size = int.from_bytes(header[0:1], 'big')
                    operation = int.from_bytes(header[1:2], 'big')
                    state = int.from_bytes(header[2:3], 'big')
                    operation_payload_size = int.from_bytes(header[3:32], 'big')

                    operation_payload = connection.recv(operation_payload_size)

                    room_name_bytes = connection.recv(room_name_size)
                    room_name = room_name_bytes.decode('utf-8')


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
                        else:
                            raise ValueError("Username length exceeds operation payload size.")
                    else:
                        raise ValueError("Operation payload is empty or too short for username.")
                    
                    # パスワードのパース(operation == 2 の場合)
                    if operation == 2:
                        if len(operation_payload) > current_offset:
                            password_length = int.from_bytes(operation_payload[current_offset:current_offset+1],'big')
                            current_offset += 1
                            if len(operation_payload) >= current_offset + password_length:
                                password_bytes = operation_payload[current_offset:current_offset + password_length]
                                password = password_bytes.decode('utf-8')
                            else:
                                raise ValueError("Password length exceeds operation payload size.")
                        else:
                            raise ValueError("Operation payload is empty or too short for password.")

                    response_data = {}

                    if operation == 1: # create new chatroom
                        print(f"Creating new chat room: {room_name}")
                        response_data = create_chatroom(room_name,username)

                    elif operation == 2: # join  existing chatroom
                        print(f"Joining chat room: {room_name}")
                        response_data = enter_chatroom(room_name,username,password)
                    else:
                        response_data = {
                            'status': 'error',
                            'message': f"Invalid operation: {operation}"
                        }

                    #  クライアントへの応答をJSON形式で送信
                    response_json = json.dumps(response_data).encode('utf-8')
                    response_len_bytes = len(response_json).to_bytes(4,'big')
                    connection.sendall(response_len_bytes + response_json)

                except Exception as e:
                    print(f"Error handling TCP client {client_address}:{e}")
                    response_data = {
                        'status': 'error',
                        'message': str(e)
                    } 
                    encoded_error_response =json.dumps(response_data).encode('utf-8')
                    error_len_bytes = len(encoded_error_response).to_bytes(4,'big')
                    connection.sendall(error_len_bytes + encoded_error_response)

                finally:
                    connection.close()
                
            elif s is udp_sock:
                # UDPメッセージの処理（チャットメッセージの送信）
                try:
                    full_packet,client_addr = udp_sock.recvfrom(4096)

                    # クライアントからのUDPヘッダーをパース
                    # ヘッダー:RoomNameSize(１バイト)| TokenSize(１バイト)
                    udp_header_from_client = full_packet[:2]
                    room_name_size_udp = int.from_bytes(udp_header_from_client[:1],'big')
                    usernametoken_size_udp = int.from_bytes(udp_header_from_client[1:2,'big'])

                    # ルーム名とユーザー名トークンを抽出
                    offset = 2
                    room_name_bytes_udp = full_packet[offset : offset + room_name_size_udp]
                    room_name_udp = room_name_bytes_udp.decode('utf-8')
                    offset += room_name_size_udp

                    usernametoken_bytes_udp = full_packet[offset : offset + usernametoken_size_udp]
                    usernametoken_udp = usernametoken_bytes_udp.decode('utf-8')
                    offset += usernametoken_size_udp

                    # 残りの部分がメッセージのヘッダーとメッセー本体
                    message_header_from_client = full_packet[offset : offset + 5] #５バイト
                    username_len_in_message = int.from_bytes(message_header_from_client[:1],'big')
                    message_len_in_message = int.from_bytes(message_header_from_client[1:5],'big')
                    offset += 5

                    #メッセージ送信者ユーザー名とメッセージ本体
                    sender_username_bytes = full_packet[offset:offset + username_len_in_message]
                    sender_username = sender_username_bytes.decode('utf-8')
                    offset += username_len_in_message

                    message_content_bytes = full_packet[offset:offset + message_len_in_message]
                    message_content = message_content_bytes.decode('utf-8')

                    print(f'UDP Received from {client_addr} (Room: {room_name_udp}, User: {sender_username}, Token: {usernametoken_udp}): {message_content}')

                    # クライアントの最終活動時刻とアドレスを更新
                    if room_name_udp in chatrooms and \
                        usernametoken_udp in chatrooms[room_name_udp]['users']:
                        user_info = chatrooms[room_name_udp]['users'][usernametoken_udp]
                        user_info['last_activity'] = time.time()
                        user_info['address'] = client_addr # UDPアドレスを更新、設定

                        if message_content.startswith("HEARTBEAT:"):
                            print(f"Heartbeat from {sender_username} in room '{room_name_udp}'. Activity updated.")
                        elif message_content.startswith("LEAVE:"):
                            # ルームからユーザーを削除
                            if usernametoken_udp in chatrooms[room_name_udp]['users']:
                                del chatrooms[room_name_udp]['users'][usernametoken_udp]
                                print(f"User {sender_username} ({usernametoken_udp}) left room '{room_name_udp}'.")
                                broadcast_udp_message(room_name_udp,"Server",f"---{sender_username} has left the chat ---", exclude_addr=client_addr)
                        else:
                            # 通常のチャットメッセージをルーム内にブロードキャスト
                            broadcast_udp_message(room_name_udp, message_content, exclude_addr = client_addr)
                except Exception as e:
                    print(f"Error processing UDP message from {client_addr}: {e}")

if __name__ == "__main__":
    main()
