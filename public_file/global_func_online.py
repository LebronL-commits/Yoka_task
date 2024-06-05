
import numpy as np
import pandas as pd
import warnings, redis, os, gc
warnings.filterwarnings('ignore')
from sqlalchemy import create_engine

############################################################################################################
# reduce memory
def reduce_mem_usage(df, verbose=True):
    start_mem = df.memory_usage().sum() / 1024**2
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']

    for col in df.columns:
        col_type = df[col].dtypes
        if col_type in numerics:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
    if verbose:
        end_mem = df.memory_usage().sum() / 1024**2
        print('Memory usage after optimization is: {:.2f} MB'.format(end_mem))
        print('Decreased by {:.1f}%'.format(100 * (start_mem - end_mem) / start_mem))
    return df

def pathIsExistsAndMake(findpath):
    # 判断文件夹是否存在
    if not os.path.exists(findpath):
        # 如果文件夹不存在，则创建文件夹
        os.makedirs(findpath)


#字符串联
def contanctStr(basestr, addstr):
    basestr = basestr + ","+str(addstr)
    return basestr

#字符串合并
def concatStr(*infos):
    basestr = ""
    for info in infos:
        if not basestr:
            basestr = basestr + info
        else:
            basestr = basestr + "," + info
    return basestr

##################################################################################################
## 数据从数据库中读写
def pushDataToMysql(inlist, cols, schemas_name, table_name, sql_type, mysql_ip):
    df = pd.DataFrame(data=inlist, columns=cols)
    write_to_mysql(df, schemas_name, table_name, sql_type, mysql_ip)
    del df
    gc.collect()
### 定义
### write to mysql
def write_to_mysql(df, mysql, table_name, ifexists='replace', ip = '10.225.136.101'): 
    engine = create_engine(f'mysql+pymysql://root:123456@{ip}:3306/'+mysql)
    df.to_sql(table_name, con=engine, if_exists=ifexists, chunksize=10000, index=False)
    # with engine.connect() as con:
    #     con.execute("""ALTER TABLE `{}`.`{}` \
    #         ADD COLUMN `id` INT NOT NULL AUTO_INCREMENT FIRST, \
    #         ADD PRIMARY KEY (`id`);"""
    #             .format(mysql, table_name))

def write_to_mysql_inchunk(df, mysql, table_name, chunksize, ip = '10.225.136.101', ifexists='replace'):
    engine = create_engine('mysql+pymysql://root:123456@{ip}:3306/'+mysql)
    df.to_sql(table_name, con=engine, if_exists=ifexists, chunksize=chunksize, index=False)
    # with engine.connect() as con:
    #         con.execute("""ALTER TABLE `{}`.`{}` \
    #             ADD COLUMN `id` INT NOT NULL AUTO_INCREMENT FIRST, \
    #             ADD PRIMARY KEY (`id`);"""
    #                 .format(mysql, table_name))

### 从数据库中读取数据
def data_from_mysql(mysql, query_label,ip = '10.225.136.101'): 
    engine = create_engine(f'mysql+pymysql://root:123456@{ip}:3306/'+mysql)
    return pd.read_sql(query_label, engine)

### 从数据库中读取数据
def data_from_mysql_chunksize(mysql, query_label, ip = '10.225.136.101', csize = 100000, ): 
    engine = create_engine(f'mysql+pymysql://root:123456@{ip}/'+mysql)
    return pd.concat([chunk for chunk in pd.read_sql(query_label, engine, chunksize=csize)]) 


### 数据从redis获取
############################################################################################################
class RedispushClass:
    def __init__(self, redis_ip):
        self.keyname=' '
        self.connect_redis(redis_ip)
                
    def connect_redis(self, redis_ip):
        self.redis_conn = redis.Redis(host=redis_ip, port=6379, db=0,password='foobaredaabb')

    
    def get_loginfo(self ,irange1, irange2):
        pipe = self.redis_conn.pipeline(transaction=False)        
        pipe.lrange(self.keyname,irange1,irange2)            
        result = pipe.execute()
        return result
    
    def set_loginfo(self, data):
        pipe = self.redis_conn.pipeline(transaction=False)      
        pipe.lpush(self.keyname, data)            
        result = pipe.execute()
        return result
    
    def setkeyname(self, name):
        self.keyname=name

    def get_llen(self, key):
        return self.redis_conn.llen(key)

#获得log信息    
def GetLogInfo(keyname, redis_ip):
    redis_push = RedispushClass(redis_ip)
    redis_push.setkeyname(keyname)
    return redis_push.get_loginfo(0,-1)    

#获得log信息    
def GetLogLlen(keyname,  redis_ip):
    redis_push = RedispushClass(redis_ip)
    return redis_push.get_llen(keyname)

#获得log信息    
def GetInfoByRange(keyname, redis_ip, ranges = 0, rangee=-1):
    redis_push = RedispushClass(redis_ip)
    redis_push.setkeyname(keyname)
    return redis_push.get_loginfo(ranges, rangee)   

#设置log数据
def SetLogInfo(keyname, redis_ip, data):
    redis_push = RedispushClass(redis_ip)
    redis_push.setkeyname(keyname)
    return redis_push.set_loginfo(data)

############################################################################################################ 
import shutil
def delete_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

#############################################################################################################
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.metrics import classification_report
def print_precison_recall_f1(y_true, y_pre):
    """打印精准率、召回率和F1值"""
    print("打印精准率、召回率和F1值")
    print(classification_report(y_true, y_pre))
    f1 = round(f1_score(y_true, y_pre, average='macro'), 2)
    p = round(precision_score(y_true, y_pre, average='macro'), 2)
    r = round(recall_score(y_true, y_pre, average='macro'), 2)
    print("Precision: {}, Recall: {}, F1: {} ".format(p, r, f1))

