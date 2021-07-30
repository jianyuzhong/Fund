from Comm.DB.idb import DBHelper
from commonbaby.mslog import MsFileLogConfig,MsLogLevels,MsLogManager, msloglevel, mslogmanager,MsLogger
from queue import Queue
import threading
import queue
MsLogManager.static_initial(
    dft_lvl=MsLogLevels.INFO,msficfg=MsFileLogConfig(fi_dir=r"./_log")
)
idb_conf = {
            'user' : 'root',
            'passwd' : 'xingfu9635',
            'host' : 'localhost',
            'schema' : 'IDataBase',
            'charset' : 'utf8'
        }
logger=MsLogManager.get_logger("IFund")

class IFund():
    code=None
    type=None
    name=None
    top=0
    price=0
    amoumt=0
    total=0
    publishtime='1949-10-01'
    company=None
    Charge=0
    d_flow=0
    w_flow=0
    m_flow=0
    date='1949-10-01'
    available=1
    manager=None    
    url=None
    ipoint=None
    variance=None
    w_avg=None
    m_avg=None
    lowlevel=0
    cguess=0.0
    score=0.0
    min_price_day=0
    lock = threading.Lock()

    def __init__(self) -> None:
        pass
    def Insert(self,helper:DBHelper):
        self.lock.acquire()
        try:
            sql='insert into ifund (Code,Type,Name,Top,Price,Amount,Total,PublishTime,Conpany,Charge,DFlow,WFlow,MFlow,Date,Url,Available)'
            sql+=f" values('{self.code}','{self.type}','{self.name}',{self.top},{self.price},{self.amoumt},{self.total},'{self.publishtime}','{self.company}',{self.Charge},{self.d_flow},{self.w_flow},{self.w_flow},'{self.date}','{self.url}',{self.available})"
            helper.execute(sql)
            logger.info(f"code:{self.code}, name:{self.name}")
        except Exception as ex:
            logger.error(f"insert into data error with messages {str(ex)} ")
        finally:
            self.lock.release()
class Position():
    f_code=None
    code=None
    name=None
    price=0
    flow=0
    flow_amount=0
    deal=0
    change=0
    PEG_ratio=0
    ratio_rate=0
    draw=0
    url=None
    propotion=0
    t_amount=0
    t_value=0
    date=None
    lock = threading.Lock()
    def Insert(self,helper:DBHelper):
        try:
            con=DBHelper(**idb_conf)
            sql='insert into position (FCode,`Code`,`Name`,Price,Flow,FlowAmount,Deal,`Change`,PEGRatio,RatioRate,Draw,Url,Propotion,TAmount,TValue,`Date`)'
            sql+=f" values('{self.f_code}','{self.code}','{self.name}',{self.price},{self.flow},{self.flow_amount},{self.deal},{self.change},{self.PEG_ratio},{self.ratio_rate},{self.draw},'{self.url}',{self.propotion},{self.t_amount},{self.t_value},now())"
            con.execute(sql)
            logger.info(f"code:{self.code}, name:{self.name}")
        except Exception as ex:
            logger.error(f"insert into data error with messages {str(ex)} ")
        finally:
            pass

class FundSpider():
    def __init__(self,name:str,url:str,db_conf:object,logger:MsLogger,enable:bool=False,maxthread:int=5) -> None:
        self._name=name
        self._url=url      
        self._enable=enable
        self._idatabase=DBHelper(**db_conf)
        self._p_idatabase=DBHelper(**db_conf)
        self._logger=logger
        self._db_conf=db_conf
        self._queque=Queue(maxthread)
    def start():
        pass
