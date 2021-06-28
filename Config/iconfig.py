from Comm.Model.DataModel import WebSite
from Comm.DB.idb import DBHelper
db_conf = {
            'user' : 'root',
            'passwd' : 'xingfu9635',
            'host' : 'localhost',
            'schema' : 'IDataBase',
            'charset' : 'utf8'
        }
idatabase=DBHelper(**db_conf)
FundWebSite=[
  WebSite(name='天天基金',url='https://fund.eastmoney.com/')
]