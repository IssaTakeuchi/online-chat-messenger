import socket
import os
from pathlib import Path
import time

def protocol_header(username_length,data_length):
    return username_length.to_bytes(1,"big") + data_length.to_bytes(7,"big")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = '0.0.0.0'
server_port = 9001

connected_clients = {}

# タイムアウト設定
CLIENT_TIMEOUT_SECONDS = 60 # クライアントが60秒間活動がない場合に削除
CLEANUP_INTERVAL_SECONDS = 10 # 10秒毎に非アクティブなクライアントをチェック

last_cleanup_time = time.time()

print('Starting up on {} port {}'.format(server_address,server_port))

# ソケットをサーバーのアドレスをポートに紐付けする
sock.bind((server_address,server_port))

try:
    while True:
        # 非アクティブなクライアントのクリーンアップを定期的に実行
        current_time = time.time()
        if current_time - last_cleanup_time > CLEANUP_INTERVAL_SECONDS:
            clients_to_remove = []
            # ループ中に辞書が変更される可能性があるので、items()のコピーを操作します
            for addr, client_info in list(connected_clients.items()):
                if isinstance(client_info, dict) and 'last_activity' in client_info and 'username' in client_info:
                    if current_time - client_info['last_activity'] > CLIENT_TIMEOUT_SECONDS:
                        clients_to_remove.append(addr)
                else:
                    # 不正な形式のデータを見つけた場合、ログを出力し削除します
                    print(f"Warning: Malformed client info for {addr}: {client_info}. Removing.")
                    clients_to_remove.append(addr)
            
            for addr in clients_to_remove:
                if addr in connected_clients: # 念のため、削除対象が存在することを確認
                    removed_info = connected_clients.pop(addr)
                    # 削除された情報からusernameを取得。もしusernameがない場合は'Unknown'
                    removed_username = removed_info.get('username', 'Unknown') 
                    print(f"Client timed out and removed: {removed_username} from {addr}. Remaining clients: {len(connected_clients)} clients.")

                    # タイムアウト通知を他のクライアントに送信
                    timeout_notification = f"--- {removed_username} has timed out ---"
                    encoded_notification = timeout_notification.encode('utf-8')
                    notification_header = protocol_header(0,len(encoded_notification))

                    for other_addr, other_info in list(connected_clients.items()): 
                        # 送信対象も正しい形式か確認します
                        if isinstance(other_info, dict):
                            sock.sendto(notification_header,other_addr)
                            sock.sendto(encoded_notification,other_addr)
            
            last_cleanup_time = current_time # クリーンアップ時刻を更新
        
        try:
            sock.settimeout(1.0) # 1秒のタイムアウトを設定
            # クライアントから受信したヘッダーを読み取る
            header,client_addr = sock.recvfrom(8)
            sock.settimeout(None) # 受信後、タイムアウトをもとに戻す

            username_length = int.from_bytes(header[:1],"big")
            data_length = int.from_bytes(header[1:8],"big")

            MAX_MESSAGE_SIZE = 4096
            # 受信しようとしているメッセージのデータ長が上限を超えていないかチェック
            if data_length > MAX_MESSAGE_SIZE:
                print (f"Error: Received message size {data_length} exceeds max allowed {MAX_MESSAGE_SIZE} from {client_addr}. Dropping packet.")
                continue # このメッセージの処理をスキップし、次の受信へ

            username_data,_ = sock.recvfrom(username_length)
            username = username_data.decode('utf-8')

            message_data,_= sock.recvfrom(data_length)
            message = message_data.decode('utf-8')

            print(f'Received from {client_addr} ({username}): {message}')

            # クライアントの情報がまだ辞書になければ新規作成、あれば更新します。
            # username は受信した最新のものを使用します。
            connected_clients[client_addr] = {'username': username, 'last_activity': time.time()}

            # メッセージの種類をチェック
            if message.startswith("JOIN:"):
                # JOINメッセージの場合、`username` 変数にはすでにJOINしているクライアントのユーザー名が入っています
                actual_username = username 
                print(f"Client joined: {actual_username} from {client_addr}. Current clients: {len(connected_clients)} clients.")

                # 参加メッセージを他の全員に通知
                join_notification = f"--- {actual_username} has joined the chat ---"
                encoded_notification = join_notification.encode('utf-8')
                notification_header = protocol_header(0,len(encoded_notification))

                for addr_to_send, client_info_to_send in list(connected_clients.items()): 
                    if addr_to_send != client_addr and isinstance(client_info_to_send, dict): 
                        sock.sendto(notification_header,addr_to_send)
                        sock.sendto(encoded_notification,addr_to_send)
                
                # 参加者本人には確認メッセージを送る
                welcome_message = "Welcome to the chat!"
                encoded_welcome = welcome_message.encode('utf-8')
                welcome_header = protocol_header(0,len(encoded_welcome))
                sock.sendto(welcome_header,client_addr)
                sock.sendto(encoded_welcome,client_addr)


            elif message.startswith("LEAVE:"):
                # クライアントが切断
                if client_addr in connected_clients:
                    # pop() の結果は辞書形式なので、'username'キーでアクセスします
                    leaving_username = connected_clients.pop(client_addr)['username'] 
                    print(f"Client left: {leaving_username} from {client_addr}. Remaining clients: {len(connected_clients)} clients.")

                    # 離脱メッセージを他の全員に通知
                    leave_notification = f"--- {leaving_username} has left the chat ---"
                    encoded_notification = leave_notification.encode('utf-8')
                    notification_header = protocol_header(0,len(encoded_notification))

                    for addr_to_send, client_info_to_send in list(connected_clients.items()): 
                        if addr_to_send != client_addr and isinstance(client_info_to_send, dict): 
                            sock.sendto(notification_header,addr_to_send)
                            sock.sendto(encoded_notification,addr_to_send)
                else:
                    print(f"Unknown client {client_addr} tried to leave.")

            elif message.startswith("HEARTBEAT:"):
                # ハートビートを受信した場合、`connected_clients`への更新は既に上記で行われているので、ここではログのみ
                if client_addr in connected_clients:
                    print(f"Heartbeat received from {connected_clients[client_addr]['username']} at {client_addr}. Activity updated.")
                else:
                    print(f"Heartbeat from unknown client {client_addr}. Ignoring (client not in list).")
            else:
                # 通常のチャットメッセージ
                relay_message = f"[{username}]: {message}"
                encoded_relay_message = relay_message.encode('utf-8')

                # リレーメッセージ用のヘッダーを生成
                relay_header = protocol_header(0,len(encoded_relay_message))

                for addr_to_send, client_info_to_send in list(connected_clients.items()): 
                    # 送信元を除く全てのクライアントにリレーし、かつクライアント情報が正しい形式か確認
                    if addr_to_send != client_addr and isinstance(client_info_to_send, dict):
                        print(f"Relaying '{relay_message}' to {client_info_to_send['username']} at {addr_to_send}")
                        sock.sendto(relay_header,addr_to_send)
                        sock.sendto(encoded_relay_message,addr_to_send)

                # 送信者に確認メッセージを送る
                confirmation_message = "Your message has been sent."
                encoded_confirmation = confirmation_message.encode('utf-8')
                confirmation_header = protocol_header(0,len(encoded_confirmation))
                sock.sendto(confirmation_header,client_addr)
                sock.sendto(encoded_confirmation,client_addr)
                
        except socket.timeout:
            # recvfromがタイムアウトした場合、次のループでクリーンアップ処理へ進みます
            pass
        except Exception as e :
            print(f"Error processing message: {e}")

finally:
    print("Closing current connection")
    sock.close()
