import sqlite3
import pandas as pd
import json
from datetime import datetime as dt
from sqlalchemy import create_engine
from TimeManagement.models import TimeManagementRecord

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views import View
from django.db import connection
from django.contrib.auth import login, logout

from .forms import LoginForm

class LoginView(View):
    template_name = 'EatryHub/login.html'

    def get(self, request):
        return render(request, self.template_name, {'form': LoginForm(request=request)})

    def post(self, request):
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('EatryHub:home')
        return render(request, self.template_name, {'form': form})

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('EatryHub:login')

def index(request):
    return render(request, 'EatryHub/index.html')

@login_required
def home(request):
    user_store = request.user.store  # ユーザーの所属店舗
    if user_store is None:
        # 店舗情報が未設定の場合、エラーメッセージを表示するか、デフォルトの店舗に切り替える処理を追加
        return render(request, 'EatryHub/error.html', {
            'error': "店舗情報が設定されていません。店舗情報を登録してください。"
        })
    # GET パラメータから selected_date を取得し、余分な空白を除去して解析する
    selected_date_str = request.GET.get('selected_date')
    try:
        selected_date = dt.strptime(selected_date_str.strip(), '%Y-%m-%d').date() if selected_date_str else dt.today().date()
    except (ValueError, AttributeError):
        selected_date = dt.today().date()
    
    print("Selected date:", selected_date)

    # Django の connection を利用して PostgreSQL からデータを取得
    # ※ ここで、ユーザーの店舗フィルタも追加（例: store_id = {user_store.id}）
    query = f"""
        SELECT id, date, table_number, people_count, plan_name, start_time, end_time, out_time, extensions, "invoiceChecked", "paymentChecked"
        FROM "TimeManagement_timemanagementrecord"
        WHERE table_number IS NOT NULL AND store_id = {user_store.id}
    """
    # SQLAlchemyエンジンにてデータを渡す
    engine = create_engine(settings.DATABASE_URL)
    df = pd.read_sql_query(query, con=engine)    
    # 日付列を日付型に変換してフィルタ
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df[df['date'] == selected_date]

    # people_count 欠損値除去 → int 変換
    df = df.dropna(subset=['people_count']).copy()
    df['people_count'] = df['people_count'].astype(int)

    # 各時刻列を文字列に変換し、4桁ゼロ埋めで HH:MM 形式に変換
    for col in ['start_time', 'end_time', 'out_time']:
        df[col] = df[col].astype(str).str.zfill(4).str.replace(r'(\d{2})(\d{2})', r'\1:\2', regex=True)

    # seat_time カラム作成：初期値は None
    df['seat_time'] = None

    # レモンの場合は、out_time が "00:00" なら "23:59"、それ以外はそのまま
    mask_lemon = df['plan_name'] == 'レモン'
    df.loc[mask_lemon, 'seat_time'] = df.loc[mask_lemon, 'out_time'].apply(
        lambda t: "23:59" if t == "00:00" else t
    )

    # その他のプランの場合：extensions から "【アウト】" を除去して使用
    mask = df['plan_name'].isin(['食べ飲み90m', '食べ飲み120m', 'スーパー'])
    df.loc[mask, 'seat_time'] = df.loc[mask, 'extensions'].str.replace('【アウト】', '', regex=False)

    # 万一 seat_time が欠損している場合は "23:59" を補完
    df['seat_time'] = df['seat_time'].fillna("23:59")

    # 24:00 以降の値を 23:59 に丸め込む
    def cap_time(time_str):
        try:
            hour, minute = map(int, time_str.split(":"))
            if hour >= 24:
                return "23:59"
            return time_str
        except Exception:
            return time_str
    df['seat_time'] = df['seat_time'].apply(cap_time)

    # status カラムの作成（invoiceChecked と paymentChecked の合計）
    df['status'] = df['invoiceChecked'].astype(int) + df['paymentChecked'].astype(int)

    # タスク辞書の作成（ガントチャート用）
    tasks = {"data": [], "links": []}
    for _, r in df.iterrows():
        tasks["data"].append({
            "id": int(r.id),
            "table": f"{r.table_number}卓",
            "resource": f"{r.date}-{r.table_number}",
            "text": r.plan_name,
            "start_date": f"{r.date} {r.start_time.strip()}",
            "end_date": f"{r.date} {r.seat_time.strip()}",
            "status": int(r.status)
        })

    # タスクをソート（status と end_date で）
    def task_sort_key(task):
        is_active = 0 if task['status'] <= 1 else 1
        end_dt = dt.strptime(task['end_date'], "%Y-%m-%d %H:%M")
        return (is_active, end_dt)

    tasks["data"] = sorted(tasks["data"], key=task_sort_key)

    return render(request, 'EatryHub/home.html', {'tasks': json.dumps(tasks)})