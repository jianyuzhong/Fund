from Comm.Model.DataModel import FundSpider
from Config.iconfig import db_conf
from commonbaby.mslog import MsFileLogConfig,MsLogLevels,MsLogManager, msloglevel, mslogmanager
MsLogManager.static_initial(
    dft_lvl=MsLogLevels.INFO,msficfg=MsFileLogConfig(fi_dir=r"./c_log")
)
logger=MsLogManager.get_logger("c_log")
class CSpider():
    def __init__(self) -> None:
        self._db_conf=db_conf
    
    def start():
        
        pass