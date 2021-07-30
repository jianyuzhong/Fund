from Config.iconfig import db_conf,c_logger
from Comm.DB.idb import DBHelper
from concurrent.futures import ThreadPoolExecutor
import threading
class ICalc():
    def __init__(self,max_compare=50,similarity=5) -> None:
        self.idatabse=DBHelper(**db_conf)
        self._max_compare=max_compare
        self._db_conf=db_conf
        self._similarity=5#相似度大于5
        self._lock = threading.Lock()
    def start(self):
        try:
            max_c=self.idatabse.get_dicts('select max(id) as max_count from ifund ')[0]["max_count"]
            a=1
            cid=100
            with  ThreadPoolExecutor(max_workers=10) as worker:
                while cid<max_c:
                    try:
                        data=self.idatabse.get_dicts(f'select id ,code from ifund where id>{cid} order by id  asc limit {self._max_compare}')
                        
                        for row in data:
                            try:
                                worker.submit(self.get_compare,row,max_c)
                                # self.get_compare(row,max_c)
                                
                            except Exception as ex:
                                c_logger.error(f'one {ex}')
                        # c_logger.info(f'\n\n {cid}/{max_c} \n\n')
                        cid=data[-1]["id"]
                    except Exception as ex:
                        c_logger.error(f" get error {ex}")
        except Exception as ex:
            c_logger.info(f'ICalc error{ex}')
    def get_compare(self,row_a,max_count):
        c_nn=DBHelper(**db_conf)
        a_position=c_nn.get_dicts(f"select code from position where fcode='{row_a['code']}'")
        cid=0
        while cid<max_count:
            data=c_nn.get_dicts(f'select id ,code from ifund where id >{cid} order by id asc limit 200')
            cid=data[-1]["id"]
            for row_b in data:
                try:
                    if row_b['code']==row_a['code']:
                        continue
                    # worker.submit(self.get_single_compare,row_a,row_b,a_position)
                    self.get_single_compare(row_a,row_b,a_position)
                except Exception as ex:
                    c_logger.error(f'one {ex}')
    def get_single_compare(self,row_a,row_b,position_a):
        try:
            c_nn=DBHelper(**db_conf)
            position_b=c_nn.get_dicts(f"select code from position where fcode='{row_b['code']}'")
            res=  [x for x in position_a if x in position_b]
            batch_insert=[]
            for item in res:
                a_insert=[row_a['code'],row_b['code'],item['code']]
                batch_insert.append(a_insert)
            if len(batch_insert)>self._similarity:
                try:
                    b_nn=DBHelper(**db_conf)
                    sql=f"select * from correlation where AFundCode='{batch_insert[0][0]}' and BFundCode='{batch_insert[0][1]}' and PCode='{batch_insert[0][2]}'"
                    if len(b_nn.get_dicts(sql))>0:
                        return
                    c_logger.info(f"similarity:{len(batch_insert)} { batch_insert}" )
                    sql='insert into correlation (AFundCode,BFundCode,PCode) values (%s,%s,%s)'
                    b_nn.execute_batch(sql,params=batch_insert)
                except  Exception as ex:
                    c_logger.error(f'insert into correlation error with {ex}')

        except Exception as ex:
            c_logger.error(f's_one {ex}')