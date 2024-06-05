import pandas as pd
import numpy as np
import json, gc, sys, json, copy, glob,os
from tqdm import tqdm
############################根据ip配置基础信息########################
from netifaces import interfaces, ifaddresses, AF_INET
base_config = {
    '10.225.136.101':{
        'wangweiqing':{
            'base_path': '/data-p4/sgs_mlai_dev/nbs/',
            'mysql_ip': '10.225.136.101',
            'read_file_path':'/data-p4/specialsimulator/',
            'write_schemas':'new_data_101',
        },
        'louxiaojun': {
            'base_path': '/data-p4/sgs_mlai_dev/nbs/',
            'mysql_ip': '10.225.136.101',
            'read_file_path': '/data-p4/specialsimulator/',
            'write_schemas': 'new_data_101',
        }
    },
    '10.225.21.248':{
        'wwq':{
            'base_path': '/devdata5/sgs_mlai_dev/nbs/',
            'mysql_ip': '10.225.21.248',
            'read_file_path':'/devdata2/simulator100/',
            'write_schemas':'sgs_data_hero100_mvp',
            'find_idx': [22]#['{:02d}'.format(ii) for ii in range(22, 23)]
        }
    },
    '10.225.21.203':{
        'wwq':{
            'base_path': '/home/wwq/sgs_mlai_dev/nbs/',
            'mysql_ip': '10.225.136.101',
            'read_file_path':'/devdata2/smilator/',
            'write_schemas':'sgs_data_mvp_hero100_203',
        }
    }
}

def get_server_ip():
    for ifaceName in interfaces():
        addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
        if addresses[0] in base_config:
            return addresses[0]
server_ip = get_server_ip()
base_path = base_config[server_ip][os.getlogin()]['base_path']
find_data_path = base_config[server_ip][os.getlogin()]['read_file_path']
mysql_ip =  base_config[server_ip][os.getlogin()]['mysql_ip']
write_schemas = base_config[server_ip][os.getlogin()]['write_schemas']
sys.path.append(base_path)
###########################################################################
from public_file.global_define_online import *
from public_file.global_func_online import *

find_idx_list = base_config[server_ip][os.getlogin()]['find_idx']

find_data_path_base = [find_data_path + str(ii) for ii in find_idx_list]
save_dict_path = ''
### 数据抛入到redis中
write_table_name = 'sgs_kf_map_21214'
write_sql_type = 'append'
cols = ['apid','aspell','atype','lcharid','lpid','lspell','ltype','modeltype','gameid','timestamp','kfpath']
pd.DataFrame()

def pushDataToMysql(inlist):
    df = pd.DataFrame(data=inlist, columns=cols)
    write_to_mysql(df, write_schemas, write_table_name, write_sql_type, mysql_ip)
    del df
    gc.collect()

def get_subfolders(path):
    return np.sort([name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))])
numlist = [f"{num:02}" for num in range(1, 11)]

def getLcharid(jdata, seat):
    for player in jdata['Simulator']:
        if int(player['stateinfo']['baseinfo']['seatid']) == seat:
            return int(player['stateinfo']['baseinfo']['charid'])
    return 0


def deal_xieyi_data(jsondata):
    pid = jsondata['Labelinfo'][0]['actionPID']
    labelinfo = jsondata['Labelinfo'][0]
    target = ''
    cards = ''
    if pid == '21210':
        uspell = int(labelinfo['useCard']['spellId'])
        target = '' if int(labelinfo['useCard']['destCnt']) > 0 else '2'
        cards = '3'
    elif pid == '21212':
        uspell = int(labelinfo['useSpell']['spellId'])
        target = '' if int(labelinfo['useSpell']['destCount']) > 0 else '2'
        cards = '' if int(labelinfo['useSpell']['useCardCount']) > 0 else '3'
    elif pid == '21219':
        uspell = 0

    return pid,uspell,target,cards


def pushDataBy21214(ifiles):
    save_list_21214 = []
    for file in tqdm(ifiles):
        with open(file, 'r', encoding='utf-8-sig') as f:
            json_data = json.load(f)['SimulatorInfo']
        gameid = int(json_data['Gameinfo']['gameid'])
        timestamp = int(json_data['Gameinfo']['timestamp'])
        pid = int(json_data['Labelinfo'][0]['actionPID'])
        labelinfo = json_data['Labelinfo'][0]
        modeltype = '0'
        charid = getLcharid(json_data, int(labelinfo['seatId']))
        mtype = 0
        if pid == 21210:
            uspell = int(labelinfo['useCard']['spellId'])
        elif pid == 21212:
            uspell = int(labelinfo['useSpell']['spellId'])
            if uspell in total_ignore_spell:
                continue
        elif pid == 21219:
            uspell = 0
        elif pid == 21209 and int(json_data['Actioninfo'][0]['actionType']) == 2:#弃牌
            uspell = int(labelinfo['moveCard']['spellId'])
            mtype = int(labelinfo['moveCard']['typeMove'])
            modeltype = '6'
        elif pid == 21209 and int(labelinfo['moveCard']['typeMove']) == 12:#重铸
            modeltype = '0'
            mtype = int(labelinfo['moveCard']['typeMove'])
            uspell = 85
        else:
            continue 
        save_list_21214.append([21214, 0, 0, charid, pid, uspell, mtype, modeltype,gameid, timestamp, file])
    pushDataToMysql(save_list_21214)
        

def pushDataBy21217(ifiles):
    save_list_21217 = []
    for file in tqdm(ifiles):
        with open(file, 'r', encoding='utf-8-sig') as f:
            json_data = json.load(f)['SimulatorInfo']
        sourcespell = int(json_data['Actioninfo'][0]['triggerinfo']['triggerSpellId'])
        pid = int(json_data['Labelinfo'][0]['actionPID'])
        labelinfo = json_data['Labelinfo'][0]
        modeltype = '99'
        charid = getLcharid(json_data, int(labelinfo['seatId']))
        if pid == 21210:
            uspell = int(labelinfo['useCard']['spellId'])
            if uspell not in [3,82]:
                continue
            modeltype = '1:3'
        elif pid == 21212:
            uspell = int(labelinfo['useSpell']['spellId'])
            if uspell not in [940, 3132, 317, 3116, 64, 884, 469]:
                continue
            modeltype = '1:3'
        elif pid == 21219:
            uspell = 0
        else:
            continue 
        save_list_21217.append([21217, sourcespell, 0, charid, pid, uspell, 0, modeltype, file])
    pushDataToMysql(save_list_21217)


def pushDataBy21265(ifiles):
    save_list_21265 = []
    for file in tqdm(ifiles):
        with open(file, 'r', encoding='utf-8-sig') as f:
            json_data = json.load(f)['SimulatorInfo']
        sourcespell = int(json_data['Actioninfo'][0]['triggerinfoNew']['triggerParam'][0]['uSpellId'])
        pid = int(json_data['Labelinfo'][0]['actionPID'])
        labelinfo = json_data['Labelinfo'][0]
        modeltype = '99'
        charid = getLcharid(json_data, int(labelinfo['seatId']))
        if pid == 21210:
            uspell = int(labelinfo['useCard']['spellId'])
            if sourcespell  == 2 and uspell not in [2]:
                continue
            elif sourcespell  == 13 and  uspell not in [13]:
                continue
            modeltype = '1;2;3' if int(labelinfo['useCard']['destCnt']) > 0 else '1;3'

        elif pid == 21212:
            uspell = int(labelinfo['useSpell']['spellId'])
            if sourcespell  == 2 and uspell not in [37,46,940,976,800,968,884,3039,298,734,749,3103,469,3155]:
                continue
            elif sourcespell  == 13 and  uspell not in [371,317,968,884,3261,376,469,98]:
                continue
            elif sourcespell != uspell:
                continue
            modeltype = '1;2' if int(labelinfo['useSpell']['destCount']) > 0 else '1'
            modeltype =  f'{modeltype};3' if int(labelinfo['useSpell']['useCardCount']) > 0 else modeltype
        elif pid == 21219:
            uspell = 0
        else:
            continue 
        save_list_21265.append([21265, 0, 0, charid, pid, uspell, 0, modeltype, file])
    pushDataToMysql(save_list_21265)

#nohup python -u kf2xieyidict_21214.py > log_kf2xieyidict21214_02.log 2>&1 &
if __name__ == "__main__":
    for path in find_data_path_base:
        for sub in tqdm(range(1, 170)):
            if not os.path.exists(f"{path}/{sub}"):
                break
            files = glob.glob(f"{path}/{sub}/SimulatorInfo_21214_*")
            pushDataBy21214(files)
            