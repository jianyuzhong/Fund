from Config.iconfig import FundWebSite,logger
from Comm.Model.DataModel import FundSpider
import pytz,time

if __name__=='__main__':
    logger.info(f"program start date{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    for item in FundWebSite:
        if isinstance(item,FundSpider):
            if  not item._enable:
                continue
            logger.info(f'Spider {item._name} start')
            item.start()
    logger.info('spider fund compeleted ...')
    # a=HttpAccess(0FundSpider,'',)
    # i=idatabase.get_dicts(" select *from test ",convert=False)
    # a=1