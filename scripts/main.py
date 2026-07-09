from data import Param, ConsumeData, InventoryData, ProcurementData
from model import PCI

if __name__ == '__main__':

    param = Param()
    c = ConsumeData(param)
    i = InventoryData(param)
    p = ProcurementData(param)

    model = PCI(param, p, c, i)
    model.to_db()
    model.to_db_static()
    c.write_log()