# online-chat-messenger

### ・ルームの作成（TCP）
新しいチャットルームの作成と参加はTCPプロトコルを使用。\
チャットルームへの接続後、自動的にUDP接続になる。

### ・ルームでのチャット（UDP）
ホストが退出したら自動的にチャットルームが閉じられる仕様。\
HEARTBEATを使用して定期的な生存確認を実施。

### ・実行手順
#### 1.サーバーサイドの起動
`python3 server.py`

#### 2.クライアントの起動
`python3 client.py`\
その後、以下の項目を入力、選択していく。
- room name
- operation(1: create , 2: join)
- state(0: Initial, 1: Response, 2: Complete)
- user name
- (2: join　の時はパスワード)\
チャットルームからの退出時は、
`exit`と入力。
<img width="1662" height="626" alt="image" src="https://github.com/user-attachments/assets/375d4ab6-f7e5-4ad0-aaa2-63e89c572fc2" />
