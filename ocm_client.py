import socket
import sys
import os 

def protocol_header(username_length,data_length):
    return username_length.to_bytes(1,"big") + data_length.to_bytes(7,"big")

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

# サーバーが待ち受けているポートにソケットを接続する
server_address = input("Type in the server's address to connect to: ")
server_port = 9001

print('connecting to {}'.format(server_address,server_port))

try:
    username = input('Type your name : ')
    message = input('Type messege : ')

    username_bits = username.encode('utf-8')
    message_bits = message.encode('utf-8')

    header = protocol_header(len(username_bits),len(message_bits))

    # データを送信
    sock.sendto(header,(server_address,server_port))
    sock.sendto(username_bits,(server_address,server_port))
    sock.sendto(message_bits,(server_address,server_port))

    # データを受信
    data,server =  sock.recvfrom(4096)
    print('Received from server:',data.decode('utf-8'))

finally:
    print("closing socket")
    sock.close()
