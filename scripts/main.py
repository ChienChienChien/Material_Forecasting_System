from data import Param, ConsumeData, IventoryData, ProcurementData
from model import PCI
from dglib.log.nlogE import Elog
from dglib.message.TeamsMsg import TeamsMsg
from config import GlobalVar

if __name__ == '__main__':

    try:
        param = Param()
        c = ConsumeData(param)
        i = IventoryData(param)
        p = ProcurementData(param)

        model = PCI(param, p, c, i)
        model.to_db()
        model.to_db_static()
        c.write_log()
    except Exception as err:
        err_str = str(err)
        Elog.info(f'YS_Material_PCI 排程失敗:{err_str}')
        TeamsMsg.send_by_request(f'YS_Material_PCI 排程失敗:{err_str}', GlobalVar.TEAMS_URL)
    else:
        Elog.info('YS_Material_PCI 排程成功')
        TeamsMsg.send_by_request('YS_Material_PCI 排程成功', GlobalVar.TEAMS_URL)