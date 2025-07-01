from django.shortcuts import render
from django.http import JsonResponse
from TimeManagement.models import TimeManagementRecord
from django.contrib.auth.decorators import login_required


from typing import Optional


# table_view関数
from datetime import date

# calculate_count関数 "math.ceil()"
import math

from datetime import date, datetime



# メタ情報をまとめるデータクラスの定義


from dataclasses import dataclass
@dataclass
class Plan:
    """
    【各プランメタデータのクラス】
    """
    name: str
    timed_lo_min: Optional[int]
    timed_out_min: Optional[int]
    auto_extend: bool = False

    def has_lo(self) -> bool:
        return self.timed_lo_min is not None

    def has_out(self) -> bool:
        return self.timed_out_min is not None

    def has_auto_extend(self) -> bool:
        return self.auto_extend
    


PLAN_REGISTRY: dict[str, Plan] = {
    "レモン": Plan(
        name = "レモン",
        timed_lo_min = None,
        timed_out_min = None,
        auto_extend = True,
    ),
    "食べ飲み90m": Plan(
        name = "食べ飲み90m",
        timed_lo_min = 60,
        timed_out_min = 90,
        auto_extend = False,
    ),
    "食べ飲み120m": Plan(
        name = "食べ飲み120m",
        timed_lo_min = 90,
        timed_out_min = 120,
        auto_extend = False,
    ),
    "スーパー90m": Plan(
        name = "スーパー90m",
        timed_lo_min = 60,
        timed_out_min = 90,
        auto_extend = False,
    ),
    "スーパー120m": Plan(
        name = "スーパー120m",
        timed_lo_min = 90,
        timed_out_min = 120,
        auto_extend = False,
    ),
    "単品": Plan(
        name = "単品",
        timed_lo_min = None,
        timed_out_min = None,
        auto_extend = False,
    ),
    "エンドレス": Plan(
        name = "エンドレス",
        timed_lo_min = None,
        timed_out_min = None,
        auto_extend = False,
        # unlimited_label = True,  # 無制限ラベルのフラグ
    ),
}



# == 時間計算クラス ================================================================
import math
class time_calculator:
    """
    【滞在時間計算及び可能滞在時間の計算を行うクラス】\n
    具体的な計算値
    - stay: 滞在時間
    - extention: 30分ごとの自動延長回数
    - 
    
    """
    @staticmethod
    def normalize_time(time: int) -> float:
        """
        時間を正規化する関数\n
        24h表記の時間を[0, 1]の範囲に正規化する.\n
        [In] 1200 ⇒ [Out] 0.5
        """
        try:
            if not isinstance(time, int) or time < 0:
                return 0.0
            time = int(time)
            # 24hを[0, 1]の正規化  Ex.)1200 = 12:00 ⇒ 0.5
            normalized_start = int(time / 100) / 24 + (time - int(time / 100) * 100) / (24 * 60)
            return normalized_start

        except ValueError:
            # 例外処理: intに変換できない場合は0.0を返す
            return 0.0
        

    @staticmethod
    def to_hhmm(val):
            """
            start_time(int4桁)をhh:mm表記に変換する関数\n
            [In]  1200\n
            [Out] 12:00
            """            
            if not val or not str(val).isdigit():
                return ""
            val = int(val)
            h = val // 100
            m = val % 100
            return f"{h:02d}{m:02d}"


    @staticmethod
    def calculate_time_diff(start_time, end_time) -> str:
        """
        開始時間と終了時間の差分を計算する関数
        [In] 1200, 1300 ⇒ [Out] 01:00
        """
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
    def calculate_count(time_diff: str, people_count: str) -> int:
        """
        60分を超えた分から30分ごとの延長回数を計算する関数\n
        Ex.) [In]2:00 ⇒ [Out]2(回)/人 ※名数=2ならば"4"を返す
        """
        try:
            people_count = int(people_count)
            hours, minutes = map(int, time_diff.split(":"))
            total_minutes = hours * 60 + minutes

            if total_minutes <= 60:
                return 0

            extention = total_minutes - 60  # 超過時間
            counts = math.ceil(extention / 30)  # 30分ごとの切り上げ
            return counts * people_count

        except ValueError:
            return "ValueError"


    @staticmethod
    def calculate_LO(start_time, timed_lo_min) -> str:
        """
        ラストオーダーの時間を計算する関数
        [In] (1200, 90) ⇒ [Out] 1330
        """
        def denormalize_time_to_hhmm(time: float) -> str:
            total_hours = time * 24
            HH = int(total_hours)
            MM = int(round((total_hours - HH) * 60))
            if MM == 60:
                HH += 1
                MM = 0
            return f"{HH:02d}{MM:02d}"
        try:
            start_time = int(start_time)
            norm_lo = timed_lo_min / (24 * 60)
            normalized_start = time_calculator.normalize_time(start_time)
            LO_time = normalized_start + norm_lo
            return denormalize_time_to_hhmm(LO_time)
        except ValueError:
            return "Value Error"

    @staticmethod
    def calculate_OUT(start_time: int, timed_out_min: int) -> str:
        """
        アウトの時間を計算する関数
        [In] (1200, 90) ⇒ [Out] 1300
        """
        def denormalize_time_to_hhmm(time: float) -> str:
            total_hours = time * 24
            HH = int(total_hours)
            MM = int(round((total_hours - HH) * 60))
            if MM == 60:
                HH += 1
                MM = 0
            return f"{HH:02d}{MM:02d}"

        try:
            start_time = int(start_time)
            norm_out = timed_out_min / (24 * 60)
            normalized_start = time_calculator.normalize_time(start_time)
            OUT_time = normalized_start + norm_out
            return denormalize_time_to_hhmm(OUT_time)
        except ValueError:
            return "Value Error"
        
    
    @staticmethod
    def calculate_water(start_time, override_level=0) -> str:
        """
        water列の処理:
        override_levelが0の場合, 開始時間の1時間半後の時刻を返す.
        override_levelが1の場合, 開始時間の2時間30分後の時刻を返す.
        override_levelが2の場合, 開始時間の3時間30分後の時刻を返す.
        ※ その後, override_levelが増えるごとに1時間ずつ延長
        """
        def denormalize_time(time: float) -> str:
            total_hours = time * 24
            HH = int(total_hours)
            MM = int(round((total_hours - HH) * 60))
            if MM == 60:
                HH += 1
                MM = 0
            return f"{HH:02d}:{MM:02d}"
        try:
            start_time = int(start_time)
            # 90分の正規化は直接割る
            norm_90 = 90 / (24 * 60)
            increment = override_level / 24.0  # 1時間ごとの正規化
            normalized_start = time_calculator.normalize_time(start_time)
            water_time = normalized_start + norm_90 + increment
            return denormalize_time(water_time)

        except ValueError:
            return "Value Error"
        

    @staticmethod
    def calculate_seat_limit(end_time) -> str:
        """
        自動延長プランの表示席時間を計算. 30分後を5分刻みで切り上げる.\n
        [In] end_time = "1402"(14:02) ⇒ [OUT]14:35
        """
        def minutes_to_time(total_minutes):
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours:02d}:{minutes:02d}"
        
        try:
            end_time = int(end_time)
            hours = end_time // 100
            minutes = end_time % 100
            total_minutes = hours * 60 + minutes + 30  # 終了時間の30分後が席時間

            # plan_nameが"レモン"またはauto_extendプランのみ席時間を返す
            rounded_minutes = math.ceil(total_minutes / 5) * 5
            return minutes_to_time(rounded_minutes)
        except ValueError:
            return "Value Error"
    
    @staticmethod
    def seat_limit_to_hhmm(end_time) -> str:
        """
        自動延長プランの席時間を4桁数値(HHMM)で返す
        [In] end_time = "1402" ⇒ [Out] "1435"
        """
        try:
            end_time = int(end_time)
            hours = end_time // 100
            minutes = end_time % 100
            total_minutes = hours * 60 + minutes + 30 # 30分後席時間
            rounded_minutes = math.ceil(total_minutes / 5) * 5
            hh = rounded_minutes // 60
            mm = rounded_minutes % 60
            return f"{hh:02d}{mm:02d}"
        except ValueError:
            return ""


########################################## RF中 ##########################################

# == ビュー関数 ================================================================

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
        plan_name = record.plan_name
        plan = PLAN_REGISTRY.get(record.plan_name.strip(), PLAN_REGISTRY['単品'])
        record.calculated_col6 = record.calculated_col7 = record.calculated_col10 = ""
        record.calculated_water_time = ""
        stay = extensions = seat = ""

        if record.start_time:
            # 自動延長プランの場合
            if plan and plan.has_auto_extend() and record.end_time:
                stay = time_calculator.calculate_time_diff(record.start_time, record.end_time)
                extensions = time_calculator.calculate_count(stay, str(record.people_count or 0))
                # DB格納値は4桁数値
                seat = time_calculator.seat_limit_to_hhmm(record.end_time)
                # 表示用はHH:MM
                record.calculated_col10 = time_calculator.calculate_seat_limit(record.end_time)

                record.calculated_col6 = stay
                record.calculated_col7 = extensions

                # **DBに保存**
                record.stay = stay
                record.extensions = extensions
                record.out_time = seat  # 4桁数値で保存
            # 時間制プランの場合
            elif plan and plan.has_lo() and plan.has_out():
                lo  = time_calculator.calculate_LO(record.start_time, plan.timed_lo_min)
                out = time_calculator.calculate_OUT(record.start_time, plan.timed_out_min)
                
                # DB格納値は4桁数値
                record.calculated_col6 = lo
                record.calculated_col7 = out
                record.calculated_col10 = out # 表示用アウト時間
                record.stay = lo
                record.extensions = out
                record.out_time = out
                # record.out_time   = out
                # record.calculated_col10 = ""  # 時間制プランでは席時間は表示しない
                # record.out_time = ""
                
            else:
                # Clear for other plans
                record.stay = record.extensions = record.out_time = ""

            save_fields = ['stay', 'extensions']
            if plan and (plan.has_out() or plan.has_auto_extend()): # 時間制or自動延長の場合, out_timeも保存
                save_fields.append('out_time')
            if record.start_time: # start_timeがある場合のみwater_timeを計算
                save_fields.append('water_time')
            record.save(update_fields=save_fields)
            record.water_time = time_calculator.calculate_water(record.start_time, override_level=record.water_override)
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
                if not val or not str(val).isdigit():
                    return ""
                val = int(val)
                h = val // 100
                m = val % 100
                return f"{h:02d}{m:02d}"

            # start_time_disp = to_hhmm(start)
            start_time_disp = start or ""


            plan_meta = PLAN_REGISTRY.get(plan)
            end_time_disp = ""
            out_time_disp = ""

            if start:
                # 自動延長プランの場合
                if plan_meta and plan_meta.has_auto_extend() and r.end_time:
                    stay = time_calculator.calculate_time_diff(start, end)
                    extensions = time_calculator.calculate_count(stay, str(people or 0))
                    out_time_disp = time_calculator.calculate_seat_limit(end)
                    end_time_disp = end or ""
                # 時間制プランの場合
                elif plan_meta and plan_meta.has_lo() and plan_meta.has_out():
                    # ここで4桁時刻をセット
                    stay = time_calculator.calculate_LO(r.start_time, plan_meta.timed_lo_min)
                    extensions = time_calculator.calculate_OUT(r.start_time, plan_meta.timed_out_min)
                    end_time_disp = stay
                    out_time_disp = extensions
                else:
                    end_time_disp = to_hhmm(end)
            else:
                end_time_disp = to_hhmm(end)

            # extensions: 空あるいはNoneであればNullを返す
            ext_val = None
            if extensions not in ("", None):  # 0も通す
                try:
                    ext_val = int(extensions)
                except Exception:
                    ext_val = extensions
            elif extensions == 0 or extensions == "0":
                ext_val = 0

            records.append({
                "row_number": r.row_number,
                "table_number": r.table_number,
                "people_count": r.people_count,
                "plan_name": r.plan_name,
                "start_time": start_time_disp,
                "end_time": end_time_disp or "",
                "stay": stay,
                "extensions": ext_val,
                "out_time": out_time_disp or "",
                "status": getattr(r, "status", ""),
                "checked": {
                    "invoiceChecked": bool(getattr(r, "invoiceChecked", False)),
                    "paymentChecked": bool(getattr(r, "paymentChecked", False)),
                }
            })
        from pytz import timezone as pytz_timezone
        jst = pytz_timezone('Asia/Tokyo')
        response = {
            "store": str(request.user.store),
            "date": selected_date.strftime('%Y-%m-%d'),
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
    def __init__(self, record, row_id, col_number, value):
        self.row_id = row_id            # 更新行
        self.col_number = col_number    # 更新する列
        self.value = value   
        self.record = record           # セルの入力値
        self.updated_cells = {}         # 変更点を送信前に一時的に控えるため

    @staticmethod
    def calculate_time_diff(start_time, end_time):
        return time_calculator.calculate_time_diff(start_time, end_time)

    @staticmethod
    def calculate_count(time_diff, people_count):
        return time_calculator.calculate_count(time_diff, people_count)

    @staticmethod
    def calculate_LO(start_time, timed_lo_min):
        return time_calculator.calculate_LO(start_time, timed_lo_min)

    @staticmethod
    def calculate_OUT(start_time, timed_out_min):
        return time_calculator.calculate_OUT(start_time, timed_out_min)

    @staticmethod
    def calculate_water(start_time, override_level=0):
        return time_calculator.calculate_water(start_time, override_level)

    @staticmethod
    def calculate_seat_limit(end_time, ):
        return time_calculator.calculate_seat_limit(end_time)

    def get_updated_cells(self):
        return self.updated_cells

    def process_column_logic(self, request):
        plan_name = request.POST.get('plan_name', "")
        people_count = request.POST.get('people_count', "").strip()
        start_time = request.POST.get('start_time', "")
        end_time = request.POST.get('end_time', "")
        water_override = request.POST.get('water_override', "0").lower()
        # PLAN_REGISTRY からメタデータを取得
        plan = PLAN_REGISTRY.get(self.record.plan_name.strip(), PLAN_REGISTRY['単品'])
        if plan is None:
            # 例えば何も計算せずに戻る or すべてクリア
            self.updated_cells = {
                '6': '', '7': '', '8': '', '10': ''
            }
            return
        # 1列目(プラン名)更新時<1>
        if self.col_number == 1:
            plan_name = request.POST.get('plan_name', "")
            people_count = request.POST.get('people_count', "").strip()
            start_time = request.POST.get('start_time', "")
            end_time = request.POST.get('end_time', "")
            water_override = request.POST.get('water_override', "0").lower()
            if start_time.strip():
                override_level = int(water_override)
                self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
            else:
                self.updated_cells[8] = ""

            if start_time and plan.has_lo() and plan.has_out():
                self.updated_cells[6] = self.calculate_LO(start_time, plan.timed_lo_min)
                self.updated_cells[7] = self.calculate_OUT(start_time, plan.timed_out_min)
                self.updated_cells[10] = self.calculate_OUT(start_time, plan.timed_out_min)
            elif start_time and plan.has_auto_extend():
                if end_time:
                    self.updated_cells[6] = self.calculate_time_diff(start_time, end_time)
                    self.updated_cells[7] = self.calculate_count(self.calculate_time_diff(start_time, end_time), people_count)
                    self.updated_cells[10] = self.calculate_seat_limit(end_time)
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
            start_time = request.POST.get('start_time', "")
            end_time = request.POST.get('end_time', "")
            water_override = request.POST.get('water_override', "0").lower()
            if start_time.strip():
                # water_overrideをPOSTから取得し, 整数変換
                override_level = int(water_override) # なんでだっけ
                self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
            else:
                self.updated_cells[8] = ""

            if start_time and plan and plan.has_lo() and plan.has_out():
                self.updated_cells[6] = self.calculate_LO(start_time, plan.timed_lo_min)
                self.updated_cells[7] = self.calculate_OUT(start_time, plan.timed_out_min)
                self.updated_cells[10] = self.calculate_OUT(start_time, plan.timed_out_min)
            elif start_time and plan.has_auto_extend():
                if end_time:
                    self.updated_cells[6] = self.calculate_time_diff(start_time, end_time)
                    self.updated_cells[7] = self.calculate_count(self.calculate_time_diff(start_time, end_time), self.value)
                    self.updated_cells[10] = self.calculate_seat_limit(end_time)
                else:
                    self.updated_cells[6] = ""
                    self.updated_cells[7] = ""
                    self.updated_cells[10] = ""
            else:
                self.updated_cells[6] = ""
                self.updated_cells[7] = ""
                self.updated_cells[10] = ""

        # startカラム更新時<4>
        elif self.col_number == 4 and self.value.strip(): # 入力値が空でないときのみ
            plan_name = request.POST.get('plan_name', "")
            people_count = request.POST.get('people_count', "").strip()
            start_time = request.POST.get('start_time', "")
            end_time = request.POST.get('end_time', "")
            water_override = request.POST.get('water_override', "0").lower()
            if start_time.strip():
                override_level = int(water_override)
                self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
            else:
                self.updated_cells[8] = ""

            if start_time and plan and plan.has_lo() and plan.has_out():
                self.updated_cells[6] = self.calculate_LO(self.value, plan.timed_lo_min)
                self.updated_cells[7] = self.calculate_OUT(self.value, plan.timed_out_min)
                self.updated_cells[10] = self.calculate_OUT(start_time, plan.timed_out_min)
            elif start_time and plan.has_auto_extend():
                if end_time:
                    self.updated_cells[6] = self.calculate_time_diff(self.value, end_time)
                    self.updated_cells[7] = self.calculate_count(self.calculate_time_diff(self.value, end_time), people_count)
                    self.updated_cells[10] = self.calculate_seat_limit(end_time)
                else:
                    self.updated_cells[6] = ""
                    self.updated_cells[7] = ""
                    self.updated_cells[10] = ""
            else:
                self.updated_cells[6] = ""
                self.updated_cells[7] = ""
                self.updated_cells[10] = ""

        # endカラム更新時<5>
        elif self.col_number == 5:
            plan_name = request.POST.get('plan_name', "")
            people_count = request.POST.get('people_count', "").strip()
            start_time = request.POST.get('start_time', "")
            end_time = request.POST.get('end_time', "")
            water_override = request.POST.get('water_override', "0").lower()
            if start_time.strip():
                override_level = int(water_override)
                self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
            else:
                self.updated_cells[8] = ""

            if start_time and plan and plan.has_lo() and plan.has_out():
                self.updated_cells[6] = self.calculate_LO(start_time, plan.timed_lo_min)
                self.updated_cells[7] = self.calculate_OUT(start_time, plan.timed_out_min)
                self.updated_cells[10] = self.calculate_OUT(start_time, plan.timed_out_min)
            elif start_time and plan.has_auto_extend():
                if end_time:
                    self.updated_cells[6] = self.calculate_time_diff(start_time, self.value)
                    self.updated_cells[7] = self.calculate_count(self.calculate_time_diff(start_time, self.value), people_count)
                    self.updated_cells[10] = self.calculate_seat_limit(self.value)
                else:
                    self.updated_cells[6] = ""
                    self.updated_cells[7] = ""
                    self.updated_cells[10] = ""
            else:
                self.updated_cells[6] = ""
                self.updated_cells[7] = ""
                self.updated_cells[10] = ""


        # waterボタン更新時<9>
        elif self.col_number == 9:
            start_time = request.POST.get('start_time', "").strip()
            water_override = request.POST.get('water_override', "0").lower()
            try:
                override_level = int(request.POST.get('water_override', "0"))
            except ValueError:
                override_level = 0
            if start_time:
                self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
            else:
                self.updated_cells[8] = ""

        else:
            plan_name = request.POST.get('plan_name', "")
            people_count = request.POST.get('people_count', "").strip()
            start_time = request.POST.get('start_time', "")
            end_time = request.POST.get('end_time', "")
            water_override = request.POST.get('water_override', "0").lower()
            if start_time.strip():
                override_level = int(water_override)
                self.updated_cells[8] = self.calculate_water(start_time, override_level=override_level)
            else:
                self.updated_cells[8] = ""

            if start_time and plan and plan.has_lo() and plan.has_out():
                self.updated_cells[6] = self.calculate_LO(start_time, plan.timed_lo_min)
                self.updated_cells[7] = self.calculate_OUT(start_time, plan.timed_out_min)
                self.updated_cells[10] = self.calculate_OUT(start_time, plan.timed_out_min)
            elif start_time and plan.has_auto_extend():
                if end_time:
                    self.updated_cells[6] = self.calculate_time_diff(start_time, end_time)
                    self.updated_cells[7] = self.calculate_count(self.calculate_time_diff(start_time, end_time), people_count)
                    self.updated_cells[10] = self.calculate_seat_limit(end_time)
                else:
                    self.updated_cells[6] = ""
                    self.updated_cells[7] = ""
                    self.updated_cells[10] = ""
            else:
                self.updated_cells[6] = ""
                self.updated_cells[7] = ""
                self.updated_cells[10] = ""


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
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
        row_id      = request.POST.get('row_id')
        col_number  = request.POST.get('col_number')
        plan_name   = request.POST.get('plan_name', "")
        plan        = PLAN_REGISTRY.get(plan_name)

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
        plan = PLAN_REGISTRY.get(
            record.plan_name.strip(),
            PLAN_REGISTRY['単品']
        )

        # データベースに保存する内容
        if col_number == 'checkboxes':
            # 複数のチェックボックスの状態を更新
            record.col11 = 'true' if request.POST.get('col11', 'false').lower() == 'true' else ''
            record.col12 = 'true' if request.POST.get('col12', 'false').lower() == 'true' else ''
            record.invoiceChecked = (request.POST.get('col13', 'false').lower() == 'true')
            record.paymentChecked = (request.POST.get('col14', 'false').lower() == 'true')
        else:
            # チェックボックス以外は通常更新
            plan_name = request.POST.get('plan_name', "")
            plan = PLAN_REGISTRY.get(record.plan_name.strip(),PLAN_REGISTRY['単品'])
            if col_number == 1:
                record.plan_name = value
                record.save(update_fields=['plan_name'])
                plan = PLAN_REGISTRY.get(
                    record.plan_name.strip(),
                    PLAN_REGISTRY['単品']
                )
                if plan.has_lo() and plan.has_out():
                    record.out_time = ""
                    updated_cells = {'10': ""} # 再確認！時間制プランでも表示予定
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
                clean = value.replace(":", "")
                record.start_time = clean
                if not value:
                    record.stay = ""
                    record.extensions = ""
                    record.water_time = ""
                    record.out_time = ""
                else:
                    record.start_time = value
                    # save_fields = ['start_time']
            elif col_number == 5:
                clean = value.replace(":", "")
                if plan.has_lo() and plan.has_out():
                    # 時間制プランならLO時刻をend_timeに保存
                    lo_time = time_calculator.calculate_LO(record.start_time, plan.timed_lo_min)
                    record.end_time = lo_time 
                else:
                    # それ以外（自動延長プラン含む）は入力値を保存
                    record.end_time = clean

                # 自動延長プランならseat時間もout_timeに保存
                if plan.has_auto_extend():
                    seat = time_calculator.seat_limit_to_hhmm(record.end_time)
                    record.out_time = seat
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

        processor = TimeManagementProcessor(record, row_id, col_number, value)
        processor.process_column_logic(request)
        updated_cells = processor.get_updated_cells()

        # 計算結果を反映
        if col_number == 1 and plan and not plan.has_auto_extend(): # 自動延長プランでない場合
            updated_cells['10'] = record.out_time
        if '6' in updated_cells:
            record.stay = updated_cells['6']
        if '7' in updated_cells:
            record.extensions = updated_cells['7']
        if '8' in updated_cells:
            record.water_time = updated_cells['8']
        if '10' in updated_cells:
            if not (plan.has_auto_extend() and plan.has_lo() and plan.has_out()): # すべての時間制を持たないプランの場合
                record.out_time = updated_cells['10']
        else:
            if not (plan.has_auto_extend() and plan.has_lo() and plan.has_out()): # すべての時間制を持たないプランの場合
                record.out_time = "" if not(plan.has_auto_extend()) or not record.end_time else record.out_time

        record.save(update_fields=['stay', 'extensions', 'water_time', 'out_time'])

        return JsonResponse({'success': True, 'updated_cells': updated_cells})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

