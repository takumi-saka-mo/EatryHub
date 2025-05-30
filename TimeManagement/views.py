from django.shortcuts import render
from django.http import JsonResponse
from .models import TimeManagementRecord
from django.contrib.auth.decorators import login_required


# table_view関数
from datetime import date

# calculate_count関数 "math.ceil()"
import math


from datetime import date, datetime

@login_required
def table_view(request):
    selected_date_str = request.GET.get('selected_date')
    try:
        selected_date = datetime.strptime(selected_date_str.strip(), '%Y-%m-%d').date() if selected_date_str else date.today()
    except (ValueError, AttributeError):
        selected_date = date.today()


    records = TimeManagementRecord.objects.filter(
        date=selected_date,
        store=request.user.store,
    )    

    for record in records:
        record.calculated_col6 = record.calculated_col7 = record.calculated_col10 = ""
        record.calculated_water_time = ""
        stay = extensions = seat = ""

        if record.start_time:
            if record.plan_name == "レモン" and record.end_time:
                stay = TimeManagementProcessor.calculate_time_diff(record.start_time, record.end_time)
                extensions = TimeManagementProcessor.calculate_count(stay, str(record.people_count or 0))
                seat = TimeManagementProcessor.calculate_seat_limit(record.end_time, record.plan_name)

                record.calculated_col6 = stay
                record.calculated_col7 = extensions
                record.calculated_col10 = seat

                # **DBに保存**
                record.stay = stay
                record.extensions = extensions
                record.out_time = seat

            elif record.plan_name in ["食べ飲み90m", "食べ飲み120m", "スーパー"]:
                lo = TimeManagementProcessor.calculate_LO(record.start_time, record.plan_name)
                out = TimeManagementProcessor.calculate_OUT(record.start_time, record.plan_name)

                record.calculated_col6 = lo
                record.calculated_col7 = out
                record.stay = lo
                record.extensions = out
                record.out_time = ""

            else:
                # Clear for other plans
                record.stay = record.extensions = record.out_time = ""

            save_fields = ['stay', 'extensions']
            if record.plan_name != "単品":  # ★「単品以外」ならout_timeも保存
                save_fields.append('out_time')
            if record.start_time:  # start_timeが空出ない場合のみwater_timeを生成
                save_fields.append('water_time')
            record.save(update_fields=save_fields)
            record.water_time = TimeManagementProcessor.calculate_water(record.start_time, override_level=record.water_override)
            record.calculated_water_time = record.water_time
            save_fields.append('water_time')
            record.save(update_fields=save_fields)

    record_dict = {r.row_number: r for r in records}
    return render(request, 'TimeManagement/table.html', {
        'rows': range(1, 201),
        'cols': range(1, 17),
        'record_dict': record_dict,
        'selected_date': selected_date.strftime('%Y-%m-%d'),
    })



@login_required
def table_data_api(request):
    from django.utils import timezone
    selected_date_str = request.GET.get('selected_date')
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_date = date.today()
    try:
        records_qs = TimeManagementRecord.objects.filter(
            date=selected_date, store=request.user.store
        )
        records = []
        for r in records_qs:
            plan = r.plan_name
            start = r.start_time
            end = r.end_time
            people = r.people_count
            end_time = r.end_time
            out_time = r.out_time
            stay = r.stay
            extensions = r.extensions

            # start_timeをhh:mm表記に
            def to_hhmm(val):
                """
                start_time(int4桁)をhh:mm表記に変換する関数
                [In]  1200
                [Out] 12:00
                """
                
                if not val or not str(val).isdigit():
                    return ""
                val = int(val)
                h = val // 100
                m = val % 100
                return f"{h:02d}:{m:02d}"

            start_time_disp = to_hhmm(start)

            if start:
                if plan == "レモン" and end:
                    stay = TimeManagementProcessor.calculate_time_diff(start, end)
                    extensions = TimeManagementProcessor.calculate_count(stay, str(people or 0))
                    out_time = TimeManagementProcessor.calculate_seat_limit(end, plan)
                    end_time_disp = to_hhmm(end)
                elif plan in ["食べ飲み90m", "食べ飲み120m", "スーパー"]:
                    lo = TimeManagementProcessor.calculate_LO(start, plan)
                    out = TimeManagementProcessor.calculate_OUT(start, plan)
                    if isinstance(lo, str) and lo.startswith("【ラスト】"):
                        end_time = lo.replace("【ラスト】", "")
                    else:
                        end_time = ""
                    if isinstance(out, str) and out.startswith("【アウト】"):
                        out_time = out.replace("【アウト】", "")
                    else:
                        out_time = ""
                    stay = None
                    extensions = None
                    end_time_disp = end_time
                else:
                    end_time_disp = to_hhmm(end)
            else:
                end_time_disp = to_hhmm(end)

            # extensions: 空あるいはNoneであればNullを返す
            ext_val = None
            if extensions not in ("", None):
                try:
                    ext_val = int(extensions)
                except Exception:
                    ext_val = extensions

            records.append({
                "row_number": r.row_number,
                "table_number": r.table_number,
                "people_count": r.people_count,
                "plan_name": r.plan_name,
                "start_time": start_time_disp,
                "end_time": end_time_disp or "",
                "stay": stay,
                "extensions": ext_val,
                "out_time": out_time or "",
                "status": getattr(r, "status", ""),  # 【修正予定】現在 : 空であれば""を返す → 予定 : 正しくstatusをjsonで表示
                "checked": {
                    "invoiceChecked": bool(getattr(r, "invoiceChecked", False)),
                    "paymentChecked": bool(getattr(r, "paymentChecked", False)),
                }
            })
        from pytz import timezone as pytz_timezone
        jst = pytz_timezone('Asia/Tokyo')
        response = {
            "store": str(request.user.store),
            "date": selected_date.strftime('%Y-%m-%d'), # 年, 月, 日のみselected_dateから取得
            "generated_at": timezone.localtime(timezone.now(), jst).isoformat(),
            "record_count": len(records),
            "records": records
        }
        return JsonResponse(response, safe=False)
    except Exception as e:
        print("API取得時にエラーが発生しました", e)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

@login_required
def mobile_view(request):
    """
    TimeManagementモバイルPWA用レンダリング関数
    """
    return render(request, 'TimeManagement/mobile_view.html')

# viewsのメイン処理
class TimeManagementProcessor:
    def __init__(self, row_id, col_number, value):
        self.row_id = row_id            # 更新行
        self.col_number = col_number    # 更新する列
        self.value = value              # セルの入力値
        self.updated_cells = {}         # 変更点を送信前に一時的に控えるため

    @staticmethod
    def calculate_time_diff(start_time, end_time):
        """開始時間と終了時間の差分を計算（HH:MM形式）"""
        try:
            start_time, end_time = int(start_time), int(end_time)
            start_hour, start_min = divmod(start_time, 100) # 例: 2330 → (23, 30)
            end_hour, end_min = divmod(end_time, 100)       # 例: 0115 → (1, 15)
            start_total_min = start_hour * 60 + start_min
            end_total_min = end_hour * 60 + end_min
            # 日をまたぐ際の処理
            if end_total_min < start_total_min:
                end_total_min += 24 * 60                    # 日をまたぐ場合, +αで24hを加算
            diff_min = end_total_min - start_total_min
            diff_hour, diff_min = divmod(diff_min, 60)
            # "HH:MM"形式で返す
            return f"{diff_hour:02d}:{diff_min:02d}"

        except ValueError:
            return "ValueError"
        
    @staticmethod
    def calculate_count(time_diff, people_count): 
        """
        60分を超えた分から30分ごとの延長回数を計算
        Ex.) [In]2:00 ⇒ [Out]2(回)/人 ※名数=2ならば"4"を返す
        """
        # calculate_count関数に関しては, 時間を分変換して計算
        try:
            hours, minutes = map(int, time_diff.split(":"))
        except ValueError:
            return "ValueError"
        # 次の2つの理由よりpeople_countの例外処理を設ける
        # 1.people_countは文字列として受け取っている  2.入力されていない空の可能性
        try:
            people_count = int(people_count)
        except ValueError:
            people_count = 0
        total_minutes = hours * 60 + minutes

        if total_minutes <= 60: # 60分以下であれば延長回数"0"を返す
            total_counts = 0
        else:
            # 60分超過時の処理
            extention = total_minutes - 60 # 超過時間
            counts = math.ceil(extention / 30) # 30分ごとの切り上げ
            total_counts = counts * int(people_count)
        return total_counts
        
    @staticmethod
    def calculate_LO(start_time, plan_name):
        """ラストオーダー表示時間を計算"""
        def denormalize_time(time):
            total_hours = time * 24
            HH = int(total_hours)
            MM = int((total_hours - HH) * 60)
            return f"【ラスト】{HH:02d}:{MM:02d}"
        try:
            # Consts
            # norm_30 = 0.0208333333333333
            norm_60 = 0.0416666667
            norm_90 = 0.0625000005
            # norm_120 = 0.0833333333333333
            start_time = int(start_time)
            normalized_start = int(start_time / 100) / 24 + (start_time - int(start_time / 100) * 100) / 24 / 60
            if plan_name in ["食べ飲み120m", "スーパー"]:
                LO_90 = normalized_start + norm_90
                return denormalize_time(LO_90)
            elif plan_name == "食べ飲み90m":
                LO_60 = normalized_start + norm_60
                return denormalize_time(LO_60)
            else:
                return ""

        except ValueError:
            return "Value Error"
        

    @staticmethod
    def calculate_OUT(start_time, plan_name):
        """アウト表示時間を計算"""
        def denormalize_time(time):
            total_hours = time * 24
            HH = int(total_hours)
            MM = int((total_hours - HH) * 60)
            return f"【アウト】{HH:02d}:{MM:02d}"
        try:
            # Consts
            # norm_30 = 0.3333333333333333333333333333
            # norm_60 = 0.0416666666666667
            norm_90 = 0.0625000005
            norm_120 = 0.0833333334
            start_time = int(start_time)
            normalized_start = int(start_time / 100) / 24 + (start_time - int(start_time / 100) * 100) / 24 / 60
            if plan_name in ["食べ飲み120m", "スーパー"]:
                OUT_120 = normalized_start + norm_120
                return denormalize_time(OUT_120)
            elif plan_name == "食べ飲み90m":
                OUT_90 = normalized_start + norm_90
                return denormalize_time(OUT_90)
            else:
                return ""

        except ValueError:
            return "Value Error"

    @staticmethod
    def calculate_water(start_time, override_level=0):
        """water列の処理:
        override_levelが0の場合, 開始時間の1時間半後の時刻を返す.
        override_levelが1の場合, 開始時間の2時間30分後の時刻を返す.
        override_levelが2の場合, 開始時間の3時間30分後の時刻を返す.
        ※ その後, override_levelが増えるごとに1時間ずつ延長
        """
        def denormalize_time(time):
            total_hours = time * 24
            HH = int(total_hours)
            MM = int((total_hours - HH) * 60)
            return f"{HH:02d}:{MM:02d}"
        try:
            # Consts
            # norm_30 = 0.3333333333333333333333333333
            # norm_60 = 0.0416666666666667
            norm_90 = 0.0625000005
            # norm_120 = 0.0833333334
            norm_180 = 0.104166666666667
            start_time = int(start_time)
            # 追加する延長時間：override_level * 1時間 (1/24)
            increment = override_level / 24.0
            start_time = int(start_time)
            # 24hを[0, 1]の正規化  Ex.)1200 = 12:00 ⇒ 0.5
            normalized_start = int(start_time / 100) / 24 + (start_time - int(start_time / 100) * 100) / (24 * 60)
            water = normalized_start + norm_90 + increment
            return denormalize_time(water)
        except ValueError:
            return "Value Error"
        
    @staticmethod
    def calculate_seat_limit(end_time, plan_name):
        """
        レモンプランの表示席時間を計算. 30分後を5分刻みで切り上げる.
        Ex.) OUT = "1402"(14:02) ⇒ [OUT]14:05
        """
        def minutes_to_time(total_minutes):
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours:02d}:{minutes:02d}"
        
        try:
            # calculate_count関数同様, 正規化をせずに分変換して計算
            end_time = int(end_time)
            hours = end_time // 100
            minutes = end_time % 100
            total_minutes = hours * 60 + minutes + 30 # 終了時間の30分後が席時間

            if plan_name == "レモン":
                rounded_minutes = math.ceil(total_minutes / 5) * 5
                return minutes_to_time(rounded_minutes)
            else:
                return ""
        except ValueError:
            return "Value Error"



    def process_column_logic(self, request):
        """列ごとの処理を実行"""
        # 1列目(プラン名)更新時<1>
        if self.col_number == 1:
            plan_name = request.POST.get('plan_name', "")
            people_count = request.POST.get('people_count', "").strip()
            start_time = request.POST.get('start_time', "") # .strip()  # 開始時間を取得
            end_time = request.POST.get('end_time', "")
            water_override = request.POST.get('water_override', "0").lower()  # "0"がデフォルト
            if start_time.strip():
                # water_overrideを取得
                override_level = int(water_override)
                self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
            else:                
                self.updated_cells[8] = ""

            if start_time and self.value in ["食べ飲み90m", "食べ飲み120m", "スーパー"]:
                self.updated_cells[6] = self.calculate_LO(start_time, self.value)  # L.O.時間を更新
                self.updated_cells[7] = self.calculate_OUT(start_time, self.value)
            elif start_time and self.value == "レモン":
                if end_time:
                    self.updated_cells[6] = self.calculate_time_diff(start_time, end_time)
                    self.updated_cells[7] = self.calculate_count(self.calculate_time_diff(start_time, end_time), people_count)
                    self.updated_cells[10] = self.calculate_seat_limit(end_time, self.value)
                else:
                    self.updated_cells[6] = ""
                    self.updated_cells[7] = ""
                    self.updated_cells[10] = ""
            else:
                self.updated_cells[6] = ""
                self.updated_cells[7] = ""
                self.updated_cells[10] = ""

            
                    
        # 名数カラム更新時<3>
        elif self.col_number == 3:
            plan_name = request.POST.get('plan_name', "")
            people_count = request.POST.get('people_count', "").strip()
            start_time = request.POST.get('start_time', "")# .strip()  # 開始時間を取得
            end_time = request.POST.get('end_time', "")
            water_override = request.POST.get('water_override', "0").lower()  # "0"がデフォルト
            if start_time.strip():
                    # water_overrideをPOSTデータから取得
                    override_level = int(water_override)
                    self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
            else:
                
                self.updated_cells[8] = ""

            if start_time and plan_name in ["食べ飲み90m", "食べ飲み120m", "スーパー"]:
                self.updated_cells[6] = self.calculate_LO(start_time, plan_name)  # L.O.時間を更新
                self.updated_cells[7] = self.calculate_OUT(start_time, plan_name)
            elif start_time and plan_name == "レモン":
                if end_time:
                    self.updated_cells[6] = self.calculate_time_diff(start_time, end_time)
                    self.updated_cells[7] = self.calculate_count(self.calculate_time_diff(start_time, end_time), self.value)
                    self.updated_cells[10] = self.calculate_seat_limit(end_time, plan_name)
                else:
                    self.updated_cells[6] = ""
                    self.updated_cells[7] = ""
                    self.updated_cells[10] = ""
            else:
                self.updated_cells[6] = ""
                self.updated_cells[7] = ""
                self.updated_cells[10] = ""
                
        # startカラム更新時<4>
        elif self.col_number == 4 and self.value.strip():  # 入力値が空でない場合のみ動作
            plan_name = request.POST.get('plan_name', "")
            people_count = request.POST.get('people_count', "").strip()
            start_time = request.POST.get('start_time', "")
            end_time = request.POST.get('end_time', "")
            water_override = request.POST.get('water_override', "0").lower()  # "0"がデフォルト
            if start_time.strip():
                    # water_overrideを取得
                    override_level = int(water_override)
                    self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
            else:
                self.updated_cells[8] = ""

            if start_time and plan_name in ["食べ飲み90m", "食べ飲み120m", "スーパー"]:
                self.updated_cells[6] = self.calculate_LO(self.value, plan_name) 
                self.updated_cells[7] = self.calculate_OUT(self.value, plan_name)
            elif start_time and plan_name == "レモン":
                if end_time:
                    self.updated_cells[6] = self.calculate_time_diff(self.value, end_time)
                    self.updated_cells[7] = self.calculate_count(self.calculate_time_diff(self.value, end_time), people_count)
                    self.updated_cells[10] = self.calculate_seat_limit(end_time, plan_name)
                else:
                    self.updated_cells[6] = ""
                    self.updated_cells[7] = ""
                    self.updated_cells[10] = ""
            else:
                self.updated_cells[6] = ""
                self.updated_cells[7] = ""
                self.updated_cells[10] = ""

        # endカラム更新 ⇒ plan_name == "レモン"であれば updated_cells[7] に"time_diff"の計算結果を表示,  時間制プランの場合は席時間を表示<5>
        elif self.col_number == 5:
            plan_name = request.POST.get('plan_name', "")
            people_count = request.POST.get('people_count', "").strip()
            start_time = request.POST.get('start_time', "")
            end_time = request.POST.get('end_time', "")
            water_override = request.POST.get('water_override', "0").lower()  # "0"がデフォルト
            if start_time.strip():
                    # water_overrideを取得
                    override_level = int(water_override)
                    self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
            else:                
                self.updated_cells[8] = ""

            if start_time and plan_name in ["食べ飲み90m", "食べ飲み120m", "スーパー"]:
                self.updated_cells[6] = self.calculate_LO(start_time, plan_name)
                self.updated_cells[7] = self.calculate_OUT(start_time, plan_name)
            elif start_time and plan_name == "レモン":
                if end_time:
                    self.updated_cells[6] = self.calculate_time_diff(start_time, self.value)
                    self.updated_cells[7] = self.calculate_count(self.calculate_time_diff(start_time, self.value), people_count)
                    self.updated_cells[10] = self.calculate_seat_limit(self.value, plan_name)
                else:
                    self.updated_cells[6] = ""
                    self.updated_cells[7] = ""
                    self.updated_cells[10] = ""
            else:
                self.updated_cells[6] = ""
                self.updated_cells[7] = ""
                self.updated_cells[10] = ""

        elif self.col_number == 9:
                start_time = request.POST.get('start_time', "").strip()
                water_override = request.POST.get('water_override', "0").lower()  # "0"がデフォルト
                # water_overrideを取得(int)
                try:
                    override_level = int(request.POST.get('water_override', "0"))
                except ValueError:
                    override_level = 0
                print("Water override level:", override_level)  # デバッグ用
                if start_time:
                    self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
                else:
                    self.updated_cells[8] = ""


        else:
            plan_name = request.POST.get('plan_name', "")
            people_count = request.POST.get('people_count', "").strip()
            start_time = request.POST.get('start_time', "")
            end_time = request.POST.get('end_time', "")
            water_override = request.POST.get('water_override', "0").lower()  # "0"がデフォルト
            if start_time.strip():
                override_level = int(water_override)
                self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
            else:                
                self.updated_cells[8] = ""

            if start_time and plan_name in ["食べ飲み90m", "食べ飲み120m", "スーパー"]:
                self.updated_cells[6] = self.calculate_LO(start_time, plan_name)
                self.updated_cells[7] =self.calculate_OUT(start_time, plan_name)
            elif start_time and plan_name == "レモン":
                if end_time:
                    self.updated_cells[6] = self.calculate_time_diff(start_time, end_time)
                    self.updated_cells[7] = self.calculate_count(self.calculate_time_diff(start_time, end_time), people_count)
                    self.updated_cells[10] = self.calculate_seat_limit(end_time, plan_name)
                else:
                    self.updated_cells[6] = ""
                    self.updated_cells[7] = ""
                    self.updated_cells[10] = ""
            else:
                self.updated_cells[6] = ""
                self.updated_cells[7] = ""
                self.updated_cells[10] = ""

    def get_updated_cells(self):
        """更新されたセルを返す"""
        return self.updated_cells

@login_required
def update_cell(request):
    """
    1. セルの更新
    2. チェックボックスの更新

    の2通りに分けて処理をする.

    ※ チェックボックスを個別で更新するとデータベースに反映されなかったため
    """
    if request.method == 'POST':
        # 店舗情報が設定の確認
        if not request.user.store:
            return JsonResponse({'success': False, 'error': '店舗情報が設定されていません。'}, status=400)
    if request.method == 'POST':
        row_id = request.POST.get('row_id')
        col_number = request.POST.get('col_number')
        value = request.POST.get('value', "").strip()
        try:
            row_id = int(row_id)
            # もし複数更新の場合は、col_number は "checkboxes" になる
            if col_number != 'checkboxes':
                col_number = int(col_number)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid row_id or col_number'}, status=400)

        selected_date_str = request.POST.get('selected_date')
        try:
            record_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            record_date = date.today()

        record, created = TimeManagementRecord.objects.get_or_create(date=record_date, row_number=row_id, store=request.user.store)

        # データベースに保存する内容
        if col_number == 'checkboxes':
            # 複数のチェックボックスの状態を更新
            record.col11 = 'true' if request.POST.get('col11', 'false').lower() == 'true' else '' # なぜか, 11,12列目のみリロード時不具合が起こるので, 空白は強制false
            record.col12 = 'true' if request.POST.get('col12', 'false').lower() == 'true' else ''
            record.invoiceChecked = (request.POST.get('col13', 'false').lower() == 'true')
            record.paymentChecked = (request.POST.get('col14', 'false').lower() == 'true')
        else:
            # チェックボックス以外は通常更新
            if col_number == 1:
                record.plan_name = value
                if value != "レモン":
                    record.out_time = ""
                    updated_cells = {'10': ""}  # 10列目クリア
                else:
                    updated_cells = {}
            elif col_number == 2:
                record.table_number = value
            elif col_number == 3:
                try:
                    record.people_count = int(value)
                except ValueError:
                    record.people_count = None
            elif col_number == 4:
                record.start_time = value
                if not value:
                    record.stay = ""
                    record.extensions = ""
                    record.water_time = ""
                    if record.plan_name != "単品":
                        record.out_time = ""
                else:
                    save_fields = ['start_time']
            elif col_number == 5:
                record.end_time = value
            elif col_number == 6:
                record.stay = value
            elif col_number == 7:
                record.extensions = value
            elif col_number == 8:
                record.water_time = value
            elif col_number == 9:
                try:
                    record.water_override = int(value)
                except ValueError:
                    record.water_override = 0
                record.water_counts = value
            elif col_number == 10:
                record.out_time = value
            elif col_number == 16:
                record.memo = value

        record.save()

        processor = TimeManagementProcessor(row_id, col_number, value)
        processor.process_column_logic(request)
        updated_cells = processor.get_updated_cells()

        # 計算結果を反映
        if col_number == 1 and value != "レモン":
            updated_cells['10'] = ""
        if '6' in updated_cells:
            record.stay = updated_cells['6']
        if '7' in updated_cells:
            record.extensions = updated_cells['7']
        if '8' in updated_cells:
            record.water_time = updated_cells['8']
        if '10' in updated_cells:
            if record.plan_name != "単品":  # 単品の処理は修正予定
                record.out_time = updated_cells['10']
        else:
            if record.plan_name != "単品":  # ★同じく修正予定
                record.out_time = "" if record.plan_name != "レモン" or not record.end_time else record.out_time

        # stay, extensions, water_time, out_time をまとめて保存
        record.save(update_fields=['stay', 'extensions', 'water_time', 'out_time'])

        return JsonResponse({'success': True, 'updated_cells': updated_cells})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)