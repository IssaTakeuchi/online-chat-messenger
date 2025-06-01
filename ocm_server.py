import socket
import os
from pathlib import Path

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = '0.0.0.0'
server_port = 9001

# フォルダが存在するかチェックする。存在しない場合、フォルダが作成される。
# クライアントから受信したファイルを格納するのに必要。
dpath = 'temp'
if not os.path.exists(dpath):
    os.makedirs(dpath)
    
print('Starting up on {} port {}'.format(server_address,server_port))

# ソケットをサーバーのアドレスをポートに紐付けする
sock.bind((server_address,server_port))

sock.listen(1)

while True:
    connection,client_address = sock.accept()
    try:
        print('connection from',client_address)
        # クライアントから受信したヘッダーを読み取る
        header = connection.recv(8)

        username_length = int.from_bytes(header[:1],"big")
        data_length = int.from_bytes(header[1:8],"big")
        stream_rate = 4096

        print('Received header from client. Byte lengths: Title length {}, data length {}'.format(username_length,data_length))

        username = connection.recv(username_length).decode('utf-8')
        print('Username: {}'.format(username))

        if data_length == 0:
            raise Exception('No data to raead from client.')
        
