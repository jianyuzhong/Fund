from cgitb import reset
from contextlib import nullcontext
from logging import Logger
import re
from unittest import result
from commonbaby.httpaccess import HttpAccess
from pymysql import connect
import requests,demjson,threading,pytz
from requests.sessions import InvalidSchema
from soupsieve import select_one
from Comm.Model.DataModel import IFund,Position,FundSpider
from commonbaby.httpaccess import ResponseIO
from bs4 import BeautifulSoup
from commonbaby.helpers import helper_str
import bs4
import calendar
from Comm.DB.idb import DBHelper
import time
from itertools import groupby
from operator import itemgetter
import numpy as np
from concurrent.futures import ThreadPoolExecutor
#低点出现的最小时间 30天内
last_day_level=25
#最低点出现的时间30天内
last_price_level=20
min_score=85.0

class T_FundSpider(FundSpider):
    def get_Manager(self,s_data:IFund):
        pass
    def check_list(self,idata:list):
        d_len=len(idata)
        m_count=0
        res=True
        if d_len>=4:
            res=True
        elif d_len==3:
            for item in idata:
                if  item>=-1:
                    res=False
                    break
        elif d_len==2:
            for item in idata:
                if item>=-2.5:
                    res=False
                    break
        return res
        
    def check_claue(self,data,low_point):
        res=(False,0)
        l_data=self.get_consecutive(low_point,data)
        if len(l_data)==0:
            return (False,0)
        # 总的下滑率
        totol_sub=0.0
        for item in l_data:
            if self.check_list(item):
                totol_sub+=np.sum(item)
                res=(True,len(item),totol_sub)
                break
        return res
    def get_cguess(self,s_data:IFund):
        try:
            url=f"http://fundf10.eastmoney.com/jjjz_{s_data.code}.html"
            headers = {
    'Host': 'fundf10.eastmoney.com',
    'Proxy-Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Referer': f'http://fund.eastmoney.com/{s_data.code}.html',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9'
    }
            
            ha=HttpAccess(0,)
            res=ha.get(url=url,headers=headers)
            i_soup=BeautifulSoup(res.text,'lxml')
            res= i_soup.select_one('[id="fund_gszf"]').get_text()
            if res=='---':
                return 0
            return str(res).replace("%","")
        except Exception as ex:
            self._logger.error(f"get cguess error {ex}")
    def get_consecutive(self,data,history_data):
        try:
            res=[]
            temp=[]
            for k, g in groupby(enumerate(data), lambda ix : ix[0] - ix[1]):
                s_data=list(map(itemgetter(1), g))
                if len(s_data)>=2:
                    temp.append(s_data)     
            for item in temp:
                s_res=[]
                for index in item:
                    s_res.append(history_data[index])
                if len(s_res)>0 and item[-1]>20: res.append(s_res)
        except Exception as ex:
            self._logger.error(f"get_consecutive error with {ex}")
        return res   
        
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
            if s_total!='---':
                s_data.total=float(helper_str.substring(s_total,'','亿'))*100000000
                s_data.amoumt=float(helper_str.substring(s_amount,'','亿'))*100000000
            s_data.Insert(self._idatabase)
            self.get_posion(s_data)
            # t=threading.Thread(target=self.get_posion,args=(s_data,))
            # t.start()
        except Exception as ex:
            self._logger.error(f"get detail error with messages {str(ex)}")
    def get_compare_point(self,history_data:list,avg):
        # 返回参数1，是否入库，2，上次低点时间，3，跌幅等级
        res=False
        c_ount=0
        i_len=len(history_data)
        i_point=[]
        low_level=0
        totol_sub=0.0
        if history_data[-1]<=0:return (0,)
        while c_ount<i_len:
            if history_data[c_ount]<=0:
                i_point.append(c_ount)
            c_ount+=1
        p_day=-1
        checked= self.check_claue(history_data,i_point)
        if checked[0]:
            p_day= i_point[-1]
            low_level=checked[1]
            totol_sub=checked[2]
        if p_day+1>=last_day_level and totol_sub<=-5:
            res=True
        if not res:
            return(res,p_day+1,low_level,totol_sub)
        return(res,p_day+1,low_level,totol_sub)
    def get_min_price(self,f_code,c_day:int):
        # c_day=200
        try:
            headers = {
  'Host': 'api.fund.eastmoney.com',
  'Connection': 'keep-alive',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
  'Accept': '*/*',
  'Referer': f'http://fundf10.eastmoney.com/jjjz_{f_code}.html',
  'Accept-Encoding': 'gzip, deflate',
  'Accept-Language': 'zh-CN,zh;q=0.9'
}
            url=f"http://api.fund.eastmoney.com/f10/lsjz?fundCode={f_code}&pageIndex=1&pageSize={c_day}&startDate=&endDate="
            ha=HttpAccess(0)
            res=ha.get(url=url,headers=headers)
            t=res.text
            json_data=demjson.decode(t)
            history_data=[]
            history_data_price=[]
            if json_data["ErrCode"]!=0:
                return
            l_data=json_data["Data"]["LSJZList"]
            min_price=float(l_data[0]['DWJZ'])
            max_price=0
            for item in l_data:
                price=float(item['DWJZ'])
                if price<=min_price:
                    min_price=price
                if price>=max_price:
                    max_price=price
            return min_price
        except Exception as ex:
            self._logger.error(f'get_min_price {ex}')
    def get_s_score(self,f_code,name,insert=False):
        # c_day=200
        try:
            headers = {
  'Host': 'fundf10.eastmoney.com',
  'Connection': 'keep-alive',
  'Cache-Control': 'max-age=0',
  'Upgrade-Insecure-Requests': '1',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
  'Referer': f'http://fundf10.eastmoney.com/jjjz_{f_code}.html',
  'Accept-Encoding': 'gzip, deflate',
  'Accept-Language': 'zh-CN,zh;q=0.9'
}
            url=f"http://fundf10.eastmoney.com/tsdata_{f_code}.html"
            ha=HttpAccess(0)
            res=ha.get(url=url,headers=headers)
            i_soup=BeautifulSoup(res.text,'lxml')
            script_content=str(i_soup.select('script')[-3])

            paire=re.compile(r'avg = \"(.*?)\"',  re.MULTILINE|re.IGNORECASE)
            obj= paire.findall(script_content)
            if len(obj)>0 and len(str(obj[0]))>0:
                if float(obj[0])>min_score and insert:
                    data=IFund()
                    data.code=f_code
                    data.name=name
                    data.score=float(obj[0])
                    data.url=f"http://fundf10.eastmoney.com/jjjz_{f_code}.html"
                    self.IInsert_score(data)
                return float(obj[0])
            else:
                return 0
        except Exception as ex:
            self._logger.error(f'get_min_price {ex}')
            return 0
    def get_compare(self,s_data:IFund,c_day:int=30):
        try:
            # s_data.code="000390"
            headers = {
  'Host': 'api.fund.eastmoney.com',
  'Connection': 'keep-alive',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
  'Accept': '*/*',
  'Referer': f'http://fundf10.eastmoney.com/jjjz_{s_data.code}.html',
  'Accept-Encoding': 'gzip, deflate',
  'Accept-Language': 'zh-CN,zh;q=0.9'
}
            url=f"http://api.fund.eastmoney.com/f10/lsjz?fundCode={s_data.code}&pageIndex=1&pageSize={c_day}&startDate=&endDate="
            ha=HttpAccess(0)
            res=ha.get(url=url,headers=headers)
            t=res.text
            json_data=demjson.decode(t)
            history_data=[]
            history_data_price=[]
            if json_data["ErrCode"]!=0:
                return
            l_data=json_data["Data"]["LSJZList"]
            tear=len(l_data)-1
            f_total=0.0
            f_total_price=0.0
            min_price=item_price=float(l_data[tear]["DWJZ"])
            min_price_date=0
            c_count=0
            while tear>=0:
                item=float(l_data[tear]["JZZZL"])
                item_price=float(l_data[tear]["DWJZ"])
                f_total+=item
                f_total_price+=item_price
                history_data.append(item)  
                history_data_price.append(item_price)
                if item_price<min_price:
                    min_price=item_price
                    min_price_date=c_count
                tear-=1  
                c_count+=1
            avg=f_total/len(l_data) 
            # avg_price=f_total_price/len(l_data)       
            mm=self.get_compare_point(history_data=history_data,avg=avg)
            if not mm[0]:return
            min_price_120=self.get_min_price(s_data.code,150)
            if min_price >min_price_120 :return
            s_data.variance=np.var(history_data)
            s_data.ipoint=mm[1]
            s_data.lowlevel=mm[2]
            s_data.score=self.get_s_score(s_data.code,s_data.name)
            s_data.cguess=self.get_cguess(s_data)
            s_data.m_avg=np.mean(history_data)
            s_data.w_avg=np.mean(history_data[-7:])
            s_data.url=f"http://fundf10.eastmoney.com/jjjz_{s_data.code}.html"
            self.IInsert(s_data)
            
        except Exception as ex:
            self._logger.error(f"get compare error{ex}")
    def IInsert(self,s_data:IFund):
        # if s_data.ipoint>25:
        sql='insert into ifund (Charge,available,code,dflow,date,ipoint,mflow,name,price,publishtime,top,wflow,variance,wavg,mavg,url,lowlevel,cguess,score)'
        sql+=f" values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        params=[s_data.Charge,s_data.available,s_data.code,s_data.d_flow,s_data.date,s_data.ipoint,s_data.m_flow,s_data.name,s_data.price,s_data.publishtime,s_data.top,s_data.w_flow,s_data.variance,s_data.w_avg,s_data.m_avg,s_data.url,s_data.lowlevel,s_data.cguess,s_data.score]
        con=DBHelper(**self._db_conf)
        con.execute(sql=sql,params=params)
        self._logger.info(f"Code :{s_data.code} name:{s_data.name} ipont:{s_data.ipoint} variance :{s_data.variance} m_avg :{s_data.m_avg} w_avg:{s_data.w_avg}")
    def IInsert_score(self,s_data:IFund):
            # if s_data.ipoint>25:
        sql='insert into ifund (code,score,url,name)'
        sql+=f" values(%s,%s,%s,%s)"
        params=[s_data.code,s_data.score,s_data.url,s_data.name]
        con=DBHelper(**self._db_conf)
        con.execute(sql=sql,params=params)
        self._logger.info(f"Code :{s_data.code} name:{s_data.name} ipont:{s_data.ipoint} variance :{s_data.variance} m_avg :{s_data.m_avg} w_avg:{s_data.w_avg}")
    
    def get_posion(self,s_data:IFund):
        try:
           headers={  'Host': 'fundf10.eastmoney.com',
     'Connection': 'keep-alive',
     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36',
     'Accept': '*/*',
     'Referer': f'http://fundf10.eastmoney.com/ccmx_{s_data.code}.html',
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
           if json_data["content"]=='':
               self._logger.info(f'Fund :{s_data.name} has no data or you an link http://fundf10.eastmoney.com/ccmx_{s_data.code}.html')
               return
           t_html=BeautifulSoup(json_data["content"],'lxml')
           h_tr=t_html.select('table tbody tr')
           ts = calendar.timegm(time.gmtime())
           secids= t_html.select_one('[class="hide"]').get_text()
           if secids=='':
               self._logger.info(f'Fund :{s_data.name} has no data or you an link http://fundf10.eastmoney.com/ccmx_{s_data.code}.html')
               return
           jjcc_items=[]
           for xx in h_tr:
               if isinstance(xx,bs4.element.Tag):
                   j_tr=xx.find_all('td')
                   j_item=Position()
                   j_item.f_code=s_data.code
                   j_item.name=j_tr[2].get_text().replace("'",'’')
                   j_item.code=j_tr[1].get_text()
                   j_item.propotion=j_tr[6].get_text().replace('%','')
                   if len(j_tr)>8:
                       j_item.t_amount=float(j_tr[7].get_text().replace(',',''))*10000
                       j_item.t_value=float(j_tr[8].get_text().replace(',',''))*10000
                   if j_tr[2].find('a')!=None:
                       j_item.url=j_tr[2].find('a').attrs["href"]
                   else:
                       j_item.url=f"http://fundf10.eastmoney.com/ccmx_{s_data.code}.html"
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
                   if str(d_item["f2"])!='-':
                         jjcc_items[i_count].price=d_item["f2"]
                   if str(d_item["f3"])!='-':
                         jjcc_items[i_count].flow=d_item["f3"]
                   if str(d_item["f4"])!='-':
                         jjcc_items[i_count].flow_amount=d_item["f4"]
                   if str(d_item["f5"])!='-':
                         jjcc_items[i_count].deal=d_item["f5"]
                   if str(d_item["f8"])!='-':
                         jjcc_items[i_count].change=d_item["f8"]
                   if str(d_item["f9"])!='-':
                         jjcc_items[i_count].PEG_ratio=str(d_item["f9"])
                   if str(d_item["f10"])!='-':
                         jjcc_items[i_count].ratio_rate=d_item["f10"]
                   if str(d_item["f11"])!='-':
                         jjcc_items[i_count].draw=d_item["f11"]
                   if isinstance(jjcc_items[i_count],Position):
                       jjcc_items[i_count].Insert(self._p_idatabase)
               except Exception as ex:
                   self._logger.error(f"d_json error  {ex}")
               i_count+=1   
        except Exception as ex:
            self._logger.error(f"get position error with message {ex}")       
    
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
                        if str(s[3])!='':
                            single_data.date=s[3]
                        single_data.code=s[0]
                        # self._logger.info(f"http://fundf10.eastmoney.com/jjjz_{single_data.code}.html")
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
                    #    self.get_detail(single_data)
                        # executor.submit(self.get_detail,single_data)
                        executor.submit(self.get_compare,single_data)
                        # self.get_compare(s_data=single_data)
                    #    time.sleep(1)
                    #    self.get_detail(single_data)
                    except Exception as ex:
                        self._logger.error(f"get s_data error with messages {str(ex)}")
            self._logger.info(f'\n\nprogress {c_num}/{max_page}\n\n')
            c_num+=1
            time.sleep(1)
    def start_get_score(self):
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
        max_score=0.0
        m_code=0
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
                        if str(s[3])!='':
                            single_data.date=s[3]
                        single_data.code=s[0]
                        # single_data.name=s[1]
                    #    self.get_detail(single_data)
                        # executor.submit(self.get_detail,single_data)
                        executor.submit(self.get_s_score,s[0],s[1],True)
                        # c_score= self.get_s_score(s[0],s[1],True)
                        # if c_score>=max_score:
                        #     max_score=c_score
                        #     m_code=s[0]
                    #    time.sleep(1)
                    #    self.get_detail(single_data)
                    except Exception as ex:
                        self._logger.error(f"get s_data error with messages {str(ex)}")
            self._logger.info(f'\n\nprogress {c_num}/{max_page}\n\n')
            c_num+=1
            time.sleep(1)
        # self._logger.info(f'\n\n最大评分地址http://fundf10.eastmoney.com/jjjz_{m_code}.html 评分:{max_score}\n\n')   
    def start_all(self):
        # url=f"http://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=all&rs=&gs=0&sc=6yzf&st=desc&sd={time.strftime('%Y-%m-%d', time.localtime())}&ed={time.strftime('%Y-%m-%d', time.localtime())}&qdii=&tabSubtype=,,,,,&pi=1&pn=50&dx=1"
        url=f"http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx?t=1&lx=1&letter=&gsid=&text=&sort=zdf,desc&page=1,200&dt={int(time.time())}&atfc=&onlySale=0"

        payload={}
        headers = {
 'Host': 'fund.eastmoney.com',
  'Connection': 'keep-alive',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
  'Accept': '*/*',
  'Referer': 'http://fund.eastmoney.com/fund.html',
  'Accept-Encoding': 'gzip, deflate',
  'Accept-Language': 'zh-CN,zh;q=0.9',
  'Cookie': 'ASP.NET_SessionId=xa1hhhvximhfjcafappk21wv'
}
    #    response = requests.request("GET", url, headers=headers, data=payload)
        ha=HttpAccess(0,)
        response=ha.get(url=url,headers=headers)
        res=response.text
        front_len=len('var db=')
        res=res[front_len:]
        json_data=demjson.decode(res)   
        c_num=1
        max_page=int(json_data["pages"])
        while c_num<=max_page+1:
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                for item in json_data["datas"]:
                    try:
                        s= str(item).split(',')
                        single_data=IFund()
                        if str(s[3])!='':
                            single_data.date=s[3]
                        single_data.code=s[0]
                        # self._logger.info(f"http://fundf10.eastmoney.com/jjjz_{single_data.code}.html")
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
                    #    self.get_detail(single_data)
                        # executor.submit(self.get_detail,single_data)
                        executor.submit(self.get_compare,single_data)
                        # self.get_compare(s_data=single_data)
                    #    time.sleep(1)
                    #    self.get_detail(single_data)
                    except Exception as ex:
                        self._logger.error(f"get s_data error with messages {str(ex)}")
            url=f"http://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=all&rs=&gs=0&sc=6yzf&st=desc&sd={time.strftime('%Y-%m-%d', time.localtime())}&ed={time.strftime('%Y-%m-%d', time.localtime())}&qdii=&tabSubtype=,,,,,&pi={c_num}&pn=50&dx=1"
            response=ha.get(url=url,headers=headers)
            res=response.text
            front_len=len('var rankData =')
            res=res[front_len:] 
            self._logger.info(f'\n\nprogress {c_num}/{max_page}\n\n')
            try:
                json_data=demjson.decode(res)   
            except Exception as ex:
                self._logger.error(f'url{url} json error {res}')
            time.sleep(3)
            c_num+=1
    def StartCount(self):
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
        result=[]
        while c_num<=max_page:
            url=f"http://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=all&rs=&gs=0&sc=6yzf&st=desc&sd={time.strftime('%Y-%m-%d', time.localtime())}&ed={time.strftime('%Y-%m-%d', time.localtime())}&qdii=&tabSubtype=,,,,,&pi={c_num}&pn=50&dx=1"
            response=ha.get(url=url,headers=headers)
            res=response.text
            front_len=len('var rankData =')
            res=res[front_len:] 
            res=res[:-1]
            try:
                json_data=demjson.decode(res)   
                for item in json_data["datas"]:
                    try:
                        sResult=self.CountTest(item)
                        if(sResult!= None):
                            result.append(sResult)
                    except Exception as ex:
                        self._logger.error(f"get s_data error with messages{str(item)} {str(ex)}")
            except Exception as ex:
                self._logger.error(f'url{url} json error {res}')
                
            self._logger.info(f'\n\nprogress {c_num}/{max_page}\n\n')
            c_num+=1
            time.sleep(1)
        self._logger.info(demjson.encode(result))
    def CountTest(self,dataStr:str):
        data= dataStr.split(',')
        result=None
        allgt0=True
        # if [i for i in data[9:14] if float(i)<0]:
        #     allgt0=False
        alllt0=True
        if [i for i in data[7:8] if float(i)>0]:
            alllt0=False

        if allgt0 and alllt0 and int(float(data[6]))>0:
            result.Name=data[1]
            result.Code=data[0]
        return result
    def get_compare(self,s_data:IFund,c_day:int=30):
        try:
            # s_data.code="000390"
            headers = {
  'Host': 'api.fund.eastmoney.com',
  'Connection': 'keep-alive',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
  'Accept': '*/*',
  'Referer': f'http://fundf10.eastmoney.com/jjjz_{s_data.code}.html',
  'Accept-Encoding': 'gzip, deflate',
  'Accept-Language': 'zh-CN,zh;q=0.9'
}
            url=f"http://api.fund.eastmoney.com/f10/lsjz?fundCode={s_data.code}&pageIndex=1&pageSize={c_day}&startDate=&endDate="