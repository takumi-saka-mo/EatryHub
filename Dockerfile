FROM python:3.10-slim

# 作業ディレクトリの作成
WORKDIR /app

# 必要なシステムパッケージのインストール（例：PostgreSQLのクライアント等）
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# requirements.txt をコンテナにコピーし、依存パッケージをインストール
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install jupyterlab ipykernel pandas

# プロジェクト全体をコンテナにコピー
COPY . /app/

# Djangoの静的ファイルを集める（必要に応じて）
RUN python manage.py collectstatic --noinput

# コンテナ起動時のコマンド（開発中なら runserver を使う）
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]