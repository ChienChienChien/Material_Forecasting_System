from utils import Util
import getlib
import datetime
import calendar
import pandas as pd
from dglib.log.nlogE import Elog
from dglib.db.dbutils import DB

class Param:

    def __init__(self):
        self.todaytime = datetime.datetime.today()
        self.today = datetime.date.today()
        self.start_date = self.today + datetime.timedelta(days=-25)
        self.end_date = getlib.get_end_date()
        self.material_list = getlib.get_material_list()
        self.self_material_list = getlib.get_self_material_list()
        self.start_month = format(self.start_date, '%Y-%m')
        self.end_month = format(self.end_date, '%Y-%m')
        self.gen_month_list()
        self.gen_date_list()
        self.gen_month_date_dict()
        self.gen_month_week_date_dict()

    def gen_month_list(self):
        '''
        生成月份清單
        '''
        self.month_list = []
        tmp_month = self.start_month
        while True:
            self.month_list.append(tmp_month)
            tmp_month = Util.next_month(tmp_month)
            if tmp_month == self.end_month:
                self.month_list.append(tmp_month)
                break

    def gen_date_list(self):
        '''
        生成日期清單
        '''
        interval_days = (self.end_date-self.start_date).days
        self.date_list = [self.start_date + datetime.timedelta(days=i) for i in range(interval_days+1)]

    def gen_month_date_dict(self):
        '''
        生成月份對應日期
        '''
        self.month_date_dict = {}
        for month in self.month_list:
            tmp = []
            for date in self.date_list:
                if month == format(date, '%Y-%m'):
                    tmp.append(date)
            self.month_date_dict[month] = tmp

    def gen_month_week_date_dict(self):
        '''
        生成月份-周別-日期的對應字典
        '''
        self.month_week_daterange = getlib.get_week_date_map()
        self.month_week_date_dict = {}
        for month, week_daterange in self.month_week_daterange.items():
            self.month_week_date_dict[month] = {}
            for weekid, daterange in week_daterange.items():
                start_date = daterange.get('start_date')
                end_date = daterange.get('end_date')
                interval_days = (end_date-start_date).days
                tmp = [start_date + datetime.timedelta(days=i) for i in range(interval_days+1)]
                self.month_week_date_dict[month][weekid] = tmp


class ConsumeData:

    def __init__(self, Param):
        self.Param = Param
        self.log_msg_list = []
        self.steel_model_dict = getlib.get_steel_all_model_map()
        self.bom_version_info = getlib.get_latest_bom_version_info()
        self.operation_calendar = getlib.get_operation_calendar()
        self.cal_number_of_workday()
        self.gen_conumse_container()
        # self.gen_real_consume()
        self.cal_estimate_consume()
        self.cal_real_consume()
        self.month_last_day_adjust()
        self.cal_estimate_mff_consume()

    def gen_conumse_container(self):
        self.consume = {}
        self.consume_mff = {}
        for material in self.Param.material_list:
            self.consume[material] = {}
            self.consume_mff[material] = {}
            for date in self.Param.date_list:
                self.consume[material][date] = 0
                self.consume_mff[material][date] = 0

    def cal_number_of_workday(self):
        '''
        計算工作天數
        依月份、月份-周別
        '''
        self.month_workday = {}
        for month, date_list in self.Param.month_date_dict.items():
            count = 0
            for date in date_list:
                if self.operation_calendar.get(date) == 'Y':
                    count += 1
            self.month_workday[month] = count

        self.month_week_workday = {}
        for month, week_dict in self.Param.month_week_date_dict.items():
            self.month_week_workday[month] = {}
            for week, date_list in week_dict.items():
                count = 0
                for date in date_list:
                    if self.operation_calendar.get(date) == 'Y':
                        count += 1
                self.month_week_workday[month][week] = count

    def gen_real_consume(self):
        '''
        生成實際耗用的對應字典
        '''
        self.real_consume_raw = getlib.get_real_consume(self.Param.start_date)
        self.day_real_consume = {}
        for date in self.Param.date_list:
            if date < self.Param.today:
                self.day_real_consume[date] = {}
                for material in self.Param.material_list:
                    self.day_real_consume[date][material] = 0

        for date, consume_dict in self.real_consume_raw.items():
            if date < self.Param.today:
                for material, amount in consume_dict.items():
                    if material in self.Param.material_list:
                        self.day_real_consume[date][material] = amount

    def cal_real_consume(self):
        '''
        判斷並配置小於當日的實際已耗用
        '''
        # for date, material_consume in self.day_real_consume.items():
        #     if date < self.Param.today:
        #         for material, single_consume in material_consume.items():
        #             self.consume[material][date] = single_consume
        self.real_consume_raw = getlib.get_real_consume(self.Param.start_date)
        for index, row in self.real_consume_raw.iterrows():
            date = row['EAF_開始日期']
            material = row['SAP料號']
            amount = row['重量']
            mmf_no = row['中頻爐爐號']

            if date in self.Param.date_list and material in self.Param.material_list:

                self.consume[material][date] += amount
                if mmf_no != '':
                    self.consume_mff[material][date] += amount

    def cal_estimate_mff_consume(self):
        '''
        計算BOM2的中頻爐原料耗用預估量
        '''
        self.cal_estimate_mff_consume_record = {}

        for month in self.Param.month_list:
            bomid = self.bom_version_info.get(month).get('bomid')
            dateid = self.bom_version_info.get(month).get('dateid')
            material_mmf_conusme_dict = getlib.get_material_consume_mff_by_bomid_dateid(bomid, dateid)
            period = getlib.get_bom_period(bomid, dateid)
            start_date = period.get('StartDate')
            end_date = period.get('EndDate')
            date_list = [start_date + datetime.timedelta(days=i) for i in range((end_date-start_date).days + 1)]
            workday_count = self.count_workday(date_list)
            for material, mff_consume in material_mmf_conusme_dict.items():
                mff_consume_per_day = mff_consume / workday_count
                for date in date_list:
                    if date >= self.Param.today:
                        if self.operation_calendar.get(date) == 'Y':
                            self.consume[material][date] += mff_consume_per_day
                            self.consume_mff[material][date] += mff_consume_per_day
            
            self.cal_estimate_mff_consume_record[month] = {
                'bomid':bomid,
                'dateid':dateid,
                'material_mmf_conusme_dict':material_mmf_conusme_dict,
                'period':period,
                'date_list':date_list,
                'workday_count':workday_count
            }

    def count_workday(self, date_list):
        count = 0
        for date in date_list:
            if self.operation_calendar.get(date) == 'Y':
                count += 1

        return count

    def cal_estimate_consume(self):
        '''
        計算下三月的原料耗用量
        若bomid為
            Bom1_0 -> 日耗用 = 整月耗用 / 工作天數
            Bom2_2 -> 判斷該周是否用排程計算日耗用
                        -> Y -> 當日與下周的 日耗用 = 排程 * BOM2
                        -> N -> 日耗用 = 周生產計劃 * BOM2 / 該周工作天數
            判斷邏輯：若當日為當周最後一天，則提前換周的原則下，下周需用排程計算
            判斷條件：取該周的第一天，扣一天作為換周的切換日，若當日>=切換日，則使用排程計算
            舉例:以2025-07為例,各周的起始日為 1/5/12/19/26, 假設當日為18, 為第三周的最後一日
                 則第四周第一日19-1=18, 剛好等於18, 所以第四周要用排程計算
        '''
        self.cal_estimate_consume_record = {}

        for month in self.Param.month_list:
            bomid = self.bom_version_info.get(month).get('bomid')
            dateid = self.bom_version_info.get(month).get('dateid')
            if bomid == 'YS_Bom1_0':
                workday_count = self.month_workday.get(month)
                material_consume_dict = getlib.get_material_consume_by_bomid_dateid(bomid, dateid)
                for material in self.Param.material_list:
                    consume = material_consume_dict.get(material,0)
                    consume_per_day = consume / workday_count
                    date_list = self.Param.month_date_dict.get(month)
                    for date in date_list:
                        if self.operation_calendar.get(date) == 'Y':
                            self.consume[material][date] += consume_per_day

                self.cal_estimate_consume_record[month] = {
                    'bomid':bomid,
                    'dateid':dateid,
                    'workday_count':workday_count,
                    'material_consume_dict':material_consume_dict,
                }

            elif bomid == 'YS_Bom2_2':
                bom = getlib.get_bom(bomid, dateid)
                week_plan = getlib.get_week_plan(month)
                plan = getlib.get_record_plan(bomid, dateid)
                schedule = getlib.get_record_schedule(bomid, dateid)
                bom_tba = self.bom2_tba_average(bom, plan, schedule)
                week_plan_dict = self.transform_week_plan_to_dict(week_plan)
                schedule_dict = self.transform_schedule_to_dict(schedule)
                schedule_consume = self.cal_schedule_consume(bom, schedule_dict)
                week_plan_consume = self.cal_week_plan_consume(month, bom_tba, week_plan_dict)
                for weekid, date_list in self.Param.month_week_date_dict.get(month).items():
                    start_date = min(date_list)
                    if self.Param.today >= start_date + datetime.timedelta(days=-1):
                        for date in date_list:
                            if date >= self.Param.today:
                                schedule_material_consume = schedule_consume.get(date,{})
                                for material, single_consume in schedule_material_consume.items():
                                    self.consume[material][date] += single_consume
                        
                    else:
                        for date in date_list:
                            week_plan_material_consume = week_plan_consume.get(date)
                            for material, single_consume in week_plan_material_consume.items():
                                self.consume[material][date] += single_consume

                self.cal_estimate_consume_record[month] = {
                    'bomid':bomid,
                    'dateid':dateid,
                    'bom':bom,
                    'week_plan':week_plan,
                    'plan':plan,
                    'schedule':schedule,
                    'bom_tba':bom_tba,
                    'week_plan_dict':week_plan_dict,
                    'schedule_dict':schedule_dict,
                    'schedule_consume':schedule_consume,
                    'week_plan_consume':week_plan_consume
                }            
    
    def month_last_day_adjust(self):
        '''
        每個月最後一天, 按照cal_estimate_consume的計算邏輯, 會用當月的BOM2乘上當日的排程
        但實際上已經提前換月, 故需使用下月的BOM2乘上當日的排程, 作為耗用推估的調整
        '''
        year = self.Param.today.year
        month = self.Param.today.month
        last_day = calendar.monthrange(year, month)[1]
        if self.Param.today.day == last_day:
            next_day = self.Param.today + datetime.timedelta(days=1)
            month = format(next_day,'%Y-%m')
            material_consume = self.cal_estimate_consume_record.get(month).get('schedule_consume').get(self.Param.today)
            if material_consume is not None:
                for material, single_consume in material_consume.items():
                    self.consume[material][self.Param.today] = single_consume

    def cal_week_plan_consume(self, month, bom_tba, week_plan_dict):
        week_plan_consume = {}
        for weekid, date_list in self.Param.month_week_date_dict.get(month).items():
            for date in date_list:
                week_plan_consume[date] = {}
                for material in self.Param.material_list:
                    week_plan_consume[date][material] = 0

        for weekid, steel_info_list in week_plan_dict.items():
            date_list = self.Param.month_week_date_dict.get(month).get(weekid)
            workday_count = self.month_week_workday.get(month).get(weekid)
            for steel_info in steel_info_list:
                steel = steel_info.get('steel')
                vod = steel_info.get('vod')
                qty = steel_info.get('qty')
                bom_single = bom_tba.get(steel)
                if bom_single is not None:
                    for material, unit_consume in bom_single.items():
                        consume = qty * unit_consume / 1000
                        consume_per_day = consume / workday_count
                        for date in date_list:
                            if self.operation_calendar.get(date) == 'Y':
                                week_plan_consume[date][material] += consume_per_day

        return week_plan_consume

    def cal_schedule_consume(self, bom, schedule_dict):

        schedule_consume = {}
        for date in schedule_dict.keys():
            schedule_consume[date] = {}
            for material in self.Param.material_list:
                schedule_consume[date][material] = 0

        for date, steel_info_list in schedule_dict.items():
            for steel_info in steel_info_list:
                steel = steel_info.get('steel')
                vod = steel_info.get('vod')
                qty = steel_info.get('qty')
                
                bom_vod = bom.get(steel)
                if bom_vod is None:
                    steel_mapped = self.steel_model_dict.get(steel)
                    if date >= self.Param.today:
                        if steel_mapped is None:
                            msg = f'排程日期({date}) | {steel} | 查無BOM模型對應鋼種'
                            self.log_msg_list.append({'msg':msg,'level':'Warning'})
                            print(msg)
                            Elog.info(msg)
                        else:
                            bom_vod = bom.get(steel_mapped)
                            if bom_vod is None:
                                msg = f'排程日期({date}) | {steel} | 有BOM模型對應鋼種({steel_mapped})但查無BOM表'
                                self.log_msg_list.append({'msg':msg,'level':'Warning'})
                                print(msg)
                                Elog.info(msg)
                else:
                    bom_single = bom_vod.get(vod)
                    if bom_single is None:
                        msg = f'排程日期({date}) | {steel} | {vod} | 有BOM表但二三段不匹配'
                        self.log_msg_list.append({'msg':msg,'level':'Warning'})
                        print(msg)
                        Elog.info(msg)
                    else:
                        for material, unit_consume in bom_single.items():
                            consume = qty * unit_consume / 1000
                            schedule_consume[date][material] += consume
        
        return schedule_consume

                                
    def transform_week_plan_to_dict(self, week_plan):

        res = {}
        for index, row in week_plan.iterrows():
            weekid = row['Week']
            steel = row['Sid']
            qty = row['TBA']
            if weekid not in res.keys():
                res[weekid] = []
            res[weekid].append(
                {
                    'steel':steel,
                    'qty':qty
                }
            )

        return res

    def transform_schedule_to_dict(self, schedule):
        res = {}
        for index, row in schedule.iterrows():
            date = row['ScheduleDate']
            vod = row['Vod']
            steel = row['Grade']
            qty = row['Qty']
            if date not in res.keys():
                res[date] = []
            res[date].append(
                {
                    'vod':vod,
                    'steel':steel,
                    'qty':qty
                }
            )

        return res

    def bom2_tba_average(self, bom, plan, schedule):

        '''
        生產計劃扣除煉鋼排程, 再計算各鋼種mod2的比例
        bom表依據mod2/mod3的比例加權平均
        '''
        schedule_sum = schedule.groupby(['Grade','Vod'])['Qty'].sum().reset_index()
        schedule_sum = schedule_sum.rename(columns={'Qty':'Qty_S'})
        plan_adjust = plan.merge(schedule_sum, on=['Grade','Vod'], how='left')
        plan_adjust['Qty_S'] = plan_adjust['Qty_S'].fillna(0)
        plan_adjust['Qty_R'] = plan_adjust['Qty'] - plan_adjust['Qty_S']
        plan_r_total = plan_adjust.groupby('Grade')['Qty_R'].sum().reset_index()
        plan_r_total = plan_r_total.rename(columns={'Qty_R':'Total_R'})
        plan_adjust = plan_adjust.merge(plan_r_total, on=['Grade'], how='left')
        plan_adjust['prop_R'] = plan_adjust['Qty_R'] / plan_adjust['Total_R']
        plan_adjst_mod2 = plan_adjust[plan_adjust['Vod']=='mod2']
        plan_adjst_mod2 = plan_adjst_mod2.dropna(subset='prop_R')
        mod2ratio = dict(plan_adjst_mod2[['Grade','prop_R']].values)

        bom_cmb = {}
        for steel, vod_bom in bom.items():
            if len(vod_bom)==1:
                vod = list(vod_bom.keys())[0]
                bom_cmb[steel] = vod_bom.get(vod)
            else:
                mod2_bom = vod_bom.get('mod2')
                mod3_bom = vod_bom.get('mod3')
                mod2_weight = mod2ratio.get(steel)
                if mod2_weight is not None:
                    avg_bom = {}
                    for material in mod2_bom.keys():
                        avg_unit_consume = mod2_bom.get(material)*mod2_weight + mod3_bom.get(material)*(1-mod2_weight)
                        avg_bom[material] = avg_unit_consume
                    bom_cmb[steel] = avg_bom

        return bom_cmb

    def write_log(self):

        todaytime_str = format(self.Param.todaytime, '%Y-%m-%d %H:%M:%S')
        event = '耗用預估'
        item = '鋼種對應檢核'
        muser = 'system_user'
        for pack in self.log_msg_list:
            level = pack.get('level')
            notes = pack.get('msg')
            sqlstr = f'''
            insert into PCI_Log
            (Datetime, Event, Item, [Level], Notes, MUser) 
            values
            ('{todaytime_str}','{event}','{item}','{level}','{notes}','{muser}')
            '''
            DB.execute(sqlstr, GlobalVar.QUANTDATA_CONNSTR)


class InventoryData:

    ''' 
    {料號:{日期:期末庫存}}
    '''

    def __init__(self, Param):
        self.Param = Param
        self.inventory_mes = getlib.get_inventory_mes()
        self.inventory_sap = getlib.get_inventory_sap()
        self.inventory_control = getlib.get_inventory_control()
        self.inventory_sub_history = getlib.get_inventory_sub_history()
        self.gen_container()
        self.gen_inventory_dict()
        self.gen_inventory_sub_dict()

    def gen_container(self):
        '''
        生成庫存的字典
        {料號:{日期:期末庫存}}
        '''
        self.inventory = {}
        self.inventory_sub = {}
        for material in self.Param.material_list:
            self.inventory[material] = {}
            self.inventory_sub[material] = {}
            for date in self.Param.date_list:
                self.inventory[material][date] = 0
                self.inventory_sub[material][date] = 0
        
    def gen_inventory_dict(self):
        '''
        將庫存資料匹配進字典中
        '''
        for material in self.Param.material_list:
            print(material)
            for date in self.Param.date_list:
                if date < self.Param.today:
                    # 此處兩料號原料抓取SAP庫存(MES沒有庫存資料)
                    SPECIAL_SAP_INVENTORY_MATERIALS = []
                    if material in SPECIAL_SAP_INVENTORY_MATERIALS:
                        inv = self.inventory_sap.get(material,{}).get(date,0)
                    else:
                        inv = self.inventory_mes.get(material,{}).get(date,0)

                    self.inventory[material][date] = inv
                
    def gen_inventory_sub_dict(self):
        '''
        可用庫存 = 庫存 - 管制用量
        '''
        # 從MES庫存資料篩選出可用庫存
        date = self.Param.today + datetime.timedelta(days=-1)
        for material in self.Param.material_list:
            inv = self.inventory.get(material).get(date)
            control = self.inventory_control.get(material, 0)
            self.inventory_sub[material][date] = inv - control

        # 從進耗存推估表(YS_Material_PCI)抓取可用庫存歷史資料
        for material in self.Param.material_list:
            for date in self.Param.date_list:
                if date < self.Param.today + datetime.timedelta(days=-1):
                    try:
                        inv = self.inventory_sub_history.get(material).get(date)
                        self.inventory_sub[material][date] = inv
                    except:
                        print(f'{material}沒有歷史可用庫存')



class ProcurementData:

    def __init__(self, Param):
        self.Param = Param
        self.procurement_wap = getlib.get_procurement_wap()
        self.procurement_transfer = getlib.get_procurement_transfer(self.Param.start_date)
        self.arrange = getlib.get_procurement_arrange()
        self.summary = getlib.get_procurement_summary()
        self.gen_container()
        self.cal_procurement()
        self.cal_procurement_self()

    def gen_container(self):
        '''
        生成進貨的字典
        {料號:{日期:進貨量}}
        '''
        self.procurement = {}
        for material in self.Param.material_list:
            self.procurement[material] = {}
            for date in self.Param.date_list:
                self.procurement[material][date] = 0

    def add_amount(self, material, date, amount):
        '''
        依據料號,日期
        把進貨量加進self.procurement字典中
        '''
        cond1 = date in self.Param.date_list
        cond2 = material in self.Param.material_list
        if cond1 and cond2:
            print(material, date, amount)
            cur_amount = self.procurement.get(material).get(date)
            cur_amount += amount
            self.procurement[material][date] = cur_amount

    @staticmethod
    def date_distribution(date_start, n_days):
        '''
        列出起始日(date_start)往後n日，且非六日的日期
        '''
        date_start = date_start + datetime.timedelta(days=-1)
        res = []
        while len(res) < n_days:
            date_start += datetime.timedelta(days=1)
            if date_start.weekday() < 5:
                res.append(date_start)

        return res

    def cal_procurement(self):
        '''
        (1) 進貨安排有資料 -> 進貨日期 及 進貨量 皆以進貨安排為準
        (2) 若無進貨安排資料 -> 以WAP採購追蹤為準
            若為"外購"：
                有進口日：
                    -> 進貨量:淨重，並以每日200MT為單位往下推展
                    -> 進貨日: if 進口日+5 < 計算日 -> 計算日當月最後一天
                            else 進口日+5
                無進口日：
                -> 進貨量: WAP採購追蹤「淨重」
                -> 進貨日: WAP採購追蹤「合約交貨日」
            若為"內購":
                -> 進貨量: WAP採購追蹤「淨重」
                -> 進貨日: WAP採購追蹤「合約交貨日」
        '''
        self.cal_result = []
        for index, row in self.procurement_wap.iterrows():
            main_key = row['main_key']
            purchase_type = row['內外購']
            wap_amount = row['淨重']
            material = row['料號']
            import_date = row['進口日']
            contract_date = row['合約交貨日']

            last_day = calendar.monthrange(self.Param.today.year, self.Param.today.month)[1]
            cur_month_last_date = self.Param.today.replace(day=last_day)

            if material in self.Param.material_list:
                arrange = self.arrange.get(main_key)
                if arrange is not None:
                    source = 'arrange'
                    for date, amount_dict in arrange.items():
                        if date < self.Param.today:
                            amount = amount_dict.get('actual')
                        else:
                            amount = amount_dict.get('plan')
                        if amount is not None:
                            self.add_amount(material, date, amount)
                            self.cal_result.append([main_key,purchase_type,source,material,date,amount])
                else:
                    if purchase_type == '外購':
                        if not pd.isna(import_date):
                            source = 'wap & import_date'
                            date = import_date + datetime.timedelta(days=5)
                            if date < self.Param.today:
                                date_start = cur_month_last_date
                            else:
                                date_start = date

                            print(wap_amount)
                            quotient, remainder = divmod(wap_amount, 200)
                            if remainder == 0:
                                amount_dist = [200] * int(quotient)
                            else:
                                amount_dist = [200] * int(quotient) + [remainder]
                            date_dist = self.date_distribution(date_start, quotient+1)

                            for amount, date in zip(amount_dist, date_dist):
                                if amount is not None:
                                    self.add_amount(material, date, amount)
                                    self.cal_result.append([main_key,purchase_type,source,material,date,amount])
                        else:
                            source = 'wap & contract_date'
                            date = contract_date
                            amount = wap_amount
                            self.add_amount(material, date, amount)
                            self.cal_result.append([main_key,purchase_type,source,material,date,amount])
                
                    elif purchase_type == '內購':
                        source = 'wap & contract_date'
                        date = contract_date
                        amount = wap_amount
                        self.add_amount(material, date, amount)
                        self.cal_result.append([main_key,purchase_type,source,material,date,amount])

        self.cal_result = pd.DataFrame(self.cal_result,columns=['main_key','purchase_type','source','material','date','amount'])

    def cal_procurement_self(self):

        for index, row in self.procurement_transfer.iterrows():

            date = row['調撥日']
            material = row['料號']
            amount = row['淨重']

            if date in self.Param.date_list and material in self.Param.self_material_list:
                self.add_amount(material, date, amount)


if __name__ == '__main__':

    pm = Param()
    p = ProcurementData(pm)
    c = ConsumeData(pm)
    i = InventoryData(pm)