from Comm.Model.DataModel import WebSite
import requests,demjson,datetime,time,threading
from Comm.Model.DataModel import IFund

class FundSpider():
    def __init__(self,iwebste:WebSite) -> None:
        _iwebsite=WebSite
    def get_detail(self,s_data:IFund):
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
  'Accept-Language': 'zh-CN,zh;q=0.9',
  'Cookie': 'ASP.NET_SessionId=yxydfgartkudabdmswlpfpq5'
}

       response = requests.request("GET", url, headers=headers, data=payload)
       res=response.text
       front_len=len('var rankData =')
       res=res[front_len:]
       res=res[:-1]
       json_data=demjson.decode(res)
       for item in json_data["datas"]:
            try:
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

               threading.Thread(target=self.get_detail,args=single_data)
            except Exception as ex:
                print(ex)
        
       
       print(json_data)
