import sqlite3
import pandas as pd
import json
from datetime import datetime as dt
from sqlalchemy import create_engine
from TimeManagement.models import TimeManagementRecord
from EatryHub.models import TableStructure


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

    # 店舗の座席一覧を取得
    tables = TableStructure.objects.filter(store=user_store)

    # 今日のTimeManagementRecord取得
    records = list(TimeManagementRecord.objects.filter(
        store=user_store,
        date=selected_date,
    ).values(
        'id', 'date', 'table_number', 'people_count',
        'plan_name', 'start_time', 'end_time', 'out_time',
        'extensions', 'invoiceChecked', 'paymentChecked'
    ))

    # 空でもcolumnsを渡すように
    cols = [
      'id', 'date', 'table_number', 'people_count',
      'plan_name', 'start_time', 'end_time', 'out_time',
      'extensions', 'invoiceChecked', 'paymentChecked'
    ]

    # レコードを辞書化（table_number基準で）
    records_dict = {r['table_number']: r for r in records}

    tasks = {"data": [], "links": []}

    # まず全席分ループ
    for table in tables:
        record = records_dict.get(table.table_number)

        if record:
            try:
                start_time = str(record['start_time']).zfill(4)
                end_time = str(record['out_time']).zfill(4) if record['out_time'] else "2359"
                start_time_fmt = f"{start_time[:2]}:{start_time[2:]}"
                end_time_fmt = f"{end_time[:2]}:{end_time[2:]}"

                # status計算（invoiceChecked + paymentChecked）
                status = int(record['invoiceChecked']) + int(record['paymentChecked'])

                tasks["data"].append({
                    "id": int(record['id']),
                    "table": f"{record['table_number']}卓",
                    "resource": f"{record['date']}-{record['table_number']}",
                    "text": record['plan_name'],
                    "start_date": f"{record['date']} {start_time_fmt}",
                    "end_date": f"{record['date']} {end_time_fmt}",
                    "status": status
                })
            except Exception as e:
                import logging
                logging.error(f"レコード処理中にエラー: {e}")
                continue

        else:
            # データなし席 → 「未使用」として出す
            tasks["data"].append({
                "id": f"table-{table.table_number}",
                "table": f"{table.table_number}卓",
                "resource": f"{selected_date}-{table.table_number}",
                "text": "未使用",
                "start_date": f"{selected_date} 00:00",
                "end_date": f"{selected_date} 23:59",
                "status": 0
            })

    # タスクをソート（status優先 → end_time優先）
    def task_sort_key(task):
        is_active = 0 if task['status'] <= 1 else 1
        end_dt = dt.strptime(task['end_date'], "%Y-%m-%d %H:%M")
        return (is_active, end_dt)

    tasks["data"] = sorted(tasks["data"], key=task_sort_key)

    return render(request, 'EatryHub/home.html', {'tasks': json.dumps(tasks)})