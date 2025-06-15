import socket
import sys
import os 
import select
import time

def protocol_header(username_length,data_length):
    return username_length.to_bytes(1,"big") + data_length.to_bytes(7,"big")

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

# サーバーが待ち受けているポートにソケットを接続する
server_address = input("Type in the server's address to connect to: ")
server_port = 9001

print('connecting to {}'.format(server_address,server_port))

username = input('Type your name : ')
username_bits = username.encode('utf-8')

# ハートビート設定
HEARTBEAT_INTERVAL_SECONDS = 30 # 30秒毎にハートビートを送信
last_hearbeat_time = time.time()

try:
    # サーバーに初回接続とユーザー名の通知
    # これにより、サーバーはクライアントのアドレスをユーザー名を紐付けできる
    initial_message = f"JOIN:{username}" #サーバーに結合を知らせるメッセージ
    initial_message_bits = initial_message.encode('utf-8')
    initial_header = protocol_header(len(username_bits),len(initial_message_bits)) #ヘッダーのデータ長はメッセージの長さにする

    sock.sendto(initial_header,(server_address,server_port))
    sock.sendto(username_bits,(server_address,server_port))
    sock.sendto(initial_message_bits,(server_address,server_port))

    print("--- Chat Started ---")
    print("Type your message and press Enter. Type 'exit' to quit.")

    while True:
        # ハートビート送信のチェック
        current_time = time.time()
        if current_time - last_hearbeat_time > HEARTBEAT_INTERVAL_SECONDS:
            heartbeat_message = f"HEARTBEAT:{username}" # ハートビートメッセージ
            heartbeat_message_bits = heartbeat_message.encode('utf-8')
            heartbeat_header = protocol_header(len(username_bits),len(heartbeat_message_bits))

            sock.sendto(heartbeat_header,(server_address,server_port))
            sock.sendto(username_bits,(server_address,server_port))
            sock.sendto(heartbeat_message_bits,(server_address,server_port))
            print(f"[{time.strftime('%H:%M:%S')}] Sent heartbeat.") # 送信確認用
            last_hearbeat_time = current_time

        readable,_,_ = select.select([sys.stdin,sock],[],[],1.0) # タイムアウトに1秒を設定

        for s in readable:
            if s == sys.stdin:
                # ユーザーがキーボードから入力した場合
                message = sys.stdin.readline().strip() # 改行文字を除去

                if message.lower() == 'exit':
                    print("Exiting chat.")
                    exit_message = f"LEAVE:{message}"
                    exit_message_bits = exit_message.encode('utf-8')
                    exit_header = protocol_header(len(username_bits),len(exit_message_bits))
                    sock.sendto(exit_header,(server_address,server_port))
                    sock.sendto(username_bits,(server_address,server_port))
                    sock.sendto(exit_message_bits,(server_address,server_port))
                    sys.exit() # プログラムの終了
                
                if message:
                    message_bits = message.encode('utf-8')
                    MAX_MESSAGE_SIZE = 4096
                    if len(message_bits) > MAX_MESSAGE_SIZE:
                        print(f"Error: Your message ({len(message_bits)} bytes) exceeds the maximum allow size of {MAX_MESSAGE_SIZE} bytes. Please shorten your message.")
                    
                    header = protocol_header(len(username_bits),len(message_bits))
                    sock.sendto(header,(server_address,server_port))
                    sock.sendto(username_bits,(server_address,server_port))
                    sock.sendto(message_bits,(server_address,server_port))
            
            elif s == sock:
                # ソケットにデータが届いたとき
                try:
                    # ヘッダーを受信
                    header,_ = sock.recvfrom(8)
                    username_len_received = int.from_bytes(header[:1],"big")
                    data_len_received = int.from_bytes(header[1:8],"big")

                    # ユーザー名とメッセージを受信
                    received_data,_ = sock.recvfrom(data_len_received)

                    # サーバーからのリレーメッセージをそのまま表示
                    print(f"\n{received_data.decode('utf-8')}")
                    sys.stdout.write(f'{username} > ') # メッセージ受信後もプロンプトを表示
                    sys.stdout.flush() # プロンプトがすぐに見えるようにフラッシュ

                except socket.error as e :
                    print(f"Socket error receiving data: {e}")
                    break # エラーが発生したらループを抜ける

finally:
    print("closing socket")
    sock.close()
