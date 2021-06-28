from commonbaby.httpaccess import HttpAccess
import requests,demjson,threading,pytz
from Comm.Model.DataModel import IFund,Position,FundSpider
from commonbaby.httpaccess import ResponseIO
from bs4 import BeautifulSoup
from commonbaby.helpers import helper_str
import bs4
import calendar
import time
import sys
from datetime import datetime
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

class T_FundSpider(FundSpider):
    def get_Manager(self,s_data:IFund):
        pass
    def get_detail(self,s_data:IFund):
        try:
            url=f"http://fundf10.eastmoney.com/jbgk_{s_data.code}.html"
            headers = {
      'Host':'fundf10.eastmoney.com',
      'Proxy-Connection': 'keep-alive',
      'Cache-Control':'max-age=0',
      'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
      'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
      'Accept-Encoding': 'gzip,deflate',
      'Accept-Language': 'zh-CN,zh;q=0.9'
}    
            ha=HttpAccess(0,)
            res=ha.get(url=url,headers=headers)
            i_soup=BeautifulSoup(res.text,'lxml')
            base_info=i_soup.select('[class="txt_cont"] table tr')
            s_data.url=url
            if isinstance(base_info[2],bs4.element.Tag):
                publishtime= base_info[2].select_one('td').get_text()
                if str(publishtime)!='':
                      s_data.publishtime=str(publishtime).replace('年','-').replace('月','-').replace('日','')
            if isinstance(base_info[1],bs4.element.Tag):
                s_data.type= base_info[1].select('td')[1].get_text()
            if isinstance(base_info[4],bs4.element.Tag):
                s_data.company= base_info[4].select('td')[0].get_text()
            if isinstance(base_info[5],bs4.element.Tag):
                s_data.manager= base_info[5].select('td')[0].get_text()
            s_total=str(base_info[3].select('td')[0].get_text())
            s_amount=str(base_info[3].select('td')[1].get_text())
            if helper_str.substring(s_total,'','亿')!='---':
                s_data.total=float(helper_str.substring(s_total,'','亿'))*100000000
                s_data.amoumt=float(helper_str.substring(s_amount,'','亿'))*100000000
            s_data.Insert(self._idatabase)
            t=threading.Thread(target=self.get_posion,args=s_data)
            t.start()
        except Exception as ex:
            self._logger.error(f"get detail error with messages {str(ex)}")
    def get_posion(self,s_data:IFund):
        headers={  'Host': 'fundf10.eastmoney.com',
  'Connection': 'keep-alive',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36',
  'Accept': '*/*',
  'Referer': 'http://fundf10.eastmoney.com/ccmx_005296.html',
  'Accept-Encoding': 'gzip, deflate',
  'Accept-Language': 'zh-CN,zh;q=0.9',}
        url=f"http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={s_data.code}&topline=10&year=&month="
        ha=HttpAccess(0)
        res=ha.get(url=url,headers=headers)
        t=res.text
        f_len=len('var apidata=')
        t_json=t[f_len:]
        t_json=t_json[:-1]
        json_data=demjson.decode(t_json)
        t_html=BeautifulSoup(json_data["content"],'lxml')
        h_tr=t_html.select('table tbody tr')
        ts = calendar.timegm(time.gmtime())
        secids= t_html.select_one('[class="hide"]').get_text()
        jjcc_items=[]
        for xx in h_tr:
            if isinstance(xx,bs4.element.Tag):
                j_tr=xx.find_all('td')
                j_item=Position()
                j_item.f_code=s_data.code
                j_item.name=j_tr[2].get_text()
                j_item.code=j_tr[1].get_text()
                j_item.propotion=j_tr[6].get_text()
                j_item.t_amount=j_tr[7].get_text()
                j_item.t_value=j_tr[8].get_text() 
                j_item.url=j_tr[2].find('a').attrs["href"]
                j_item.date=datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
                jjcc_items.append(j_item) 
        j_url=f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=f2,f3,f4,f5,f8,f9,f10,f11&secids={secids}"  
        headers={  'Host': 'push2.eastmoney.com',
  'Connection': 'keep-alive',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36',
  'Accept': '*/*',
  'Referer': 'http://fundf10.eastmoney.com/',
  'Accept-Encoding': 'gzip, deflate',
  'Accept-Language': 'zh-CN,zh;q=0.9',}
  
        j_res=ha.get(url=j_url,headers=headers)
        d_json=demjson.decode(j_res.text)
        i_count=0
        for d_item in d_json["data"]["diff"]:
            try:
               jjcc_items[i_count].price=d_item["f2"]
               jjcc_items[i_count].flow=d_item["f3"]
               jjcc_items[i_count].flow_amount=d_item["f4"]
               jjcc_items[i_count].deal=d_item["f5"]
               jjcc_items[i_count].change=d_item["f8"]
               jjcc_items[i_count].PEG_ratio=d_item["f9"]
               jjcc_items[i_count].ratio_rate=d_item["f10"]
               jjcc_items[i_count].draw=d_item["f11"]
               if isinstance(jjcc_items[i_count],Position):
                   jjcc_items[i_count].
            except Exception as ex:
                self._logger.error(f"d_json error  {ex}")
            i_count+=1     
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
       c_num=1
       max_page=json_data["allPages"]
       while c_num<=max_page:
            url=f"http://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=all&rs=&gs=0&sc=6yzf&st=desc&sd={time.strftime('%Y-%m-%d', time.localtime())}&ed={time.strftime('%Y-%m-%d', time.localtime())}&qdii=&tabSubtype=,,,,,&pi={c_num}&pn=50&dx=1"
            response=ha.get(url=url,headers=headers)
            res=response.text
            front_len=len('var rankData =')
            res=res[front_len:] 
            res=res[:-1]
            try:
                json_data=demjson.decode(res)   
            except Exception as ex:
                self._logger.error(f'url{url} json error {res}')
            with ThreadPoolExecutor(max_workers=5) as executor:
                for item in json_data["datas"]:
                    try:
                       s= str(item).split(',')
                       single_data=IFund()
                       single_data.date=s[3]
                       single_data.code=s[0]
                       single_data.name=s[1]
                       if str(s[4])!='':
                            single_data.price=s[4]
                       if str(s[5])!='':
                            single_data.top=s[5]
                       if str(s[6])!='':
                            single_data.d_flow=s[6]
                       if str(s[7])!='':
                            single_data.w_flow=s[7]
                       if str(s[8])!='':
                            single_data.m_flow=s[8]
                       if str(s[22])!='':
                            single_data.Charge=s[22].replace('%','')
                       if s[23]!='':
                           single_data.available=s[23]
                       executor.submit(self.get_detail,single_data)
                    #    time.sleep(1)
                    #    self.get_detail(single_data)
                    except Exception as ex:
                       self._logger.error(f"get s_data error with messages {str(ex)}")
            self._logger.info(f'\n\nprogress {c_num}/{max_page}\n\n')
            c_num+=1
    #    print(json_data)
