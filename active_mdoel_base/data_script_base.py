#%%

import numpy as np
import pandas as pd
import xgboost as xgb
import sys, gc, os, glob, cysimdjson
from tqdm import tqdm
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from multiprocessing import Process
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score
from sklearn.metrics import classification_report
############################根据ip配置基础信息########################
from netifaces import interfaces, ifaddresses, AF_INET
base_path_config = {
    '10.225.136.101':{
        'wangweiqing':'/data-p4/sgs_mlai_dev/nbs/',
        'louxiaojun':'/home/louxiaojun/file/nbs/'
    },
    '10.225.21.248':{
        'wwq':'/devdata5/sgs_mlai_dev/nbs/',
        'lxj':'/home/lxj/sgs_program/nbs/'
    },
    '10.225.21.203':{
        'wwq':'/home/wwq/sgs_mlai_dev/nbs/',
        'lxj':'/home/lxj/sgs_program/nbs/'
    }
}

find_data_path_config = {
    '10.225.136.101':{
        'wangweiqing':'/data-p4/newsimlator/',
        'louxiaojun':'/data-p4/newsimlator/'
    },
    '10.225.21.248':{
        'wwq':'/devdata5/newsimlator/',
        'lxj':'/devdata5/newsimlator/'
    },
    '10.225.21.203':{
        'wwq':'/devdata2/smilator/',
        'lxj':'/devdata2/newsimlator/'
    }
}
def get_server_ip():
    for ifaceName in interfaces():
        addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
        if addresses[0] in base_path_config:
            return addresses[0]
server_ip = get_server_ip()
base_path = base_path_config[server_ip][os.getlogin()]
find_data_path = find_data_path_config[server_ip][os.getlogin()]
sys.path.append(base_path)
###########################################################################
from public_file.global_func_online import *
from public_file.global_define_online import *
from sgs_newmodel_ver1.xieyi21214new.publicfuc_kf2input import *

#%%
charid_spell = {1:31,2:33,5:37,8:53,9:57,11:62,12:56,13:60,22:65,24:68,25:69,27:296}
charid_lst = (6,15,17,18,19,23,210)
total_data = []
write_table_name = 'sgs_kf_map_21214'
# for schemas in ['sgs_data_schemas_203_mvp']:
    # # sql_lb = f'select kfpath from {schemas}.{write_table_name} where lcharid = 1 and lspell = 0 limit 50000'
    # data_liubei.extend(data_from_mysql(schemas, sql_lb, '10.225.136.101')['kfpath'].tolist())
schema_name = 'sgs_data_schemas_203_mvp'
table_name = 'sgs_kf_map_21214'
for lspell in [1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
               82, 83, 84, 85, 86, 87, 88, 89, 90, 200, 201]:
    sql_lb = f'select kfpath from {schema_name}.{table_name} where lcharid in {charid_lst} and lspell = {lspell} and lpid =21210 limit 10000'
    total_data.extend(data_from_mysql(schema_name, sql_lb)['kfpath'].tolist())
    print('lspell:', lspell, len(total_data))

    ##重铸
sql_lb = f'select kfpath from {schema_name}.{table_name} where lcharid in {charid_lst} and lspell = {85} and lpid =21209 limit 10000'
total_data.extend(data_from_mysql(schema_name, sql_lb)['kfpath'].tolist())
print('lspell:', lspell, len(total_data))

##请求弃牌
sql_lb = f'select kfpath from {schema_name}.{table_name} where lcharid in {charid_lst} and lspell = {0} and lpid =21219 limit 10000'
total_data.extend(data_from_mysql(schema_name, sql_lb)['kfpath'].tolist())
#%%

inputdata = []
parser = cysimdjson.JSONParser()
for i in tqdm(range(0, len(total_data))):
    file = total_data[i]
    with open(file, 'rb') as f:
        jdata = parser.parse(f.read())['SimulatorInfo']
    if int(jdata['Actioninfo'][0]['actionPID']) == 21214 and int(jdata['Actioninfo'][0]['actionType']) == 1:
        input = deal_base_activate_inputdata(jdata, int(jdata['Actioninfo'][0]['seatId']))
        input.append(file)
        inputdata.append(input)

#%%

target_cols = [
        'ailive','emery_alive_num','own_alive_number','emery_can_change','team_can_change',
        'phase_id', 'curseat', 'curheroid', 'curherosex','curherospell1', 'curherospell2', 'curherospell3', 'curheromaxhp', 'curherohp',
        'curcardnum', 'curnum_sha','curnum_huosha',
        'curnum_leisha','curnum_shan','curnum_tao','curnum_ssqy','curnum_ghcq','curnum_wgfd','curnum_wzsy','curnum_juedou','curnum_mmlq','curnum_wjqf',
        'curnum_flash','curnum_tyjy','curnum_wxkj','curnum_jdsr','curnum_lbss','curnum_bgz','curnum_chitu','curnum_zixin','curnum_dawam','curnum_jueying',
        'curnum_dilu','curnum_zhft','curnum_zglv','curnum_cxsgj','curnum_qgj','curnum_qlyyd','curnum_zbsm','curnum_gsf','curnum_fthj','curnum_qlg','curnum_jiu',
        'curnum_huogong','curnum_blcd','curnum_tslh','curnum_gdd','curnum_zqys','curnum_tengjia','curnum_byss','curnum_hualiu','curnum_rwd','curnum_hbj',
        'curnum_388','curnum_390','curnum_391','curnum_700','curnum_1128','curnum_1129','curnum_1131','curnum_1135',
        'curnum_2055','curnum_3060','curnum_3061','curnum_3063','curnum_6008','curnum_6009','curnum_6010',
        'curcolor1','curcolor2','curcolor3','curcolor4',
       'curarms_spell','curequis_spell','curadd1_spell','curreduce1_spell','curextar_spell',
       'curstate_jiu','curstate_flash','curstate_tslh','have_use_sha','cur_can_sha','need_give_up','taojiu_num',

       'friseat','friheroid', 'friherosex', 'friherospell1','friherospell2','friherospell3','friheromaxhp', 'friherohp', 'fricardnum',
       'frinum_total_sha', 'frinum_shan','frinum_tao', 'frinum_wxkj', 'frinum_jiu','friarms_spell','friequis_spell',
       'friadd1_spell','frireduce1_spell','friextar_spell','frijudge_lbss','frijudge_blcd',
       'frijudge_flash','fristate_tslh','fri_inrange_attr', 'fri_inrange_jn','fri_have_handcards',

       'nextheroid','nextherosex', 'nextherospell1','nextherospell2','nextherospell3','nextheromaxhp','nextherohp','nextcardnum','nextarms_spell','nextequis_spell','nextadd1_spell','nextreduce1_spell','nextextar_spell',
       'nextjudge_lbss','nextjudge_blcd','nextjudge_flash','nextstate_tslh','next_inrange_attr','next_inrange_jn','next_have_handcards','next_opposite_sex','next_be_lbss',
       'next_be_blcd','next_be_ssqy','next_be_ghcq','next_be_sha','next_be_juedou','next_attr_no_equis_distance',

       'otherheroid','otherherosex','otherherospell1','otherherospell2','otherherospell3','otherheromaxhp','otherherohp','othercardnum','otherarms_spell','otherequis_spell','otheradd1_spell','otherreduce1_spell','otherextar_spell',
       'otherjudge_lbss','otherjudge_blcd','otherjudge_flash','otherstate_tslh','other_inrange_attr','other_inrange_jn','other_have_handcards','other_opposite_sex','other_be_lbss',
       'other_be_blcd','other_be_ssqy','other_be_ghcq','other_be_sha','other_be_juedou','other_attr_no_equis_distance',

       'can_jdsr'
]
target_cols.extend(['action_idx','error','kf'])
len(target_cols)

#%%

sgs_data = pd.DataFrame(data=inputdata, columns=target_cols)
sgs_data.to_feather(f'/home/lxj/21214new_model/base/base_21214_10000_.feather')


