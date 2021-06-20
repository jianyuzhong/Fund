from Config.iconfig import idatabase,FundWebSite
from Comm.Model.DataModel import WebSite
from Bussiness.Spider import FundSpider

if __name__=='__main__':
    for item in FundWebSite:
        if isinstance(item,WebSite):
            spider=FundSpider(WebSite)
            spider.start()
    # a=HttpAccess(0,'',)
    # i=idatabase.get_dicts(" select *from test ",convert=False)
    # a=1