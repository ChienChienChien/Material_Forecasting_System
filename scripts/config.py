import os
from dotenv import load_dotenv
from dglib.config.globalvar import GlobalVar

GlobalVar.Init(GlobalVar.dglib_DBConnStr_QUANTDATA)
load_dotenv()

GlobalVar.ZONE = os.getenv('SWITCH')
if GlobalVar.ZONE == 'Formal':
    GlobalVar.QUANTDATA_CONNSTR = GlobalVar.dglib_DBConnStr_QUANTDATA_F
    
if GlobalVar.ZONE == 'Test':
    GlobalVar.QUANTDATA_CONNSTR = GlobalVar.dglib_DBConnStr_QUANTDATA