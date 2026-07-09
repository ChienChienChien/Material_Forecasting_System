import datetime

class Util:

    @staticmethod
    def next_month(ym):
        ym_date = datetime.datetime.strptime(f'{ym}-01', '%Y-%m-%d')
        ym_month = ym_date.month
        ym_year = ym_date.year
        if ym_month == 12:
            year = ym_year + 1
            month = 1
        else:
            year = ym_year
            month = ym_month + 1

        next_ym_date = ym_date.replace(year=year, month=month)
        next_ym = format(next_ym_date, '%Y-%m')

        return next_ym

    @staticmethod
    def inv_control_filter(x):

        material = x['料號']
        cond1 = x['儲區']=='M201'
        cond2 = x['試熔狀態'] in ('待試熔','交貨中')
        cond3 = x['管制使用']=='Y'

        if material == '030126SUS000':
            if (cond1 and cond2) or cond3:
                return 'Y'
            else:
                return 'N'

        elif material in ('030126SUS316','030126SUS011'):
            if cond2 or cond3:
                return 'Y'
            else:
                return 'N'

        else:
            if cond3:
                return 'Y'
            else:
                return 'N'            

