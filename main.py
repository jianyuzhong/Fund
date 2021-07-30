from Config.iconfig import FundWebSite,logger
from Comm.Model.DataModel import FundSpider
import pytz,time
from Bussiness.ICalc import ICalc
import numpy as np
from itertools import groupby
from operator import itemgetter
def get_low_point(s:list):
    pass

if __name__=='__main__':
    # data = [1, 2, 3, 8, 6, 7, 5, 10, 16, 98, 99, 100, 101]
    # for k, g in groupby(enumerate(data), lambda ix : ix[0] - ix[1]):
    #     print(list(map(itemgetter(1), g)))

    for item in FundWebSite:
        if isinstance(item,FundSpider):
            if  not item._enable:
                continue
            logger.info(f'Spider {item._name} start')
            
            item.start()
        
    # logger.info('spider fund compeleted ...')
    # i=idatabase.get_dicts(" select *from test ",convert=False)
    # a=1