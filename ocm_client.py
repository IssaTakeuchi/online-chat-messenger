import socket
import sys
import os 

def protocol_header(username_length,data_length):
    return username_length.to_bytes(1,"big") + data_length.to_bytes(7,"big")

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

# サーバーが待ち受けているポートにソケットを接続する
server_address = input("Type in the server's address to connect to: ")
server_port = 9001

print('connecting to {}'.format(server_address,server_port))

try:
    sock.connect((server_address,server_port))
except socket.error as err:
    print(err)
    sys.exit(1)

try:
    username = input('Type your name : ')
    message = input('Type messege : ')

    username_bits = username.encode('utf-8')
    message_bits = message.encode('utf-8')

    header = protocol_header(len(username_bits),len(message_bits))

    sock.send(header)

    sock.send(username_bits)
    sock.send(message_bits)

finally:
    print("closing socket")
    sock.close()
