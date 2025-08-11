# chatroom.py
# UDPサーバーのチャットルーム管理機能

import socket
import time
import select
import sys

# ハートビート設定
HEARTBEAT_INTERVAL_SECONDS = 30 # 30秒毎にハートビートを送信
last_hearbeat_time = time.time()

def protocol_header(username, message):
    # ヘッダーを作成
    # ユーザー名の長さとメッセージの長さを含むヘッダー
    username_size = len(username)
    message_size = len(message)
    header = (username_size).to_bytes(1, 'big') + (message_size).to_bytes(4, 'big')
    return header

class ChatRoom:
    # headerにはルーム名とユーザートークンのサイズが含まれます。
    def enter_room(self, sock, server_address, server_port, username, roomname, usernametoken):
    
        #  ユーザー名とトークンをバイト列にエンコード
        username_bytes = username.encode('utf-8')
        roomname_bytes = roomname.encode('utf-8')
        usernametoken_bytes = usernametoken.encode('utf-8')

        print(f"Connected to {server_address}:{server_port} as {username}.")

        sys.stdout.write(f'{username} > ')
        sys.stdout.flush()  # プロンプトがすぐに見えるように

        global last_hearbeat_time   

        while True:
            # ハートビート送信のチェック
            current_time = time.time()
            if current_time - last_hearbeat_time > HEARTBEAT_INTERVAL_SECONDS:
                heartbeat_message = "HEARTBEAT" # ハートビートメッセージ
                heartbeat_message_bytes = heartbeat_message.encode('utf-8')

                # パケット全体を構築
                # ユーザー名トークン　｜　メッセージ本体
                full_packet = usernametoken_bytes + b":" + heartbeat_message_bytes
                sock.sendto(full_packet,(server_address,server_port))
                print(f"[{time.strftime('%H:%M:%S')}] Sent heartbeat.") # 送信確認用
                last_hearbeat_time = current_time

            readable,_,_ = select.select([sys.stdin,sock],[],[],1.0) # タイムアウトに1秒を設定

            for s in readable:
                if s == sys.stdin:
                    # ユーザーがキーボードから入力した場合
                    message = sys.stdin.readline().strip() # 改行文字を除去

                    if message.lower() == 'exit':
                        print("Exiting chat.")
                        exit_message = "LEAVE"
                        exit_message_bytes = exit_message.encode('utf-8')

                        # パケット全体を構築
                        full_packet = usernametoken_bytes + b":" + exit_message_bytes
                        sock.sendto(full_packet,(server_address,server_port))
                        sys.exit() # プログラムの終了
                    
                    if message:
                        message_bytes = message.encode('utf-8')

                        # 送信処理
                        full_packet = usernametoken_bytes + b":" + message_bytes
                        sock.sendto(full_packet, (server_address, server_port))

                        sys.stdout.write(f'{username} > ')  # メッセージ送信後もプロンプトを表示
                        sys.stdout.flush()  # プロンプトがすぐに見えるように
                
                elif s == sock:
                    # ソケットにデータが届いたとき
                    try:
                        # ヘッダーを受信
                        MAX_UDP_PACKET_SIZE = 4096
                        full_received_packet,_ = sock.recvfrom(MAX_UDP_PACKET_SIZE)
                        
                        # 受信したメッセージをデコードして表示
                        received_message = full_received_packet.decode('utf-8')
                        print(f"\n{received_message}")
                        
                        sys.stdout.write(f'{username} > ') # メッセージ受信後もプロンプトを表示
                        sys.stdout.flush() # プロンプトがすぐに見えるようにフラッシュ

                    except socket.error as e :
                        print(f"Socket error receiving data: {e}")
                        break # エラーが発生したらループを抜ける
