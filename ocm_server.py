import socket
import os
from pathlib import Path

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = '0.0.0.0'
server_port = 9001

print('Starting up on {} port {}'.format(server_address,server_port))

# ソケットをサーバーのアドレスをポートに紐付けする
sock.bind((server_address,server_port))

try:
    while True:
        try:
            # クライアントから受信したヘッダーを読み取る
            header,addr = sock.recvfrom(8)

            username_length = int.from_bytes(header[:1],"big")
            data_length = int.from_bytes(header[1:8],"big")
            stream_rate = 4096

            print('Received header from client. Byte lengths: Title length {}, data length {}'.format(username_length,data_length))

            username_data,_ = sock.recvfrom(username_length)
            username = username_data.decode('utf-8')
            print('Username: {}'.format(username))

            if data_length == 0:
                raise Exception('No data to raead from client.')
            else:
                message_data,_= sock.recvfrom(data_length)
                message = message_data.decode('utf-8')
                print('Message: {}'.format(message))

            # データを送信
            confirmation_massage = f"Server received your massage: '{message}' from '{username}'"
            sock.sendto(confirmation_massage.encode('utf-8'),addr)

        except Exception as e :
            print(f"Error: {e}")

finally:
    print("Closing current connection")
    sock.close()
