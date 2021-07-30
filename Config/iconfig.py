from Bussiness.Spider import T_FundSpider
from Comm.DB.idb import DBHelper

from commonbaby.mslog import MsFileLogConfig,MsLogLevels,MsLogManager, msloglevel, mslogmanager
MsLogManager.static_initial(
    dft_lvl=MsLogLevels.INFO,msficfg=MsFileLogConfig(fi_dir=r"./_log")
)
c_logger=MsLogManager.get_logger("fund_clac")
logger=MsLogManager.get_logger("fund_spider")
db_conf = {
            'user' : 'root',
            'passwd' : 'xingfu9635',
            'host' : 'localhost',
            'schema' : 'IDataBase',
            'charset' : 'utf8'
        }


FundWebSite=[T_FundSpider(name='天天基金',url='https://fund.eastmoney.com/',db_conf=db_conf,enable=True,logger=logger)]


