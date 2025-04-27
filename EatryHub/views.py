import sqlite3
import pandas as pd
import json
from django.http import JsonResponse
from datetime import datetime as dt
# from sqlalchemy import create_engine
from TimeManagement.models import TimeManagementRecord
from EatryHub.models import TableStructure
from django.utils import timezone


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
    user_store = request.user.store
    if user_store is None:
        return render(request, 'EatryHub/error.html', {
            'error': "店舗情報が設定されていません。店舗情報を登録してください。"
        })

    selected_date_str = request.GET.get('selected_date')
    try:
        selected_date = dt.strptime(selected_date_str.strip(), '%Y-%m-%d').date() if selected_date_str else dt.today().date()
    except (ValueError, AttributeError):
        selected_date = dt.today().date()

    print("Selected date:", selected_date)

    records = list(TimeManagementRecord.objects.filter(
        store=user_store,
        date=selected_date,
    ).values(
        'id', 'date', 'table_number', 'people_count',
        'plan_name', 'start_time', 'end_time', 'out_time',
        'extensions', 'invoiceChecked', 'paymentChecked'
    ))

    cols = [
        'id', 'date', 'table_number', 'people_count',
        'plan_name', 'start_time', 'end_time', 'out_time',
        'extensions', 'invoiceChecked', 'paymentChecked'
    ]

    # DataFrameに変換
    try:
        df = pd.DataFrame.from_records(records, columns=cols)
        if df.empty:
            tasks = {"data": [], "links": []}
            return render(request, 'EatryHub/home.html', {'tasks': json.dumps(tasks)})
    except Exception as e:
        import logging
        logging.error(f"DataFrame生成エラー: {e}")
        df = pd.DataFrame()

    # 日付変換
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df[df['date'] == selected_date]

    # 人数
    df = df.dropna(subset=['people_count']).copy()
    df['people_count'] = df['people_count'].astype(int)

    # 時刻列の文字列正規化
    for col in ['start_time', 'end_time', 'out_time']:
        df[col] = df[col].astype(str).str.zfill(4).str.replace(r'(\d{2})(\d{2})', r'\1:\2', regex=True)

    # seat_timeカラムを作成
    df['seat_time'] = None

    # レモンプラン：out_timeが"00:00"なら"23:59"に補正
    mask_lemon = df['plan_name'] == 'レモン'
    df.loc[mask_lemon, 'seat_time'] = df.loc[mask_lemon, 'out_time'].apply(
        lambda t: "23:59" if t == "00:00" else t
    )

    # その他のプラン："【アウト】"を除いたextensionsを使う
    mask = df['plan_name'].isin(['食べ飲み90m', '食べ飲み120m', 'スーパー'])
    df.loc[mask, 'seat_time'] = df.loc[mask, 'extensions'].str.replace('【アウト】', '', regex=False)

    # seat_timeが欠損なら"23:59"補完
    df['seat_time'] = df['seat_time'].fillna("23:59")

    # 24:00以降を23:59に丸める関数
    def cap_time(time_str):
        try:
            hour, minute = map(int, time_str.split(":"))
            if hour >= 24:
                return "23:59"
            return time_str
        except Exception:
            return "23:59"
    df['seat_time'] = df['seat_time'].apply(cap_time)

    # status計算
    df['status'] = df['invoiceChecked'].astype(int) + df['paymentChecked'].astype(int)

    # タスク作成
    tasks = {"data": [], "links": []}
    for _, r in df.iterrows():
        # デフォルト seat_time
        seat_time = r.seat_time.strip()

        # paymentChecked が1なら現在時刻をseat_timeに上書き
        # プラン名に応じた判定
        if r.paymentChecked == 1:
            if r.plan_name not in ['食べ飲み90m', '食べ飲み120m', 'スーパー']:
                # 単品, エンドレス(実装予定)ならば, チェックボックス押下時の時刻をガントチャート終了とする.
                now = timezone.localtime()
                seat_time = now.strftime("%H:%M")

        tasks["data"].append({
            "id": int(r.id),
            "table": f"{r.table_number}卓",
            "resource": f"{r.date}-{r.table_number}",
            "text": r.plan_name,
            "start_date": f"{r.date} {r.start_time.strip()}",
            "end_date": f"{r.date} {seat_time}",
            "status": int(r.status)
        })

    # タスクソート
    def task_sort_key(task):
        is_active = 0 if task['status'] <= 1 else 1
        end_dt = dt.strptime(task['end_date'], "%Y-%m-%d %H:%M")
        return (is_active, end_dt)

    tasks["data"] = sorted(tasks["data"], key=task_sort_key)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # もしAjaxリクエストならtasksだけ返す
        return JsonResponse(tasks)

    return render(request, 'EatryHub/home.html', {
        'tasks': json.dumps(tasks)
    })