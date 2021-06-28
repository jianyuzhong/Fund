from Config.iconfig import idatabase,FundWebSite
from Comm.Model.DataModel import WebSite
from Bussiness.Spider import FundSpider
import pytz


if __name__=='__main__':
    sql='insert into ifund (Code,Type,Name,Top,Price,Amount,Total,PublishTime,Conpany,Charge,DFlow,WFlow,MFlow,Date,Url)'
    sql+=f" values('162411','QDII-指数','华宝标普油气上游股票人民币A',0.4805,0.4805,9592460000.0,3865000000.0,'2011-09-05','华宝基金',0.15,1.84,7.33,13.33,'2021-06-24','http://fundf10.eastmoney.com/jbgk_162411.html')"
    idatabase.execute
    for item in FundWebSite:
        if isinstance(item,WebSite):
            spider=FundSpider(WebSite)
            spider.start()
    # a=HttpAccess(0,'',)
    # i=idatabase.get_dicts(" select *from test ",convert=False)
    # a=1