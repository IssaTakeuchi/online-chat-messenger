import socket
import sys
import os 
import select

def protocol_header(username_length,data_length):
    return username_length.to_bytes(1,"big") + data_length.to_bytes(7,"big")

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

# サーバーが待ち受けているポートにソケットを接続する
server_address = input("Type in the server's address to connect to: ")
server_port = 9001

print('connecting to {}'.format(server_address,server_port))

username = input('Type your name : ')
username_bits = username.encode('utf-8')

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
        readable,_,_ = select.select([sys.stdin,sock],[],[])

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
