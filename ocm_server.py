import socket
import os
from pathlib import Path


def protocol_header(username_length,data_length):
    return username_length.to_bytes(1,"big") + data_length.to_bytes(7,"big")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = '0.0.0.0'
server_port = 9001

connected_clients = {}

print('Starting up on {} port {}'.format(server_address,server_port))

# ソケットをサーバーのアドレスをポートに紐付けする
sock.bind((server_address,server_port))

try:
    while True:
        try:
            # クライアントから受信したヘッダーを読み取る
            header,client_addr = sock.recvfrom(8)

            username_length = int.from_bytes(header[:1],"big")
            data_length = int.from_bytes(header[1:8],"big")

            username_data,_ = sock.recvfrom(username_length)
            username = username_data.decode('utf-8')

            if data_length == 0:
                print(f"Error: No data to read from client {client_addr} - possibily malformed message.")
                message = ""

            else:
                message_data,_= sock.recvfrom(data_length)
                message = message_data.decode('utf-8')

            print(f'Recerved from {client_addr} ({username}): {message}')

            # クライアントリスト更新
            connected_clients[client_addr] = username

            # メッセージの種類をチェック
            if message.startswith("JOIN:"):
                # 新しいクライアントが追加
                actual_username = message[len("JOIN:"):] # JOIN:を除いた部分が実際のユーザー名
                connected_clients[client_addr] = actual_username
                print(f"Client joined: {actual_username} from {client_addr}.Current clients: {connected_clients}")

                # 参加メッセージを他の全員に通知
                join_notification = f"--- {actual_username} has joined the chat ---"
                encoded_notification = join_notification.encode('utf-8')

                # 通知メッセージ用ヘッダーを生成
                notification_header = protocol_header(0,len(encoded_notification))

                for addr,name in connected_clients.items():
                    if addr != client_addr:
                        sock.sendto(notification_header,addr)
                        sock.sendto(encoded_notification,addr)
                
                # 参加者本人には確認メッセージを送る
                welcome_message = "Welcome to the chat!"
                encoded_welcome = welcome_message.encode('utf-8')
                welcome_header = protocol_header(0,len(encoded_welcome))
                sock.sendto(welcome_header,client_addr)
                sock.sendto(encoded_welcome,client_addr)


            elif message.startswith("LEAVE:"):
                # クライアントが切断
                if client_addr in connected_clients:
                    leaving_username = connected_clients.pop(client_addr)
                    print(f"Client left: {leaving_username} from {client_addr}. Remaining clients: {connected_clients}")

                    # 離脱メッセージを他の全員に通知
                    leave_notification = f"--- {leaving_username} has left the chat ---"
                    encoded_notification = leave_notification.encode('utf-8')

                    # 通知メッセージ用のヘッダーを生成
                    notification_header = protocol_header(0,len(encoded_notification))

                    for addr, name in connected_clients.items():
                        sock.sendto(notification_header,addr)
                        sock.sendto(encoded_notification,addr)
                else:
                    print(f"Unknown client {client_addr} tried to leave.")

            else:
                # 通常のチャットメッセージ
                relay_message = f"[{username}]: {message}"
                encoded_relay_message = relay_message.encode('utf-8')

                # リレーメッセージ用のヘッダーを生成
                relay_header = protocol_header(0,len(encoded_relay_message))

                for addr,name in connected_clients.items():
                    if addr != client_addr:
                        print(f"Relaying '{relay_message}' to {name} at {addr}")
                        sock.sendto(relay_header,addr)
                        sock.sendto(encoded_relay_message,addr)

                # 送信者に確認メッセージを送る
                confirmation_massage = "Your message has been sent."
                encoded_confirmation = confirmation_massage.encode('utf-8')
                confirmation_header = protocol_header(0,len(encoded_confirmation))
                sock.sendto(confirmation_header,client_addr)
                sock.sendto(encoded_confirmation,client_addr)
                

        except Exception as e :
            print(f"Error processing message: {e}")

finally:
    print("Closing current connection")
    sock.close()
