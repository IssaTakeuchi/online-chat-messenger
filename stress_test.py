import os
import socket
import argparse
import asyncio
import random
import string
import time

sent_messages = 0
start_time = 0

def protocol_header(username_length, data_length):
    return username_length.to_bytes(1, "big") + data_length.to_bytes(7, "big")

async def client_task(address,port,client_id,message_rate_per_sec):
    """
    一人のクライアントの動作を定義する非同期タスク
    """
    global sent_messages

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)  # 非同期処理のためにノンブロッキングに設定

    username = f"Bot_{client_id}"
    username_bits = username.encode('utf-8')

    # JOINメッセージを送信
    join_message = f"JOIN:{username}"
    join_message_bits = join_message.encode('utf-8')
    join_header = protocol_header(len(username_bits), len(join_message_bits))

    # asyncioでUDP送信
    loop = asyncio.get_running_loop()
    await loop.sock_sendto(sock, join_header + username_bits + join_message_bits, (address, port))
    
    # メッセージ送信の間隔を計算
    sleep_interval = 1.0 / message_rate_per_sec

    while True:
        try:
            # 100バイトのランダムなメッセージを作成
            message_body = ''.join(random.choices(string.ascii_letters + string.digits, k = 100))
            message_bits = message_body.encode('utf-8')

            header = protocol_header(len(username_bits),len(message_bits))

            # ヘッダー、ユーザー名、メッセージを結合して一度に送信
            payload = header + username_bits + message_bits

            await loop.sock_sendto(sock, payload, (address, port))
            sent_messages += 1

            await asyncio.sleep(sleep_interval)

        except Exception as e:
            print(f"Error in client: {client_id}: {e}")
            break

# num_clientsの数だけクライアントを起動し、そのうち、num_messageの数のユーザーだけメッセージを送信する。
# timeの時間の間監視を行い、終了後に各クライアントの送信メッセージ数を表示する。パケット量の計測も行う。
async def main(address,num_clients,num_message,duration):

    # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # server_address = (address,port)
    global sent_messages, start_time
    server_port = 9001
    rate_per_client = num_message / duration

    # すべてのクライアントをタスクを作成
    tasks = [
        client_task(address, server_port, i, rate_per_client) 
        for i in range(num_clients)
    ]

    start_time = time.time()

    # テストで指定された時間だけを実行
    gathered_tasks = asyncio.gather(*tasks)
    try:
        await asyncio.wait_for(gathered_tasks, timeout = duration)
    except asyncio.TimeoutError:
        print(f"Test completesd after {duration} seconds.")
    finally:
        gathered_tasks.cancel() # すべてのタスクをキャンセル

    end_time = time.time()
    actual_duration = end_time - start_time

    print("\n--- Test Results ---")
    print(f"Total messages sent: {sent_messages}")
    print(f"Actual duration: {actual_duration:.2f} seconds")

    # サーバーが処理すべきだった総パケット数を計算
    # (受信パケット＋送信者への買う人＋他クライアントへの通知)
    # 簡略化のため、1メッセージあたり（1受信 + （N-1）リレー）= Nパケットとする。
    total_packets_processed = sent_messages * num_clients
    print(f"Average mesaage rate: {(sent_messages / actual_duration):.2f} msg/s")
    print(f"Estimadted server packet rate: {total_packets_processed / actual_duration:.2f} packets/s")
    print("---- Stress test completed ----")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stress test the OCM server with multiple clients.")
    parser.add_argument('address',default='127.0.0.1')
    # parser.add_argument('port',type=int,default=9001)
    parser.add_argument('num_clients',type=int,default=100)
    parser.add_argument('num_message',type=int,default=100)
    parser.add_argument('duration',type=int, default=10)
    
    args = parser.parse_args()

    print(f'starting the stress test.address:{args.address}')
    print(f'number of clients: {args.num_clients} number of messages: {args.num_message} duration: {args.duration}s')

    asyncio.run(main(
        args.address,
        args.num_clients,
        args.num_message,
        args.duration
    )) 
