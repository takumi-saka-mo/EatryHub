# EatryHub

## 概要
Djangoをベースにした時間管理・座席管理システム<br>
### [home]

dhtmlxGantt を利用したガントチャート表示により, 来店状況やテーブル使用状況を直感的に把握可能<br>
時間管理システムのデータを使用.
- id: データID
- table: テーブル番号（例: “1卓”）
- text: プラン名(食べ放題や飲み放題等, 任意のプランが選択可能)
- start_date: 来店開始日時（例: “2025-03-27 17:30”）
- end_date: 退店（または seat_time）日時（例: “2025-03-27 23:59”） ← TimeManagement/views.pyでの計算結果

### [時間管理システム]

AJAX を用いた非同期更新を使った時間管理システム.<br>
表計算ソフトライクなUIで, これまでの操作と変わりがない様に設計.

### [空席モニタ]

※実装予定<br>
時間管理システムのデータを用いて, 次回空席予定のテーブルを表示. 配席効率の向上.



## 特徴

- **ユーザー認証**  
Django標準の認証機能を利用したログイン&ログアウト機能

- **時間管理・座席管理**  
テーブルごとの来店記録、L.O. & 退店時刻、延長料金(回数)などを管理.


- **AJAX による非同期更新**  
セル編集やチェックボックスの更新を AJAX 経由で行い、ページの再読み込みなしに更新可能.
10秒ごとの自動更新のため, ラストオーダーなどの時間アラートの遅延は最大10秒.

- **ガントチャート表示**  
dhtmlxGanttを使用. 日毎の来店情報対してガントチャートを描画.



## 必要環境

- Python 3.10 以上
- Django 4.2 以降
- SQLite（デフォルト。必要に応じて他のデータベースにも対応）
- dhtmlxGantt（CDN 経由で読み込み）
- jQuery、Bootstrap、Boxicons、Google Fonts（CDN 経由で読み込み）

## インストール方法

1. リポジトリをクローン
```bash
git clone <リポジトリのURL>
cd EatryHub
```

2. 仮想環境の作成と依存パッケージのインストール
```bash
python -m venv env
source env/bin/activate  # Windows の場合は env\Scripts\activate
pip install -r requirements.txt
```

3. マイグレーションの実行
```bash
python manage.py migrate
```

4. スーパーユーザーの作成
```bash
python manage.py createsuperuser --username="<user_name>" --email=<"xxxx@exmaple.com>"
```

5. 静的ファイルの収集
```bash
python manage.py collectstatic --noinput
```

6. 開発サーバーの起動
```bash
python manage.py runserver
```

## Dockerを用いた実行方法

このプロジェクトはDockerでも動作するように設計しております.
- EatryHub/Dockerfile
- EatryHub/docker-compose.yml

以上2ファイルを参照してください.

※Dockerのインストール手順については省略します.

<br>

1. コンテナをビルド&起動
```bash
docker-compose up --build
```
(ビルド後であれば)
```bash
docker-compose up
```

2. ブラウザでアクセス
http://localhost:8000/ にアクセスしてください。

3. 新規ユーザ設定(バックグラウンドでDockerを起動しておくこと)
```bash
docker-compose exec web python manage.py createsuperuser --username="◯◯" --email="xxx@example.com"
```