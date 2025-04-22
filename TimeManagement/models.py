# TimeManagement/models.py
from django.db import models
from datetime import date
from EatryHub.models import Store

class TimeManagementRecord(models.Model):
    """
    [TimeManagement内テーブルレコード]\n
    席時間(10列目)は未実装\n
    リロード後, 任意の行を更新すると計算結果が反映される.
    """
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    row_number = models.IntegerField()
    # 1～5列目
    plan_name = models.CharField(max_length=100, blank=True)
    table_number = models.CharField(max_length=50, blank=True)
    people_count = models.IntegerField(null=True, blank=True)
    start_time = models.CharField(max_length=5, blank=True)
    end_time = models.CharField(max_length=5, blank=True)
    # 6列目以降
    stay = models.CharField(max_length=20, blank=True)         # 滞在時間 or L.O.時間
    extensions = models.CharField(max_length=20, blank=True)   # 延長回数(合計) or アウト時間
    water_time = models.CharField(max_length=20, blank=True)   # waterの計算結果
    water_counts = models.CharField(max_length=20, blank=True) # 補充回数
    out_time = models.CharField(max_length=20, blank=True)     # 退店時間(指定のプランの場合のみ表示)
    water_override = models.IntegerField(default=0)            # 例：Overrideレベル
    col11 = models.CharField(max_length=20, blank=False)        # L.O.
    col12 = models.CharField(max_length=20, blank=False)        # レバー
    invoiceChecked = models.BooleanField(default=False)
    paymentChecked = models.BooleanField(default=False)
    status = models.CharField(max_length=20, blank=True)
    memo = models.TextField(blank=True)

    def __str__(self):
        return f"{self.date} - Row {self.row_number}"