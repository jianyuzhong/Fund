from commonbaby.httpaccess.httpaccess import HttpAccess
from Comm.Model.DataModel import WebSite
import requests,demjson,datetime,time,threading
from Comm.Model.DataModel import IFund
from commonbaby.httpaccess import ResponseIO
from commonbaby.helpers import helper_str
from bs4 import BeautifulSoup
import bs4

class FundSpider():
    def __init__(self,iwebste:WebSite) -> None:
        _iwebsite=WebSite
    def get_Manager(self,s_data:IFund):
        pass
    def get_detail(self,s_data:IFund):
        url=f"http://fundf10.eastmoney.com/ccmx_{s_data.code}.html"
        headers = {
  'Host':'fundf10.eastmoney.com',
  'Proxy-Connection': 'keep-alive',
  'Cache-Control':'max-age=0',
  'Upgrade-Insecure-Requests':'1',
  'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
  'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
  'Referer':'http://fund.eastmoney.com/005296.html',
  'Accept-Encoding': 'gzip,deflate',
  'Accept-Language': 'zh-CN,zh;q=0.9'
}
        ha=HttpAccess(0,)
        res=ha.get(url=url,headers=headers)
        i_soup=BeautifulSoup(res.text,'lxml')
        base_info=i_soup.select('[class="bs_gl"] p label')
        if isinstance(base_info[0],bs4.element.Tag):
            s_data.publishtime= base_info[0].select_one('span').get_text()
        if isinstance(base_info[2],bs4.element.Tag):
            s_data.publishtime= base_info[2].select_one('span').get_text()
        if isinstance(base_info[3],bs4.element.Tag):
            s_data.company= base_info[3].select_one('a').get_text()
        s_date=base_info[0]
        for xx in base_info:
            if isinstance(xx,bs4.element.Tag):
                print(xx.text)
                
            
            
        a=0
       
    

        pass     
    def start(self):
       url=f"http://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=all&rs=&gs=0&sc=6yzf&st=desc&sd={time.strftime('%Y-%m-%d', time.localtime())}&ed={time.strftime('%Y-%m-%d', time.localtime())}&qdii=&tabSubtype=,,,,,&pi=1&pn=50&dx=1"
       payload={}
       headers = {
  'Host': 'fund.eastmoney.com',
  'Proxy-Connection': 'keep-alive',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
  'Accept': '*/*',
  'Referer': 'http://fund.eastmoney.com/data/fundranking.html',
  'Accept-Encoding': 'gzip, deflate',
  'Accept-Language': 'zh-CN,zh;q=0.9'
}
    #    response = requests.request("GET", url, headers=headers, data=payload)
       ha=HttpAccess(0,)
       response=ha.get(url=url,headers=headers)
       res=response.text
       front_len=len('var rankData =')
       res=res[front_len:]
       res=res[:-1]
       json_data=demjson.decode(res)   
       t_list=[]
       for item in json_data["datas"]:
            try:
               if len(t_list)>5:
                   for end_t in t_list:
                       if isinstance(end_t,threading.Thread):
                           end_t.join()
               s= str(item).split(',')
               single_data=IFund()
               single_data.date=s[3]
               single_data.code=s[0]
               single_data.name=s[1]
               single_data.price=s[4]
               single_data.top=s[5]
               single_data.d_flow=s[6]
               single_data.w_flow=s[7]
               single_data.m_flow=s[8]
               single_data.Charge=s[22]
               single_data.available=s[23]
            #    t= threading.Thread(target=self.get_detail,args=(self,single_data))
            #    t_list.append(t)
               self.get_detail(single_data)
            except Exception as ex:
                print(ex)  
       for end_t in t_list:
            if isinstance(end_t,threading.Thread):
                end_t.join()
    #    print(json_data)
