from Config.iconfig import idatabase
if __name__=='__main__':
    i=idatabase.get_dicts(" select *from demo ",convert=False)
    a=1