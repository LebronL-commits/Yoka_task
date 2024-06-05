#! /home/yoka/anaconda3/envs/xg102/bin/python
import shutil
# %%
import pandas as pd
import warnings, json, os, shutil, redis, copy, sys, glob
import numpy as np
from datetime import date
from tqdm import tqdm
from enum import Enum
warnings.filterwarnings('ignore')

############################根据ip配置基础信息########################
from netifaces import interfaces, ifaddresses, AF_INET
base_config = {
    '10.225.136.101':{
        'wangweiqing':{
            'base_path': '/data-p4/sgs_mlai_dev/nbs/',
            'mysql_ip': '10.225.136.101',
            'read_file_path':'/data-p4/specialsimulator/',
            'find_idx':['{:02d}'.format(ii) for ii in range(1, 11)]
        },
        'louxiaojun':{
            'base_path': '/home/louxiaojun/file/nbs/',
            'mysql_ip': '10.225.136.101',
            'read_file_path':'/home/louxiaojun/tianxiang_data/simulator/',
        }
       
    },
    '10.225.21.248':{
        'wwq':{
            'base_path': '/devdata5/sgs_mlai_dev/nbs/',
            'mysql_ip': '10.225.136.101',
            'read_file_path':'/devdata2/specialsimulator/',
            'find_idx':['{:02d}'.format(ii) for ii in range(21, 32)]
        },
        'lxj':{
            'base_path': '/home/lxj/sgs_program/nbs/',
            'mysql_ip': '10.225.136.101',
            'read_file_path':'/home/lxj/liuli_data_2/simulator',
        }
       
    },
    '10.225.21.203':{
        'wwq':{
            'base_path': '/home/wwq/sgs_mlai_dev/nbs/',
            'mysql_ip': '10.225.136.101',
            'read_file_path':'/devdata2/specialsimulator/',
            'find_idx':[ii for ii in range(11, 16)]
        },
        'lxj':{
            'base_path': '/home/lxj/sgs_program/nbs/',
            'mysql_ip': '10.225.136.101',
            'read_file_path':'/home/lxj/liuli_data_2/simulator',
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
find_idx = base_config[server_ip][os.getlogin()]['find_idx']
sys.path.append(base_path)
print(mysql_ip)
###########################################################################
    
from public_file.global_define_online import eZoneType
from public_file.global_func_online import data_from_mysql, delete_files_in_folder
# %%
timescnt = 0
playcard = pd.read_csv(base_path + "base_data_file/playcard.csv")
characters = pd.read_csv(base_path + "base_data_file/character.csv")

# %%
maxline = 2000
redis_key_index = '01'
# mysql_ip = '10.225.136.101'
file_index = 0

save_json_path = f'{find_data_path}/{redis_key_index}/{file_index}/'
temp_SimulatorInfo = f'{base_path}base_data_file/mlaiSimulatorInfo_template.json'

### 数据抛入到redis中
is_savetoredis = False
redis_server = 16
current_date = date.today().strftime("%m_%d").replace('_', '')
template = {}

read_schemas_name = 'ReplayBaseInfo'

class DataType(Enum):
    WinSeat = 0#赢家数据
    MVP     = 1#Mvp数据
    SMVP    = 2#MVP数据
    WinSeat_single = 4#赢家数据
    ANY = 5#所有数据
    FIND_HERO = 6


find_hero_list =  [ ]

def getDatasFromMysql(datatype, tableidx, findhero = 0):
    if datatype == DataType.WinSeat:
        #sql_label = f'select winseat1, winseat2, kfpath from {read_schemas_name}.{read_table_name}'
        sql_label = f'select winseat1, winseat2, kfpath from {read_schemas_name}.json_path_{tableidx} WHERE winheroid1 in (1, 4, 11, 30) or winheroid2 in (1, 4, 11, 30);'
        df = data_from_mysql(read_schemas_name, sql_label, '10.225.21.248')
        return df['kfpath'].tolist(), pd.Series(df[['winseat1', 'winseat2']].values.tolist(), index=df['kfpath']).to_dict()
    elif datatype == DataType.MVP:
        sql_label = f'select mvp, kfpath from {read_schemas_name}.json_path_{tableidx} WHERE mvphero in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,27,28,29,30,31,32,33,34,35,36,37,38,39,40,40,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,210,212)'
        df = data_from_mysql(read_schemas_name, sql_label)
        return df['kfpath'].tolist(), pd.Series(df[['mvp']].values.tolist(), index=df['kfpath']).to_dict()
    elif datatype == DataType.SMVP:
        sql_label = f'select smvp, kfpath from {read_schemas_name}.json_path_{tableidx}'
        df = data_from_mysql(read_schemas_name, sql_label)
        return df['kfpath'].tolist(), pd.Series(df[['smvp']].values.tolist(), index=df['kfpath']).to_dict()
    if datatype == DataType.WinSeat_single:
        #sql_label = f'select winseat1, winseat2, kfpath from {read_schemas_name}.{read_table_name}'
        sql_label = f'select winseat1, winseat2, kfpath from {read_schemas_name}.json_path_{tableidx} WHERE winheroid1 in (f{findhero}) or winheroid2 in (f{findhero});'
        df = data_from_mysql(read_schemas_name, sql_label)
        return df['kfpath'].tolist(), pd.Series(df[['winseat1', 'winseat2']].values.tolist(), index=df['kfpath']).to_dict()
    elif datatype == DataType.ANY:
        #sql_label = f'select winseat1, winseat2, kfpath from {read_schemas_name}.{read_table_name}'
        sql_label =  f'select mvp, kfpath from {read_schemas_name}.json_path_{tableidx} WHERE player1 in (1,3,5,6,7,8,16,17,18,20,21,23,24,26,29,34,35,39,51,54,103,107,108,112,118,131,153,158,161,164,175,177,185,202,207,299,300,301,302,303,306,307,308,310,311,314,315,316,319,323,326,328,339,344,357,361,365,374,378,379,392,393,406,408,410,411,414,415,430,431,440,441,442,443,445,448,450,451,452,458,462,463,466,480,484,485,498,500,523,526,527,532,534,552,7000,7001,7002,7004,7005,7019) and player2 in (1,3,5,6,7,8,16,17,18,20,21,23,24,26,29,34,35,39,51,54,103,107,108,112,118,131,153,158,161,164,175,177,185,202,207,299,300,301,302,303,306,307,308,310,311,314,315,316,319,323,326,328,339,344,357,361,365,374,378,379,392,393,406,408,410,411,414,415,430,431,440,441,442,443,445,448,450,451,452,458,462,463,466,480,484,485,498,500,523,526,527,532,534,552,7000,7001,7002,7004,7005,7019) and player3 in (1,3,5,6,7,8,16,17,18,20,21,23,24,26,29,34,35,39,51,54,103,107,108,112,118,131,153,158,161,164,175,177,185,202,207,299,300,301,302,303,306,307,308,310,311,314,315,316,319,323,326,328,339,344,357,361,365,374,378,379,392,393,406,408,410,411,414,415,430,431,440,441,442,443,445,448,450,451,452,458,462,463,466,480,484,485,498,500,523,526,527,532,534,552,7000,7001,7002,7004,7005,7019) and player4 in (1,3,5,6,7,8,16,17,18,20,21,23,24,26,29,34,35,39,51,54,103,107,108,112,118,131,153,158,161,164,175,177,185,202,207,299,300,301,302,303,306,307,308,310,311,314,315,316,319,323,326,328,339,344,357,361,365,374,378,379,392,393,406,408,410,411,414,415,430,431,440,441,442,443,445,448,450,451,452,458,462,463,466,480,484,485,498,500,523,526,527,532,534,552,7000,7001,7002,7004,7005,7019)'
        df = data_from_mysql(read_schemas_name, sql_label,ip = mysql_ip)
        return df['kfpath'].tolist(), pd.Series(df[['mvp']].values.tolist(), index=df['kfpath']).to_dict()
    elif datatype == DataType.FIND_HERO:
        #sql_label = f'select winseat1, winseat2, kfpath from {read_schemas_name}.{read_table_name}'
        sql_label = f'select mvp, kfpath from {read_schemas_name}.json_path_{tableidx} WHERE mvphero = {findhero}'
        df = data_from_mysql(read_schemas_name, sql_label)
        return df['kfpath'].tolist(), pd.Series(df[['mvp']].values.tolist(), index=df['kfpath']).to_dict()
    
def pathIsExists(findpath):
    # 判断文件夹是否存在
    if not os.path.exists(findpath):
        # 如果文件夹不存在，则创建文件夹
        os.makedirs(findpath)

pathIsExists(save_json_path)

def getColorAndNumberAndSpell(card):
    item = playcard.loc[playcard['id'] == card]
    if len(item) < 1:
        return -1, -1, '', -1

    color, name, spell, subType = getattr(item, 'color').values, getattr(item, 'name').values, getattr(item, 'spellId').values, getattr(
        item, 'subType').values
    return color[0], name[0], spell[0], subType[0]

def getJudgeSpellInfo(card):
    color, name, spell, _  = getColorAndNumberAndSpell(card)
    if name == '乐不思蜀':
        return spell, color
    elif name == '兵粮寸断':
        return spell, color
    elif name == '闪电':
        return spell, color
    elif color == 2:#方块牌
        return 15, color
    elif color in [3,4]:#黑色
        return 84, color
    else:
        print("JudgeSpell error ")
    return -1, -1

icon_give_label = False
# 当前武将信息
player_hero_list = []
game_phase_id = 0
play_seat = 0
game_model = 0
save_simulatfiles_list = []
cur_file_name = ''
table_stack_info = {}
table_spell_info = {}
is_special_spell = 0
gameid = '000000'
timestamp = '00000000'

def pushDataToRedis(jsondata):
    if not is_savetoredis:
        return
    redis_conn = redis.Redis(host = mysql_ip, port=6379, db=0,password='foobaredaabb')
    key = f'kf_{redis_server}_{current_date}_{redis_key_index}'
    redis_conn.rpush(key, json.dumps(jsondata))

class Player():
    figure = 0
    characterID = 0
    country = 0
    maxhp = 0
    curhp = 0
    gender = 0
    isTurnOver = 0
    phase = 0
    lbss_state = 1##1是红桃 0是非红桃
    maxhandcardnum = 0
    roundplaycard = 0
    def __init__(self, seat_id, role_id):
        self.seatid = seat_id
        self.roleid = role_id
        self.handcards = []
        self.equipinfo = []
        self.judgeinfo = []
        self.spellInfoList = []
        self.skillinfo = []
        self.removeinfo = {700:[], 6:[], 52:[], 945:[], 869:[],35:[], 724:[],304:[],818:[], 55:[]}
        self.stateinfo = []
        

    def reset(self):
        self.roleid = 0
        self.handcards = []
        self.equipinfo = []
        self.judgeinfo = []
        self.figure = 0
        self.characterID = 0
        self.country = 0
        self.spellInfoList = []
        self.maxhp = 0
        self.curhp = 0
        self.removeinfo = {700:[], 6:[], 52:[], 945:[], 869:[],35:[], 724:[],304:[],818:[], 55:[]}#52, 945, 869, 35, 724
        self.stateinfo = []
        self.skillinfo = []
        self.isTurnOver = 0
        self.gender = 0
        self.phase = 0
        self.maxhandcardnum = 0
        self.roundplaycard = 0
        self.lbss_state = 1##1是红桃 0是非红桃

    def add_handcard(self, card):
        if card not in self.handcards:
            self.handcards.append(card)
    
    def remove_handcard(self, card):
        if card in self.handcards:
            self.handcards.remove(card)

    def add_equiscard(self, card):
        if card not in self.equipinfo:
            self.equipinfo.append(card)
    
    def remove_equiscard(self, card):
        if card in self.equipinfo:
            self.equipinfo.remove(card)
    
    def add_judgecard(self, card):
        if card not in self.judgeinfo:
            self.judgeinfo.append(card)
    
    def remove_judgecard(self, card):
        if card in self.judgeinfo:
            self.judgeinfo.remove(card)

    def add_removecard(self, spell, card):
        if spell not in self.removeinfo:
            self.removeinfo[spell] = []
            self.removeinfo[spell].append(card)
        elif card not in self.removeinfo[spell]:
            self.removeinfo[spell].append(card)

    def remove_removecard(self, spell, card):
        if card in self.removeinfo[spell]:
            self.removeinfo[spell].remove(card)

    def updateTurnOver(self, state):
        self.isTurnOver = state

table_players = []
opt_info_21220 = []
status_temp_save = []
# 根据座位号获取玩家
def get_player_by_seat(seat):
    for player in table_players:
        if player.seatid == seat:
            return player
    return -1

#桌子信息
def deal_xieyi_21208(jdata):
    global table_players
    table_players.clear()
    global game_model
    global save_simulatfiles_list
    save_simulatfiles_list = []
    game_model = jdata['model']
    for item in jdata['seatinfo']:
        if item['role_id'] > 0 and item['seat_id'] != 255:
            table_players.append(Player(item['seat_id'], item['role_id']))
        else:
            break
    
## 身份展示
def deal_xieyi_21223(jdata):
    templay = get_player_by_seat(jdata['SeatID'])
    if templay == -1:
        return
    ## 设置frigure
    templay.figure = jdata['Figure']

##玩家设置
def deal_xieyi_21227(jdata):
    global player_hero_list
    player_hero_list = []

    for item in jdata['Infos']:
        templay = get_player_by_seat(item['SeatID'])
        if templay == -1:
            continue
        ## 设置frigure
        templay.characterID = item['CharacterID']
        templay.country = item['Country']
        player_hero_list.append(item['CharacterID'])
##玩家设置

##玩家设置
skillinfo = {'skillid':str(0), 'dataCnt':str(0), 'datas':"","skilltimes":"0"}
stateinfo = {'skillid':str(0), "statusvalue":"0"}

def isHaveSpell(templay, spell):
    for item in templay.skillinfo:
        if item['skillid'] == spell:
            return True
    return False

def isHaveState(templay, spell):
    for item in templay.stateinfo:
        if item['skillid'] == spell:
            return True
    return False


def deal_xieyi_21213(jdata):
    global game_phase_id
    global play_seat
    global status_temp_save
    global is_special_spell
    global table_spell_info
    global table_stack_info
    
    play_seat = jdata['SeatID']
    templay = get_player_by_seat(jdata['SeatID'])
    if templay == -1:
        return
    templay.phase = jdata['Round'] if jdata['Round'] != 8 else 0
    status_temp_save = []
    is_special_spell = 0
    save_simulatInfo(21213, {"open": "1","actionType": str(jdata['Round']), "seatId":str(jdata['SeatID']), "actionPID": str(jdata['id'])})
    if jdata['Round'] == 8:
        table_spell_info = {}
        table_stack_info = {}
        templay.lbss_state = 1
    ##重置回合的出牌数量
    for i in range(4):
        templay = get_player_by_seat(i)
        if templay == -1:
            continue
        templay.roundplaycard = 0

def save_simulatInfo(name,  Actioninfo, spell = 0):
    global template
    template = {}

    with open(temp_SimulatorInfo, 'r', encoding='utf-8-sig') as j:
        template = copy.deepcopy(json.load(j)) 
    template['SimulatorInfo']['Gameinfo']['gamemodel'] = str(game_model)
    template['SimulatorInfo']['Gameinfo']['gameid'] = gameid
    template['SimulatorInfo']['Gameinfo']['timestamp'] = timestamp
    for i in range(len(table_players)):
        if table_players[i].characterID != 0:
            tempdict = {}
            tempdict['id'] = str(i)
            tempdict['stateinfo'] = {}
            ### 基础信息 baseinfo
            tempdict['stateinfo']['baseinfo'] = {}
            tempdict['stateinfo']['baseinfo']['isdead'] = str(0)
            tempdict['stateinfo']['baseinfo']['seatid'] = str(table_players[i].seatid)
            tempdict['stateinfo']['baseinfo']['charid'] = str(table_players[i].characterID)
            tempdict['stateinfo']['baseinfo']['maxhp'] = str(table_players[i].maxhp)
            tempdict['stateinfo']['baseinfo']['curhp'] = str(table_players[i].curhp)
            tempdict['stateinfo']['baseinfo']['gender'] = str(table_players[i].gender)
            tempdict['stateinfo']['baseinfo']['country'] = str(table_players[i].country)
            tempdict['stateinfo']['baseinfo']['isTurnOver'] = str(table_players[i].isTurnOver)
            tempdict['stateinfo']['baseinfo']['curPhase'] = str(table_players[i].phase)
            tempdict['stateinfo']['baseinfo']['lbss_state'] = str(table_players[i].lbss_state)
            tempdict['stateinfo']['baseinfo']['roundplaycard']  = str(table_players[i].roundplaycard)
            tempdict['stateinfo']['baseinfo']['maxhandcardnum']  = str(table_players[i].maxhandcardnum)
            ###charinfo
            tempdict['stateinfo']['baseinfo']['charinfo']=[str(table_players[i].characterID), ';'.join([str(c) for c in table_players[i].spellInfoList])]
            ###技能信息 skillinfo
            tempdict['stateinfo']['skillinfo'] = []
            for spellinfo in table_players[i].skillinfo:
                tempdict['stateinfo']['skillinfo'].append(spellinfo)
            ###状态信息 statusinfo
            tempdict['stateinfo']['statusinfo'] = []  
            for sinfo in table_players[i].stateinfo:
                tempdict['stateinfo']['statusinfo'].append(sinfo) 

            if table_players[i].characterID == 27:
                for item in status_temp_save:
                    if item['spell'] == 296:
                        tempdict['stateinfo']['statusinfo'].append( {
                        "skillid": "296666",
                        "statusvalue": str(item['value'])
            },)
            ###手牌数据 handinfo
            tempdict['stateinfo']['handinfo'] = {}
            if len(table_players[i].handcards) > 0:
                tempdict['stateinfo']['handinfo']['cards'] = ';'.join([str(c) for c in table_players[i].handcards])
            ###装备数据 equipinfo
            tempdict['stateinfo']['equipinfo'] = {}
            if len(table_players[i].equipinfo) > 0:
                tempdict['stateinfo']['equipinfo']['cards'] = ';'.join([str(c) for c in table_players[i].equipinfo])
            ### 判定数据 judgeinfo
            tempdict['stateinfo']['judgeinfo'] = []
            for card in table_players[i].judgeinfo:
                retspell, retcolor = getJudgeSpellInfo(card)
                tempdict['stateinfo']['judgeinfo'].append({'cardid':str(card), 'spellid':str(retspell),'color':str(retcolor)})
            ## 共享区域
            tempdict['stateinfo']['removeinfo'] = []
            for key in table_players[i].removeinfo:
                if len(table_players[i].removeinfo[key]) > 0:
                    tempdict['stateinfo']['removeinfo'].append({'spellid':str(key), 'cards':[str(c) for c in table_players[i].removeinfo[key]] })
            ##数据保存
            template['SimulatorInfo']['Simulator'].append(tempdict)
        else:
            tempdict = {}
            tempdict['id'] = str(i)
            tempdict['stateinfo'] = {}
            ### 基础信息 baseinfo
            tempdict['stateinfo']['baseinfo'] = {}
            tempdict['stateinfo']['baseinfo']['isdead'] = str(1)
            tempdict['stateinfo']['baseinfo']['seatid'] = str(table_players[i].seatid)
            tempdict['stateinfo']['baseinfo']['charid'] = str(0)
            tempdict['stateinfo']['baseinfo']['maxhp'] = str(0)
            tempdict['stateinfo']['baseinfo']['curhp'] = '0'
            tempdict['stateinfo']['baseinfo']['gender'] = '0'
            tempdict['stateinfo']['baseinfo']['country'] = '0'
            tempdict['stateinfo']['baseinfo']['isTurnOver'] = '0'
            tempdict['stateinfo']['baseinfo']['curPhase'] = '0'
            tempdict['stateinfo']['baseinfo']['charinfo'] = []
            tempdict['stateinfo']['baseinfo']['lbss_state'] = '1'
            tempdict['stateinfo']['baseinfo']['roundplaycard']  = '0'
            tempdict['stateinfo']['baseinfo']['maxhandcardnum']  = '0'
            tempdict['stateinfo']['handinfo'] = {}
            tempdict['stateinfo']['equipinfo'] = {}
            tempdict['stateinfo']['skillinfo'] = []
            tempdict['stateinfo']['statusinfo'] = []  
            tempdict['stateinfo']['judgeinfo'] = []
            tempdict['stateinfo']['removeinfo'] = []

            template['SimulatorInfo']['Simulator'].append(tempdict)
   
    template['SimulatorInfo']['TableInfo'] = {
        'SpellZoneinfo':[],'StackZoneinfo':[],
    }  
    for key, value in table_stack_info.items():
        template['SimulatorInfo']['TableInfo']['StackZoneinfo'] = {'spellid': str(key), 'cards':";".join([str(i) for i in value])}
        break
    
    for key, value in table_spell_info.items():
        template['SimulatorInfo']['TableInfo']['SpellZoneinfo'].append({'spellid': str(key), 'cards':';'.join([str(i) for i in value])})

     # 写入修改后的数据回 JSON 文件sda
    #
          ### 报错动作数据
    template['SimulatorInfo']['Actioninfo'] = []
    template['SimulatorInfo']['Actioninfo'].append(Actioninfo)
    global timescnt
    save_simulatfiles_list.append(f'SimulatorInfo_{name}_{spell}_{timescnt}.json')
    # with open(f'{save_json_temp_path}SimulatorInfo_{name}_{spell}_{timescnt}.json', 'w') as file:
    #     json.dump(template, file, indent=2)  # indent 参数用于指定缩进的空格数，使输出更易读`
    timescnt += 1

def deal_xieyi_21214(jdata):
    global table_spell_info
    global table_stack_info
    table_stack_info = {}
    global is_special_spell
    is_special_spell = 0
    save_simulatInfo(21214, {"open": "1","actionType": str(jdata['Type']), "seatId":str(jdata['SeatID']),"actionPID": str(jdata['id']), "param":str(jdata['DiscardCount'])})
   
def deal_xieyi_21265(jdata):
    data_info_21265 = { "open": str(1),
                        "actionType":str(5),
                        "seatId":str( jdata["TriggerSpellData"][0]['SeatId']),
                        "actionPID": str(21265),}
    data_info_21265['triggerinfoNew'] = {
        "triggerSeatId": str(jdata['TriggerSeatId']),
        "srcSpellCasterSeat": str(jdata['SrcSpellCasterSeat']),
        "spellCasterchrId": str(jdata['SpellCasterchrId']),
        "srcSpellId": str(jdata['SrcSpellID']),
        "uTriggerSpellCnt": str(jdata['TriggerSpellCnt']),
        'triggerParam':[]
    }

    for param in jdata["TriggerSpellData"]:
        tempdict = {"uIndex": str(param['Idx']),
                    "uSpellId": str(param['SpellId']),
                    "uCount": str(param['Count']),
                    "uSeatId": str(param['SeatId']),
                    "uChrId": str(param['CharacterId']),
                    "uMark": str(param['Mark']),
                    "uTargetCnt":str(len(param['Targets'])) ,
                    "uCardCnt": str(len(param['Cards'])),
                    "uDataCnt":str(len(param['Datas'])),
                    "TargetValue": ';'.join([str(t) for t in param['Targets']]),
                    "CardValue": ';'.join([str(t) for t in param['Cards']]),
                    "DataValue": ';'.join([str(t) for t in param['Datas']]),}
        data_info_21265['triggerinfoNew']['triggerParam'].append(tempdict)
    save_simulatInfo(21265, data_info_21265, jdata["TriggerSpellData"][0]['SpellId'])

def deal_xieyi_21217(jdata):
    data_info_21217 = {
        'open':'1',
        'actionPID':str(jdata['id']),
        'actionType':str(jdata['SpellID']),
        'seatId':str(jdata['SeatID']),
        "triggerinfo": {
                    'triggerSeatId':str(jdata['SeatID']),
                    'targetSeatId':str(jdata['targetSeatID']),
                    'srcSpellCasterSeat':str(jdata['SrcSeatID']),
                    'srcSpellId':str(jdata['SrcSpellID']),
                    'triggerSpellId':str(jdata['SpellID']),
                    'GeneralID':str(jdata['GeneralID']),
                    'skillIndex':str(jdata['skillIndex']),
        },
       
    }
    save_simulatInfo(21217, data_info_21217, jdata['SrcSpellID'])

def deal_xieyi_21215(jdata):
    global is_special_spell
    opt_type = int(jdata['Type'])
    spell_id = jdata['SpellID']

    if spell_id == 3053 and opt_type == 29 and len(jdata['Params']) == 0:
        return
    if spell_id == 900 and opt_type == 30 and len(jdata['Params']) == 0:
        return

    data_info_21215 = {
        'open':'1',
        'actionPID':str(jdata['id']),
        'actionType':str(jdata['Type']),
        'seatId':str(jdata['SeatID']),
        'optTargetParam':{
            'optSeatId':str(jdata['SeatID']),
            'targetSeatId':str(jdata['targetSeatID']),
            'spellCasterSeat':str(jdata['SrcSeatID']),
            'spellId':str(jdata['SpellID']),
            'optType':str(jdata['Type']),
            'param':str(jdata['Param']),
            'dataCnt':';'.join([str(t) for t in jdata['Params']]),
        }
       
    }
    save_simulatInfo(21215, data_info_21215, jdata['SpellID'])

    if opt_type == 2 and spell_id in [364, 704]:
        is_special_spell = spell_id
    elif opt_type == 24 and spell_id in [127, 128]:
        is_special_spell = spell_id
    elif opt_type == 8 and spell_id in [115, 118, 3190]:
        is_special_spell = spell_id
    elif opt_type == 28 and spell_id in [3123, 713, 485, 3204]:
        is_special_spell = spell_id
    elif opt_type == 4 and spell_id in [83]:
        is_special_spell = spell_id
    elif opt_type == 3 and spell_id in [304]:
        is_special_spell = spell_id
    elif opt_type == 5 and spell_id in [24]:
        is_special_spell = spell_id


def save_simulatInfo_addaction(name,  labelinfo, spell = 0):
    global template
    if len(save_simulatfiles_list) == 0:
        return
    # with open(save_simulatfiles_list[-1], 'r', encoding='utf-8-sig') as j:
    #     template = copy.deepcopy(json.load(j)) deal_xieyi_21219

    ##移牌不应该跟使用技能
    if name == 21212 and int(template['SimulatorInfo']['Actioninfo'][0]['actionPID']) == 21215 and  int(template['SimulatorInfo']['Actioninfo'][0]['optTargetParam']['optType']) in [1,2,3,4]:
        return 
    # ## 已经有了 就不在保存了
    if name == 21219 and int(template['SimulatorInfo']['Actioninfo'][0]['actionPID']) == 21215 and \
        'Labelinfo' in template['SimulatorInfo'] and template['SimulatorInfo']['Labelinfo'][0]['actionPID'] == 21219:
        return 
    
    aspell = int(template['SimulatorInfo']['Actioninfo'][0]['actionPID'])

    template['SimulatorInfo']['TableInfo'] = {
        'SpellZoneinfo':[],'StackZoneinfo':[],
    }
    for key, value in table_stack_info.items():
        template['SimulatorInfo']['TableInfo']['StackZoneinfo'] = {'spellid': str(key), 'cards':";".join([str(i) for i in value])}
        break

    for key, value in table_spell_info.items():
        template['SimulatorInfo']['TableInfo']['SpellZoneinfo'].append({'spellid': str(key), 'cards':';'.join([str(i) for i in value])})

    template['SimulatorInfo']['KFRecoverInfo'] = opt_info_21220


    template['SimulatorInfo']['Labelinfo'] = []
    template['SimulatorInfo']['Labelinfo'].append(labelinfo)
    global timescnt
    save_simulatfiles_list.append(f'{save_json_path}SimulatorInfo_{aspell}_{timescnt}_{spell}_{gameid}.json')
    pushDataToRedis(template)
    # if int(labelinfo['seatId']) in [1, 4, 11, 30]:
    with open(f'{save_json_path}SimulatorInfo_{aspell}_{timescnt}_{spell}_{gameid}.json', 'w') as file:
        json.dump(template, file, ensure_ascii=False, indent=None)  # indent 参数用于指定缩进的空格数，使输出更易读`
    timescnt += 1

def deal_xieyi_21219(jdata):
    actionPID = str(21219)
    optType = str(jdata['Type'])
    labelinfo = {'actionPID':actionPID, 'seatId':str(jdata['SeatID']),"roleOpt":{'seatId':str(jdata['SeatID']),'optType':optType, }}
    save_simulatInfo_addaction(21219,  labelinfo, optType)

def deal_xieyi_21210(jdata):
    if jdata['CardID'] == 0:
        return 
    labelinfo = {'actionPID':str(jdata['id']),'seatId':str(jdata['SeatID']), 'useCard':{
        'srcSeatId':str(jdata['SeatID']),
        'cardId':str(jdata['CardID']), 'spellId':str(jdata['spellID']), 
                 'fromZone':str(jdata['fromZone']), 'usetype':str(jdata['useType']),
                 'destCnt':str(len(jdata['DestSeatIDs'])),'datas':';'.join([str(c) for c in jdata['DestSeatIDs']]),
                 'paramCnt':str(len(jdata['Params'])), 'useParam': ';'.join([str(c) for c in jdata['Params']])
    } }
    save_simulatInfo_addaction(21210,  labelinfo, jdata['spellID'])

    templay = get_player_by_seat(jdata['SeatID'])
    if templay == -1:
        return
    templay.roundplaycard += 1


def deal_xieyi_21212(jdata):
    global status_temp_save
    if jdata['card_count'] > 0:
        for card in jdata['CardIDs']:
            if card == 0:
                return 
    if jdata['SpellID'] in [88, 89, 200] :
        return 
    if jdata['SpellID'] == 296:
        status_temp_save.append:({'srcSeatId':jdata['SeatID'], 'spellID':296, 'value':jdata['Params'][0]})

    labelinfo = {'actionPID':str(jdata['id']),'seatId':str(jdata['SeatID']), "useSpell": {
                 'srcSeatId':str(jdata['SeatID']), 'seatId':str(jdata['SkillOwerSeatID']), 
                 'spellId':str(jdata['SpellID']), 'chrId':str(jdata['GeneralID']), 
                 'spellIndex':str(jdata['GeneralIndex']),
                 'effectIndex':str((jdata['EffectIndex'])),
                 'destCount':str(jdata['dest_Count']),'user_param0':str(jdata['Params'][0]),'user_param1':str(jdata['Params'][1]),
                 'useCardCount':str(jdata['card_count']), 'datas': ';'.join([str(c) for c in jdata['DestSeatIDs']])+ ';'+';'.join([str(c) for c in jdata['CardIDs']])}}
    save_simulatInfo_addaction(21212,  labelinfo, jdata['SpellID'])

    templay = get_player_by_seat(jdata['SeatID'])
    if templay == -1:
        return
    templay.roundplaycard += jdata['card_count'] 

def deal_xieyi_21220(jdata):
    global opt_info_21220
    if len(save_simulatfiles_list) == 0:
        return
    
    # with open(save_simulatfiles_list[-1], 'r', encoding='utf-8-sig') as j:
    #     template = copy.deepcopy(json.load(j)) 
    actionPID = str(jdata['id'])
    optType = str(jdata['Type'])
    if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] == '21214' and jdata['Type'] in [27,21]:
        actionPID = str(21219)
        optType = str(jdata['Type'])
        return
    
    if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] == '21217':
        return
    
    labelinfo = {'actionPID':actionPID, 'seatId':str(jdata['SeatID']),"spellOpt":{ 'seatId':str(jdata['SeatID']), 'optType':optType, 'SpellId':str(jdata['SpellID']), 'dataCnt':str(jdata['data_count']), 
                 'datas': ';'.join([str(c) for c in jdata['Datas']])}}

    if (jdata['Type'] == 11 and jdata['data_count'] == 0) :
        return
    if jdata['Type'] in [51, 26, 29]:
        return
    
    if jdata['Type'] == 7 and jdata['SpellID'] == 15:
        templay = get_player_by_seat(jdata['SeatID'])
        if templay == -1:
            return
        templay.lbss_state = jdata['Datas'][0]#1是红桃 0是非红桃
        return
    
    if jdata['Type'] in [0] and jdata['SpellID'] == 221 and jdata['data_count'] == 0:
        return
    
    if jdata['Type'] in [22] and jdata['SpellID'] == 3301 and jdata['data_count'] == 0:
        return
    
    if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] in ['21265', '21217']:
        return

    if  jdata['Type'] not in [26, 21]:
        opt_info_21220 =[ {
            'seatId':str(jdata['SeatID']),
            'actionPID':actionPID,
            "spellOpt":{ 'seatId':str(jdata['SeatID']), 'optType':optType, 'SpellId':str(jdata['SpellID']), 'dataCnt':str(jdata['data_count']),
                    'datas': ';'.join([str(c) for c in jdata['Datas']])}}]

    save_simulatInfo_addaction(f'{actionPID}_{optType}',  labelinfo, jdata['SpellID'])

def deal_xieyi_21216(jdata):
    templay = get_player_by_seat(jdata['SeatID'])
    if templay == -1:
        return
    if jdata['Mark'] == 32 or ('isMaxHp' in jdata and jdata['isMaxHp'] == True) :
        templay.maxhp = jdata['HP']
    else:
        templay.curhp = jdata['HP']

    if (jdata['SpellID'] in [882,818,215,3235,7000,439,701, 382,463,495,709,967, 3122, 3202, 3236, 784, 3072, 111, 126, 212, 49, 397,8,3262, 460, 3253, 397, 92, 884,757,313,3085,930,3262,91,111,126,118,305,407,460,467,471,651,681,713,757,784,852,884,930,957,975,1113,2023,1521,1609,7005]) :
        labelinfo = {'actionPID':str(jdata['id']),'seatId':str(jdata['SeatID']), 'useCard':{
            'srcSeatId':str(jdata['SeatID']),
                'spellId':str(jdata['SpellID']),
                'hp':str(jdata['HP']),
                'Mark':str(jdata['Mark']),
                'MurderSeatID':str(jdata['MurderSeatID']),
        } }
        save_simulatInfo_addaction(21216,  labelinfo, jdata['SpellID'])

def deal_xieyi_21241(jdata):
    templay = get_player_by_seat(jdata['SeatID'])
    if templay == -1 or templay.characterID == 0:
        return 
    templay.reset()


def deal_xieyi_21373(jdata):
    apid = int(template['SimulatorInfo']['Actioninfo'][0]['actionPID'])
    if apid != 21215:
        return 

    attype = int(template['SimulatorInfo']['Actioninfo'][0]['optTargetParam']['optType'])
    aspell = int(template['SimulatorInfo']['Actioninfo'][0]['optTargetParam']['spellId'])
    fspell = jdata['fromSpellId']
    if apid == 21215 and  attype in [28,29] and fspell in [3216,3126,3372,3302,3301,9008,3300,3334,7029] and aspell in [3216,3126,3372,3301,3302,9008,3300,7029,3334] :
        labelinfo = {'actionPID':str(jdata['id']),'seatId':str(jdata['castSeatId']), 'usespell':{
            'castSeatId':str(jdata['castSeatId']),
                'spellId':str(jdata['spellId']),
                'fromSpellId':str(jdata['fromSpellId']),
                'destCnt':str(jdata['destCnt']),
                'color':str(jdata['color']),
                'spellType':str(jdata['spellType']),
                'type':str(jdata['type']),
                'destCnt':str(jdata['destCnt']),
                'cardIds': ';'.join([str(c) for c in jdata['cardIds']]),
                'datas': ';'.join([str(c) for c in jdata['datas']]),
        } }
        save_simulatInfo_addaction(21373,  labelinfo, jdata['fromSpellId'])

def deal_xieyi_21252(jdata):
    templay = get_player_by_seat(jdata['SeatID'])
    if templay == -1:
        return 
    
    if jdata['IsSpell'] == True:#技能状态
        if not isHaveSpell(templay, str(jdata['DataID'])) and jdata['DataID'] not in [1443, 6006, 724, 84, 51, 52, 60, 61, 700] :
            cpstateinfo = copy.deepcopy(skillinfo)
            cpstateinfo['skillid'] = str(jdata['DataID'])
            cpstateinfo['dataCnt'] = str(jdata['data_count'])
            cpstateinfo['skilltimes'] = str(jdata['Datas'][-1]) if jdata['data_count'] > 0 else 0
            cpstateinfo['datas'] = ';'.join([str(i) for i in jdata['Datas']])
            templay.skillinfo.append(cpstateinfo)
        else:
            for item in templay.skillinfo:
                if item['skillid'] == str(jdata['DataID']):
                    item['dataCnt'] = str(jdata['data_count'])
                    item['skilltimes'] = str(jdata['Datas'][-1]) if jdata['data_count'] > 0 else 0
                    item['datas'] = ';'.join([str(i) for i in jdata['Datas']] )
                    break
        if len(template) == 0:
            return
        apid = int(template['SimulatorInfo']['Actioninfo'][0]['actionPID'])

        if apid != 21215:
            return 
        attype = int(template['SimulatorInfo']['Actioninfo'][0]['optTargetParam']['optType'])
        aspell = int(template['SimulatorInfo']['Actioninfo'][0]['optTargetParam']['spellId'])
        StateID = jdata['DataID']
        if apid == 21215 and  attype ==28 and StateID == 881 and aspell == 881 and jdata['data_count'] > 0 and jdata['Datas'][0] != 0:
            labelinfo = {'actionPID':str(jdata['id']),'seatId':str(jdata['SeatID']), 'stateinfo':{
                'dataID':str(jdata['DataID']),
                'IsSpell': '1' if jdata['IsSpell'] else '0',
                'data_count':str(jdata['data_count']),
                'datas': ';'.join([str(c) for c in jdata['Datas']]),
            } }
            save_simulatInfo_addaction(21252,  labelinfo, aspell)
    else:
        if jdata['DataID'] == 4:  #铁索连环
            if not isHaveState(templay, str(85)):
                cpstateinfo = copy.deepcopy(stateinfo)
                cpstateinfo['skillid'] = str(85)
                cpstateinfo['statusvalue'] = ';'.join([str(i) for i in jdata['Datas']])
                templay.stateinfo.append(cpstateinfo)
            else:
                for item in templay.stateinfo:
                    if item['skillid'] == str(85):
                        item['statusvalue'] = ';'.join([str(i) for i in jdata['Datas']] )
                        break
        elif jdata['DataID'] == 5:  #武将是否翻面
            templay.updateTurnOver(jdata['Datas'][jdata['data_count'] - 1])
        elif jdata['DataID'] in [8]:  # 增加技能效果(有点问题)
            if not isHaveState(templay, str(jdata['Datas'][0])):
                cpstateinfo = copy.deepcopy(stateinfo)
                cpstateinfo['skillid'] = str(jdata['Datas'][0])
                cpstateinfo['statusvalue'] = ';'.join([str(i) for i in jdata['Datas']])
                templay.stateinfo.append(cpstateinfo)
            else:
                for item in templay.stateinfo:
                    if item['skillid'] == str(jdata['Datas'][0]):
                        item['statusvalue'] = ';'.join([str(i) for i in jdata['Datas']] )
                        break
        elif jdata['DataID'] == 9:  #移除技能效
            if isHaveState(templay, str(jdata['Datas'][0])):
                for item in templay.stateinfo:
                    if item['skillid'] == str(jdata['Datas'][0]):
                        templay.stateinfo.remove(item)
                        break
        elif jdata['DataID'] == 13:  # 设置武将国家
            templay.country = str(jdata['Datas'][0])
        elif jdata['DataID'] == 14:  # 设置武将性别
            templay.gender = str(jdata['Datas'][0])
        elif jdata['DataID'] == 15:  # 为武将添加技能
            if str(jdata['Datas'][2]) not in templay.spellInfoList:
                templay.spellInfoList.append(str(jdata['Datas'][2]))
        elif jdata['DataID'] == 16:  # 为武将删除技能
            if str(jdata['Datas'][2]) in templay.spellInfoList:
                templay.spellInfoList.remove(str(jdata['Datas'][2]))
        elif jdata['DataID'] == 17:#设置武将技能 data[0]表示武将ID，为无效值时表示设置的是玩家的技能;data[1]:技能个数
            for i in range(jdata['Datas'][1]):
                if str(jdata['Datas'][i + 2]) not in templay.spellInfoList:
                    templay.spellInfoList.append(str(jdata['Datas'][i + 2]))
        elif jdata['DataID'] == 11 and jdata['data_count'] > 0 and jdata['Datas'][0] != 0:#增加化身牌
            if not isHaveState(templay, str(881)):
                cpstateinfo = copy.deepcopy(stateinfo)
                cpstateinfo['skillid'] = str(881)
                cpstateinfo['statusvalue'] = ';'.join([str(i) for i in jdata['Datas']])
                templay.stateinfo.append(cpstateinfo)
            else:
                for item in templay.stateinfo:
                    if item['skillid'] == str(881):
                        item['statusvalue'] = item['statusvalue'] + ';' + ';'.join([str(i) for i in jdata['Datas']])
                        break
        elif jdata['DataID'] == 24 and jdata['data_count'] > 0 and jdata['Datas'][0] != 0:# OPT_REMOVE_HUA_SHEN_CARD
            for item in templay.stateinfo:
                if item['skillid'] == str(881):
                    temp = item['statusvalue'].split(';')
                    for dd in jdata['Datas']:
                        if str(dd) in temp:
                            temp.remove(str(dd))
                    item['statusvalue'] = ';'.join([str(i) for i in temp])
                    break
    
    if len(template) == 0:
        return

    apid = int(template['SimulatorInfo']['Actioninfo'][0]['actionPID'])

    if apid != 21215:
        return 
    
    attype = int(template['SimulatorInfo']['Actioninfo'][0]['optTargetParam']['optType'])
    aspell = int(template['SimulatorInfo']['Actioninfo'][0]['optTargetParam']['spellId'])
    StateID = jdata['DataID']
    if apid == 21215 and  attype in [28,29,30,41] and StateID in [15,8,] and aspell in [3245,278,911,863,955,3078,3104,989,3166,3233,3220] :
        labelinfo = {'actionPID':str(jdata['id']),'seatId':str(jdata['SeatID']), 'stateinfo':{
            'dataID':str(jdata['DataID']),
            'IsSpell': '1' if jdata['IsSpell'] else '0',
            'data_count':str(jdata['data_count']),
            'datas': ';'.join([str(c) for c in jdata['Datas']]),
        } }
        save_simulatInfo_addaction(21252,  labelinfo, aspell)

### 待处理21218的状态处理
def deal_xieyi_21218(jdata):
    templay = get_player_by_seat(jdata['SeatID'])
    if templay == -1:
        return 
    if jdata['StateID'] == 1:
        if not isHaveState(templay, str(1)):
                cpstateinfo = copy.deepcopy(stateinfo)
                cpstateinfo['skillid'] = str(1)
                cpstateinfo['statusvalue'] = str(jdata['Value'])
                templay.stateinfo.append(cpstateinfo)
        else:
            for item in templay.stateinfo:
                if item['skillid'] == str(1):
                    item['statusvalue'] =  str(jdata['Value'])
                    break
    if jdata['StateID'] == 48:
        if not isHaveState(templay, str(7000)):
                cpstateinfo = copy.deepcopy(stateinfo)
                cpstateinfo['skillid'] = str(7000)
                cpstateinfo['statusvalue'] = str(jdata['Value'])
                templay.stateinfo.append(cpstateinfo)
        else:
            for item in templay.stateinfo:
                if item['skillid'] == str(7000):
                    item['statusvalue'] =  str(jdata['Value'])
                    break
    elif jdata['StateID'] == 54:## 手牌上限
        templay.maxhandcardnum = str(jdata['Value'])
    if len(template) == 0:
        return

    apid = int(template['SimulatorInfo']['Actioninfo'][0]['actionPID'])

    if apid != 21215:
        return 
    attype = int(template['SimulatorInfo']['Actioninfo'][0]['optTargetParam']['optType'])
    aspell = int(template['SimulatorInfo']['Actioninfo'][0]['optTargetParam']['spellId'])
    StateID = jdata['StateID']
    if apid == 21215 and  attype in [28,29,30,41] and StateID in [4,5,54,60,61,31,32,7,] and aspell in [219,3081,3078,844,764] :
        labelinfo = {'actionPID':str(jdata['id']),'seatId':str(jdata['SeatID']), 'stateinfo':{
            'stateID':str(jdata['StateID']),
            'value':str(jdata['Value']),
        } }
        save_simulatInfo_addaction(21218,  labelinfo, aspell)
    
def deal_special_spell(jdata):
    def addMoveCardInfo(jdata):
        if len(save_simulatfiles_list) == 0:
            return 
        # with open(save_simulatfiles_list[-1], 'r', encoding='utf-8-sig') as j:
        #     template = copy.deepcopy(json.load(j))
        if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] == '21215' and  template['SimulatorInfo'].get('Labelinfo') is None:
            labelinfo = {'actionPID':str(jdata['id']), "seatId": str(jdata['SrcSeatID']), "moveCard":{
                'fromZone':str(jdata['FromZone']), 'ToZone':str(jdata['ToZone']), 'typeMove':str(jdata['MoveType']), 'fromId':str(jdata['FromID']),
                'toId':str(jdata['ToID']),'fromPosition':str(jdata['FromPosition']),'toPosition':str(jdata['ToPosition']),'srcSeatID':str(jdata['SrcSeatID']),
                'spellId':str(jdata['SpellID']),'fromZoneParam':str(jdata['FromZoneParam']),'toZoneParam':str(jdata['ToZoneParam']),'cardCnt':str(jdata['CardCount']),
            'datas': ';'.join([str(c) for c in jdata['CardIDs']])}}
            save_simulatInfo_addaction(21209,  labelinfo, jdata['SpellID'])

    global is_special_spell
    # 眩惑 摸牌阶段，你可以改为令一名其他角色摸两张牌，然后其选择一项：1.对你指定的另一名角色使用一张【杀】；2.你获得其两张牌。
    if jdata['SpellID'] == 24:
        if jdata['MoveType'] == 1 and jdata['FromZone'] == 1 and jdata['ToZone'] == 5 and is_special_spell == 0:  # 选择了给牌
            is_special_spell = 24
            addMoveCardInfo(jdata)
        elif jdata['MoveType'] == 4 and jdata['FromZone'] == 5 and jdata['ToZone'] == 2 and is_special_spell == 24:
            is_special_spell = 0
            addMoveCardInfo(jdata)
    # 眩惑 摸牌阶段，你可以改为令一名其他角色摸两张牌，然后其选择一项：1.对你指定的另一名角色使用一张【杀】；2.你获得其两张牌。
    elif jdata['SpellID'] == 461 and is_special_spell == 461:
        if jdata['FromID'] != 255 and jdata['FromZone'] == 5 and jdata['ToZone'] == 5:  # 选择了给牌
            is_special_spell = 0
            addMoveCardInfo(jdata)
     # 享乐 其选择一项：1.弃置一张基牌；2.令此【杀】对你无效。
    elif jdata['SpellID'] == 127 and is_special_spell == 127:
        if jdata['FromID'] != 255 and jdata['FromZone'] == 5 and jdata['ToZone'] == 2:  # 选择了给牌
            is_special_spell = 0
            addMoveCardInfo(jdata)
     # 然后本回合结束时，你可以弃置一张手牌并令一名其他角色执行一个额外的回合。
    elif jdata['SpellID'] == 128 and is_special_spell == 128:
        if jdata['MoveType'] == 4 and jdata['FromZone'] == 5 and jdata['ToZone'] == 2:  # 选择了给牌
            is_special_spell = 0
            addMoveCardInfo(jdata)
    # 哲妇 当你于回合外使用或打出牌后，你可以令一名有手牌的其他角色选择弃置一张同名牌或受到1点伤害。
    elif jdata['SpellID'] == 3262 and is_special_spell == 3262:
        if jdata['FromID'] != 255 and jdata['FromZone'] == 5 and jdata['ToZone'] == 2:  # 弃置
            is_special_spell = 0
            addMoveCardInfo(jdata)
    # 潜袭 准备阶段，你可以摸一张牌并弃置一张牌，然后令距离为1的一名角色本回合不能使用或打出与你弃置牌颜色相同的手牌。
    elif jdata['SpellID'] == 474 and is_special_spell == 474:
        if jdata['FromID'] != 255 and jdata['FromZone'] == 5 and jdata['ToZone'] == 2:  # 弃置
            is_special_spell = 0
            addMoveCardInfo(jdata)
    #恩怨  当你获得一名其他角色至少两张牌后，你可以令其摸一张牌。当你受到1点伤害后，你可以令伤害来源选择一项：1.交给你一张手牌；2.失去1点体力。
    elif jdata['SpellID'] == 460:
        if jdata['FromID'] != 255 and jdata['FromZone'] == 5 and jdata['ToZone'] == 5:  # 选择了给牌
            is_special_spell = 0
            addMoveCardInfo(jdata)
    #明策  出牌阶段限一次，你可以交给一名其他角色一张【杀】或装备牌，然后其选择一项：1.视为对其攻击范围内你选择的另一名角色使用一张【杀】；2.摸一张牌。
    elif jdata['SpellID'] == 405 and len(jdata['CardIDs']) != 0:
        if jdata['FromID'] == 255 and jdata['FromZone'] == 1 and jdata['ToID'] == jdata['SrcSeatID']:#选择了摸牌
            addMoveCardInfo(jdata)
    #狂斧 出牌阶段限一次，你可以弃置一名角色装备区里的一张牌，视为使用一张无距离限制的【杀】。若以此法弃置的牌：不属于你且未造成伤害，你弃置两张手牌；属于你且造成了伤害，你摸两张牌。
    elif jdata['SpellID'] == 9008 and len(jdata['CardIDs']) != 0:
        if  jdata['FromZone'] == 6 and jdata['ToZone'] == 2:#选择了摸牌
            addMoveCardInfo(jdata)
    #弘援 每阶段限一次，当你一次获得至少两张牌后，你可以交给至多两名其他角色各一张牌。
    elif jdata['SpellID'] == 3204 and len(jdata['CardIDs']) != 0:
        if  jdata['FromZone'] == 5 and jdata['ToZone'] == 5:#选择了摸牌
            addMoveCardInfo(jdata)
    #陈情  每轮限一次，当一名角色进入濒死状态时，你可以令另一名其他角色摸四张牌，然后弃置四张牌，若弃置牌包含四种花色，其视为对处于濒死状态的角色使用一张【桃】。
    elif jdata['SpellID'] == 264 and is_special_spell == 264:
        if jdata['FromZone'] == 5 and jdata['ToZone'] == 2 and jdata['FromID'] == jdata['SrcSeatID']:  # 选择了摸牌
            is_special_spell = 0
            addMoveCardInfo(jdata)
    #破军 当你于出牌阶段使用【杀】指定目标后，你可以将其至多X张牌移出游戏直到回合结束（X为其体力值）
    elif jdata['SpellID'] == 414 and is_special_spell == 414:
        if jdata['FromZone'] == 5 and jdata['ToZone'] == 4 and jdata['FromID'] == jdata['ToID']:  # 选择了摸牌
            is_special_spell = 0
            addMoveCardInfo(jdata)
    #义绝 出牌阶段限一次，你可以弃置一张牌，然后令一名其他角色展示一张手牌。若此牌为：黑色，其本回合非锁定技失效且不能使用或打出手牌，你本回合对其使用的红桃【杀】伤害+1；红色，你获得之，然后你可以令其回复1点体力。
    elif jdata['SpellID'] == 701 and is_special_spell == 701 and len(jdata['CardIDs']) != 0:
        if  jdata['MoveType'] == 21 and jdata['FromZone'] == jdata['ToZone'] and jdata['ToZone'] == 5 and jdata['FromID'] == jdata['ToID']:#选择了摸牌
            is_special_spell = 0
            addMoveCardInfo(jdata)
    #狂骨 当你对距离1以内的一名角色造成1点伤害后，你可以回复1点体力或摸一张牌
    elif jdata['SpellID'] == 295 and len(jdata['CardIDs']) != 0 and is_special_spell == 0:
        if  jdata['MoveType'] == 1 and jdata['ToID'] == jdata['SrcSeatID'] and jdata['ToZone'] == 5:#选择了摸牌
            addMoveCardInfo(jdata)
            is_special_spell = -1
    # 据守 结束阶段，你可以翻面并摸四张牌，然后弃置一张手牌，若为装备牌，你改为使用之。
    elif jdata['SpellID'] == 370 and len(jdata['CardIDs']) != 0 and len(jdata['CardIDs']) == 1:
        if  jdata['MoveType'] == 4 and jdata['FromID'] == jdata['SrcSeatID'] and jdata['FromZone'] == 5:
            addMoveCardInfo(jdata)
    # 鞬出""当你使用【杀】指定目标后，你可以弃置其一张牌，若弃置牌为：装备牌，其不能抵消此【杀】；非装备牌，其获得此【杀】。
    elif jdata['SpellID'] == 364 and is_special_spell == 364 :
        if  jdata['MoveType'] == 4 and jdata['FromZone'] == 5:#选择了摸牌
            addMoveCardInfo(jdata)
            is_special_spell = 0
    #"好施" "摸牌阶段，你可以多摸两张牌，然后若你的手牌数大于5，你将一半的手牌（向下取整）交给手牌最少的一名其他角色。"
    elif jdata['SpellID'] == 120 and is_special_spell == 0:
        if  jdata['MoveType'] == 8 and jdata['FromID'] == jdata['SrcSeatID']:#选择了获得牌 获得弃的牌
            is_special_spell = -1
            addMoveCardInfo(jdata)
    # 志继" "觉醒技，准备阶段或结束阶段，若你没有手牌，你回复1点体力或摸两张牌，然后减少1点体力上限，获得【观星】。
    elif jdata['SpellID'] == 986 and is_special_spell == 0:
        if  jdata['MoveType'] == 1 and jdata['ToID'] == jdata['SrcSeatID'] and jdata['FromZone'] == 1:#选择了获得牌 获得弃的牌
            is_special_spell = -1
            addMoveCardInfo(jdata)
    # 志继" "觉醒技，准备阶段或结束阶段，若你没有手牌，你回复1点体力或摸两张牌，然后减少1点体力上限，获得【观星】。
    elif jdata['SpellID'] == 126 and is_special_spell == 0:
        if  jdata['MoveType'] == 1 and jdata['ToID'] == jdata['SrcSeatID'] and jdata['FromZone'] == 1:#选择了获得牌 获得弃的牌
            is_special_spell = -1
            addMoveCardInfo(jdata)
    # 严教 出牌阶段限一次，你可以令一名其他角色亮出牌堆顶4张牌并将之分成点数之和相等的两组，你与其各获得其中一组，若剩余牌数大于1，你本回合手牌上限-1。
    elif jdata['SpellID'] == 945:
        if  jdata['MoveType'] == 15 and jdata['ToID'] == jdata['SrcSeatID'] and jdata['FromZone'] == 3:#选择了获得牌 获得弃的牌
            addMoveCardInfo(jdata)
    # 追击 锁定技，你计算与体力值不大于你的角色的距离视为1。当你使用【杀】指定距离为1的角色为目标后，其弃置一张牌或重铸其装备区里的所有牌
    elif jdata['SpellID'] == 3123 and is_special_spell == 3123:
        if  jdata['MoveType'] == 4 and jdata['FromID'] == jdata['SrcSeatID'] and jdata['FromZone'] == 5 and jdata['ToZone'] == 2:#选择了获得牌 获得弃的牌
            addMoveCardInfo(jdata)
            is_special_spell = 0
    # 铁骑 当你使用【杀】指定目标后，你可以令其本回合非锁定技失效，然后你判定，除非其弃置一张与判定结果花色相同的牌，否则其不能抵消此【杀】。
    elif jdata['SpellID'] == 704 and is_special_spell == 704:
        if  jdata['MoveType'] == 4 and jdata['FromID'] == jdata['SrcSeatID'] and jdata['ToZone'] == 2:#选择了获得牌 获得弃的牌
            addMoveCardInfo(jdata)
            is_special_spell = 0
    elif len(jdata['CardIDs']) == 0 and jdata['SpellID'] in [3204, 9008, 405, 295, 120, 986, 24]:
        is_special_spell = 0
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] == 870 and jdata['MoveType'] == 4:
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] == 703 and len(jdata['CardIDs']) == jdata['CardCount']:  ## 处理【涯角】
        if (jdata['FromZone'] == 1 and jdata['ToZone'] == 8) or (jdata['FromZone'] == 8 and jdata['ToZone'] == 1):
            return
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] == 304 and len(jdata['CardIDs']) == jdata['CardCount'] and is_special_spell == 304:  ## 处理【攻心】
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] == 713 and jdata['MoveType'] == 21 and len(jdata['CardIDs']) == jdata['CardCount'] and is_special_spell == 713: # 选择拆牌
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] in [35, 869] and jdata['MoveType'] == 7 and len(jdata['CardIDs']) == jdata['CardCount']: #观星之后放回卡牌
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] in [728,967,480,484,814,]:
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] == 485 and jdata['FromZone'] == 5 and jdata['ToZone'] == 5 and jdata['CardIDs'] and is_special_spell == 485:
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] in [818] and jdata['MoveType'] == 15 and len(jdata['CardIDs']) == jdata['CardCount'] and jdata['ToID'] == jdata['SrcSeatID']: #罪论
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] == 414 and jdata['CardIDs'] and jdata['MoveType'] == 15:
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] == 424 and jdata['MoveType'] == 4:
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] == 371 and jdata['MoveType'] != 4:
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] == 382 and jdata['FromID'] != jdata["SrcSeatID"]:
        addMoveCardInfo(jdata)
    elif jdata['SpellID'] == 125 and jdata['MoveType'] == 4:
        addMoveCardInfo(jdata)

def deal_xieyi_21209(jdata):
    global table_spell_info
    global table_stack_info
    

    def add_stack_card(spell, cards):
        if spell in table_stack_info :
            if cards not in  table_stack_info[spell]:
                table_stack_info[spell].append(cards)
        else:
            table_stack_info[spell] = [cards]

    def remove_stack_card(spell, card):
        if spell in table_stack_info and card in table_stack_info[spell]:
            table_stack_info[spell].remove(card)

    def add_spell_card(spell, cards):
        table_spell_info[spell] = cards

    def remove_spell_card(spell, card):
        if spell in table_spell_info and card in table_spell_info[spell]:
            table_spell_info[spell].remove(card)

    def add_remove_zone_card(spell, player, card):
        if spell in player.removeinfo:
            if card not in player.removeinfo[spell]:
                player.removeinfo[spell].append(card)
        else:
            player.removeinfo[spell] = [card]

    def remove_remove_zone_card(spell, player, card):
        if spell in player.removeinfo:
            if card in player.removeinfo[spell]:
                player.removeinfo[spell].remove(card)
    
    def card_isin_spell(spell, card, template):
        for item in template['SimulatorInfo']['TableInfo']['SpellZoneinfo']:
            if int(item['spellid']) == spell and len(item['cards']) > 0 and int(card) in [int(ii) for ii in item['cards'].split(";")]:
               return 1
        return 0
    
    def addMoveCardInfo(templay, card, jdata):
        if card not in templay.handcards and jdata['SpellID'] != 0 and len(save_simulatfiles_list) > 0:
            # with open(save_simulatfiles_list[-1], 'r', encoding='utf-8-sig') as j:
            #     template = copy.deepcopy(json.load(j)) 
            if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] == '21215' \
                and ((template['SimulatorInfo'].get('Labelinfo') is None) or (int(template['SimulatorInfo']['Labelinfo'][0]['actionPID']) == 21220 and int(template['SimulatorInfo']['Labelinfo'][0]['spellOpt']['SpellId']) in [7009, 845, 818])):
                labelinfo = {'actionPID':str(jdata['id']), "seatId": str(jdata['SrcSeatID']), "moveCard":{
                    'fromZone':str(jdata['FromZone']), 'ToZone':str(jdata['ToZone']), 'typeMove':str(jdata['MoveType']), 'fromId':str(jdata['FromID']), 
                    'toId':str(jdata['ToID']),'fromPosition':str(jdata['FromPosition']),'toPosition':str(jdata['ToPosition']),'srcSeatID':str(jdata['SrcSeatID']),
                    'spellId':str(jdata['SpellID']),'fromZoneParam':str(jdata['FromZoneParam']),'toZoneParam':str(jdata['ToZoneParam']),'cardCnt':str(jdata['CardCount']),
                'datas': ';'.join([str(c) for c in jdata['CardIDs']])}}
                save_simulatInfo_addaction(21209,  labelinfo, jdata['SpellID'])

            if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] == '21265' and jdata['SpellID'] in [759]:
                labelinfo = {'actionPID':str(jdata['id']), "seatId": str(jdata['SrcSeatID']), "moveCard":{
                    'fromZone':str(jdata['FromZone']), 'ToZone':str(jdata['ToZone']), 'typeMove':str(jdata['MoveType']), 'fromId':str(jdata['FromID']), 
                    'toId':str(jdata['ToID']),'fromPosition':str(jdata['FromPosition']),'toPosition':str(jdata['ToPosition']),'srcSeatID':str(jdata['SrcSeatID']),
                    'spellId':str(jdata['SpellID']),'fromZoneParam':str(jdata['FromZoneParam']),'toZoneParam':str(jdata['ToZoneParam']),'cardCnt':str(jdata['CardCount']),
                'datas': ';'.join([str(c) for c in jdata['CardIDs']])}}
                save_simulatInfo_addaction(21209,  labelinfo, jdata['SpellID'])

    def moveHandInfo(templay, card, jdata):
        if card in templay.handcards and (jdata['SpellID'] != 0 or jdata['MoveType'] in[12, 8] )and len(save_simulatfiles_list) > 0:
            # with open(save_simulatfiles_list[-1], 'r', encoding='utf-8-sig') as j:
            #     template = copy.deepcopy(json.load(j)) 
            if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] == '21215' and \
             ((template['SimulatorInfo'].get('Labelinfo') is None)
             or ((template['SimulatorInfo']['Labelinfo'][0]['actionPID'] == '21220') and (template['SimulatorInfo']['Labelinfo'][0]['spellOpt']['SpellId'] in['747','304'] ))
              or ((template['SimulatorInfo']['Labelinfo'][0]['actionPID'] == '21212') and (template['SimulatorInfo']['Labelinfo'][0]['useSpell']['spellId'] in['269','3263'])) 
              or ((template['SimulatorInfo']['Labelinfo'][0]['actionPID'] == '21209') 
              and ((str(card) not in template['SimulatorInfo']['Labelinfo'][0]['moveCard']['datas']) 
              or (str(jdata['MoveType']) != template['SimulatorInfo']['Labelinfo'][0]['moveCard']['typeMove'])))):
                labelinfo = {'actionPID':str(jdata['id']), "seatId": str(jdata['SrcSeatID']), "moveCard":{
                    'fromZone':str(jdata['FromZone']), 'ToZone':str(jdata['ToZone']), 'typeMove':str(jdata['MoveType']), 'fromId':str(jdata['FromID']), 
                    'toId':str(jdata['ToID']),'fromPosition':str(jdata['FromPosition']),'toPosition':str(jdata['ToPosition']),'srcSeatID':str(jdata['SrcSeatID']),
                    'spellId':str(jdata['SpellID']),'fromZoneParam':str(jdata['FromZoneParam']),'toZoneParam':str(jdata['ToZoneParam']),'cardCnt':str(jdata['CardCount']),
                'datas': ';'.join([str(c) for c in jdata['CardIDs']])}}
                save_simulatInfo_addaction(21209,  labelinfo, jdata['SpellID'])

        if card in templay.handcards and len(save_simulatfiles_list) > 0:
            # with open(save_simulatfiles_list[-1], 'r', encoding='utf-8-sig') as j:
            #     template = copy.deepcopy(json.load(j)) 
            if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] == '21214' and template['SimulatorInfo']['Actioninfo'][0]['actionType'] == '2' and template['SimulatorInfo'].get('Labelinfo') is None:
                labelinfo = {'actionPID':str(jdata['id']), "seatId": str(jdata['SrcSeatID']), "moveCard":{
                    'fromZone':str(jdata['FromZone']), 'ToZone':str(jdata['ToZone']), 'typeMove':str(jdata['MoveType']), 'fromId':str(jdata['FromID']), 
                    'toId':str(jdata['ToID']),'fromPosition':str(jdata['FromPosition']),'toPosition':str(jdata['ToPosition']),'srcSeatID':str(jdata['SrcSeatID']),
                    'spellId':str(jdata['SpellID']),'fromZoneParam':str(jdata['FromZoneParam']),'toZoneParam':str(jdata['ToZoneParam']),'cardCnt':str(jdata['CardCount']),
                'datas': ';'.join([str(c) for c in jdata['CardIDs']])}}
                save_simulatInfo_addaction(21209,  labelinfo, jdata['SpellID'])

        if str(jdata['MoveType']) == '12' and template['SimulatorInfo'].get('Labelinfo') is None:
            labelinfo = {'actionPID':str(jdata['id']), "seatId": str(jdata['SrcSeatID']), "moveCard":{
                'fromZone':str(jdata['FromZone']), 'ToZone':str(jdata['ToZone']), 'typeMove':str(jdata['MoveType']), 'fromId':str(jdata['FromID']), 
                'toId':str(jdata['ToID']),'fromPosition':str(jdata['FromPosition']),'toPosition':str(jdata['ToPosition']),'srcSeatID':str(jdata['SrcSeatID']),
                'spellId':str(jdata['SpellID']),'fromZoneParam':str(jdata['FromZoneParam']),'toZoneParam':str(jdata['ToZoneParam']),'cardCnt':str(jdata['CardCount']),
            'datas': ';'.join([str(c) for c in jdata['CardIDs']])}}
            save_simulatInfo_addaction(21209,  labelinfo, jdata['SpellID'])
        

    def addMoveequipinfo(templay, card, jdata):
        if card not in templay.equipinfo and jdata['SpellID'] != 0 and len(save_simulatfiles_list) > 0:
            # with open(save_simulatfiles_list[-1], 'r', encoding='utf-8-sig') as j:
            #     template = copy.deepcopy(json.load(j)) 
            if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] == '21215' and template['SimulatorInfo'].get('Labelinfo') is None:
                labelinfo = {'actionPID':str(jdata['id']), "seatId": str(jdata['SrcSeatID']), "moveCard":{
                    'fromZone':str(jdata['FromZone']), 'ToZone':str(jdata['ToZone']), 'typeMove':str(jdata['MoveType']), 'fromId':str(jdata['FromID']), 
                    'toId':str(jdata['ToID']),'fromPosition':str(jdata['FromPosition']),'toPosition':str(jdata['ToPosition']),'srcSeatID':str(jdata['SrcSeatID']),
                    'spellId':str(jdata['SpellID']),'fromZoneParam':str(jdata['FromZoneParam']),'toZoneParam':str(jdata['ToZoneParam']),'cardCnt':str(jdata['CardCount']),
                'datas': ';'.join([str(c) for c in jdata['CardIDs']])}}
                save_simulatInfo_addaction(21209,  labelinfo, jdata['SpellID'])

    def moveequipinfo(templay, card, jdata):
        if card in templay.equipinfo and jdata['SpellID'] != 0 and len(save_simulatfiles_list) > 0:
            # with open(save_simulatfiles_list[-1], 'r', encoding='utf-8-sig') as j:
            #     template = copy.deepcopy(json.load(j)) 
            if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] == '21215' and template['SimulatorInfo'].get('Labelinfo') is None:
                labelinfo = {'actionPID':str(jdata['id']), "seatId": str(jdata['SrcSeatID']), "moveCard":{
                    'fromZone':str(jdata['FromZone']), 'ToZone':str(jdata['ToZone']), 'typeMove':str(jdata['MoveType']), 'fromId':str(jdata['FromID']), 
                    'toId':str(jdata['ToID']),'fromPosition':str(jdata['FromPosition']),'toPosition':str(jdata['ToPosition']),'srcSeatID':str(jdata['SrcSeatID']),
                    'spellId':str(jdata['SpellID']),'fromZoneParam':str(jdata['FromZoneParam']),'toZoneParam':str(jdata['ToZoneParam']),'cardCnt':str(jdata['CardCount']),
                'datas': ';'.join([str(c) for c in jdata['CardIDs']])}}
                save_simulatInfo_addaction(21209,  labelinfo, jdata['SpellID'])

    def addMoveJudgeInfo(templay, card, jdata):
        if card not in templay.judgeinfo and jdata['SpellID'] != 0 and len(save_simulatfiles_list) > 0:
            # with open(save_simulatfiles_list[-1], 'r', encoding='utf-8-sig') as j:
            #     template = copy.deepcopy(json.load(j)) 
            if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] == '21215' and template['SimulatorInfo'].get('Labelinfo') is None:
                labelinfo = {'actionPID':str(jdata['id']), "seatId": str(jdata['SrcSeatID']), "moveCard":{
                    'fromZone':str(jdata['FromZone']), 'ToZone':str(jdata['ToZone']), 'typeMove':str(jdata['MoveType']), 'fromId':str(jdata['FromID']), 
                    'toId':str(jdata['ToID']),'fromPosition':str(jdata['FromPosition']),'toPosition':str(jdata['ToPosition']),'srcSeatID':str(jdata['SrcSeatID']),
                    'spellId':str(jdata['SpellID']),'fromZoneParam':str(jdata['FromZoneParam']),'toZoneParam':str(jdata['ToZoneParam']),'cardCnt':str(jdata['CardCount']),
                'datas': ';'.join([str(c) for c in jdata['CardIDs']])}}
                save_simulatInfo_addaction(21209,  labelinfo, jdata['SpellID'])

    def moveJudgeInfo(templay, card, jdata):
        if card in templay.judgeinfo and jdata['SpellID'] != 0 and len(save_simulatfiles_list) > 0:
            # with open(save_simulatfiles_list[-1], 'r', encoding='utf-8-sig') as j:
            #     template = copy.deepcopy(json.load(j)) 
            actionPID = template['SimulatorInfo']['Actioninfo'][0]['actionPID']
            if (actionPID == '21215' and template['SimulatorInfo'].get('Labelinfo') is None ) or (actionPID == '21265' and jdata['SpellID'] == 479):
                labelinfo = {'actionPID':str(jdata['id']), "seatId": str(jdata['SrcSeatID']), "moveCard":{
                    'fromZone':str(jdata['FromZone']), 'ToZone':str(jdata['ToZone']), 'typeMove':str(jdata['MoveType']), 'fromId':str(jdata['FromID']), 
                    'toId':str(jdata['ToID']),'fromPosition':str(jdata['FromPosition']),'toPosition':str(jdata['ToPosition']),'srcSeatID':str(jdata['SrcSeatID']),
                    'spellId':str(jdata['SpellID']),'fromZoneParam':str(jdata['FromZoneParam']),'toZoneParam':str(jdata['ToZoneParam']),'cardCnt':str(jdata['CardCount']),
                'datas': ';'.join([str(c) for c in jdata['CardIDs']])}}
                save_simulatInfo_addaction(21209,  labelinfo, jdata['SpellID'])

    def moveSpellInfo(card, jdata):
        if len(save_simulatfiles_list) == 0:
            return 
        # with open(save_simulatfiles_list[-1], 'r', encoding='utf-8-sig') as j:
        #     template = copy.deepcopy(json.lofad(j)) 
        if card_isin_spell(int(jdata['SpellID']), card, template) == 0:
            return 
        if template['SimulatorInfo']['Actioninfo'][0]['actionPID'] == '21215' and ((template['SimulatorInfo'].get('Labelinfo') is None) or (template['SimulatorInfo']['Labelinfo'][0]['actionPID'] != '21209'))  :
            labelinfo = {'actionPID':str(jdata['id']), "seatId": str(jdata['SrcSeatID']), "moveCard":{
                'fromZone':str(jdata['FromZone']), 'ToZone':str(jdata['ToZone']), 'typeMove':str(jdata['MoveType']), 'fromId':str(jdata['FromID']), 
                'toId':str(jdata['ToID']),'fromPosition':str(jdata['FromPosition']),'toPosition':str(jdata['ToPosition']),'srcSeatID':str(jdata['SrcSeatID']),
                'spellId':str(jdata['SpellID']),'fromZoneParam':str(jdata['FromZoneParam']),'toZoneParam':str(jdata['ToZoneParam']),'cardCnt':str(jdata['CardCount']),
            'datas': ';'.join([str(c) for c in jdata['CardIDs']])}}
            save_simulatInfo_addaction(21209,  labelinfo, jdata['SpellID'])
    
    if jdata['CardCount'] == 161 or jdata['SrcSeatID'] == 255 or jdata['MoveType'] == 0:
        return
    
    if jdata['MoveType'] == 12:
        templay = get_player_by_seat(jdata['ToID'])
        if templay == -1:
            return 
        templay.roundplaycard += 0.25
    
    if jdata['MoveType'] == 1:##发牌
        if jdata['FromZone'] == eZoneType.ZONE_CARDPILE.value and jdata['ToZone'] == eZoneType.ZONE_HAND.value and jdata['ToID'] == jdata['SrcSeatID'] and (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['ToID'])
            if templay == -1:
                return 
            for card in jdata['CardIDs']:
                addMoveCardInfo(templay, card, jdata)
                templay.add_handcard(card)
    elif jdata['MoveType'] == 18 and jdata['FromZone'] == eZoneType.ZONE_CARDPILE.value and jdata['ToZone'] == eZoneType.ZONE_HAND.value and jdata['ToID'] == jdata['SrcSeatID'] and (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['ToID'])
            if templay == -1:
                return 
            for card in jdata['CardIDs']:
                addMoveCardInfo(templay, card, jdata)
                templay.add_handcard(card)
    elif  jdata['FromZone'] == eZoneType.ZONE_HAND.value and jdata['ToZone'] == eZoneType.ZONE_STACK.value:
        if (jdata['DataCount']) > 0:

            templay = get_player_by_seat(jdata['FromID'])
            if templay == -1:
                return 
            for card in jdata['CardIDs']:
                add_stack_card(jdata['SpellID'], card)
                moveHandInfo(templay, card, jdata)
                templay.remove_handcard(card)
    elif  jdata['FromZone'] == eZoneType.ZONE_STACK.value and jdata['ToZone'] == eZoneType.ZONE_DISACARPILE.value:
        if (jdata['DataCount']) > 0:
            for card in jdata['CardIDs']:
                remove_stack_card(jdata['SpellID'], card)
     # 36 从堆叠区域到装备区
    elif jdata['FromZone'] == eZoneType.ZONE_VIRTUAL.value and jdata['ToZone'] == eZoneType.ZONE_EQUIP.value:
        if (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['ToID'])
            if templay == -1:
                return 
            for card in jdata['CardIDs']:
                addMoveequipinfo(templay, card, jdata)
                templay.add_equiscard(card)       
    # 36 从堆叠区域到装备区
    elif jdata['FromZone'] == eZoneType.ZONE_STACK.value and jdata['ToZone'] == eZoneType.ZONE_EQUIP.value:
        if (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['ToID'])
            if templay == -1:
                return 
            for card in jdata['CardIDs']:
                remove_stack_card(jdata['SpellID'], card)
                templay.add_equiscard(card)
    # 55 从手牌区域到手牌 (顺手牵羊)
    elif jdata['FromZone'] == eZoneType.ZONE_HAND.value and jdata['ToZone'] == eZoneType.ZONE_HAND.value:
        # 统计数量
        if (jdata['DataCount']) > 0:
            toTemplay = get_player_by_seat(jdata['ToID'])
            if toTemplay == -1:
                return 
            fromTemplay = get_player_by_seat(jdata['FromID'])
            if fromTemplay == -1:
                return 
            for card in jdata['CardIDs']:
                moveHandInfo(fromTemplay, card, jdata)
                fromTemplay.remove_handcard(card)
                toTemplay.add_handcard(card)
                
        if (jdata['SpellID'] == 304 or jdata['MoveType'] == 21 )and len(jdata['CardIDs']) == jdata['CardCount']: #攻心
            add_spell_card(jdata['SpellID'], jdata['CardIDs'])   
    # 35 从堆叠区域到手牌区域 判定牌生效后，你就可以使用天妒技能获得那张使判定牌生效的牌。例如乐不思蜀
    elif jdata['FromZone'] == eZoneType.ZONE_STACK.value and jdata['ToZone'] == eZoneType.ZONE_HAND.value:
        if (jdata['DataCount']) > 0:
            toTemplay = get_player_by_seat(jdata['ToID'])
            if toTemplay == -1:
                return
            for card in jdata['CardIDs']:
                remove_stack_card(jdata['SpellID'], card)
                addMoveCardInfo(toTemplay, card, jdata)
                toTemplay.add_handcard(card)
                if jdata['SpellID'] == 818:
                    remove_spell_card(jdata['SpellID'], card)
    # 52 从手牌区到弃牌区
    elif jdata['FromZone'] == eZoneType.ZONE_HAND.value and jdata['ToZone'] == eZoneType.ZONE_DISACARPILE.value:
        temp_give = []
        if (jdata['DataCount']) > 0:
            fromTemplay = get_player_by_seat(jdata['FromID'])
            if fromTemplay == -1:
                return
            
            for card in jdata['CardIDs']:
                moveHandInfo(fromTemplay, card, jdata)
                temp_give.append(card)
                fromTemplay.remove_handcard(card)
        if icon_give_label and 55 in player_hero_list and table_players[jdata['FromID']].role_id != 55:
            add_spell_card(55, temp_give)
    # 37 从堆叠区域到判定
    elif jdata['FromZone'] == eZoneType.ZONE_STACK.value and jdata['ToZone'] == eZoneType.ZONE_JUDGE.value:
        if (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['ToID'])
            if templay == -1:
                return
            for card in jdata['CardIDs']:
                remove_stack_card(jdata['SpellID'], card)
                templay.add_judgecard(card)
    # 18 从摸牌区域到技能使用的牌的区域 属于具体spell 五谷丰登
    elif  jdata['MoveType'] == 6 and jdata['FromZone'] == eZoneType.ZONE_CARDPILE.value and jdata['ToZone'] == eZoneType.ZONE_SPELL.value :
        # 涯角的技能第一次更新response_data,完整动作需要在第二次21209中才会生成
        if len(jdata['CardIDs']) == jdata['CardCount']:
            add_spell_card(jdata['SpellID'], jdata['CardIDs'])
    elif jdata['MoveType'] == 21 and jdata['FromZone'] == eZoneType.ZONE_CARDPILE.value and jdata['ToZone'] == eZoneType.ZONE_CARDPILE.value:
        if len(jdata['CardIDs']) == jdata['CardCount']:
            add_spell_card(jdata['SpellID'], jdata['CardIDs'])
    elif jdata['FromZone'] == eZoneType.ZONE_SPELL.value and jdata['ToZone'] == eZoneType.ZONE_CARDPILE.value:
        # 涯角的技能第一次更新response_data,完整动作需要在第二次21209中才会生成
        if len(jdata['CardIDs']) == jdata['CardCount'] and jdata['DataCount'] > 0:
            for card in jdata['CardIDs']:
                moveSpellInfo(card, jdata)
                remove_spell_card(jdata['SpellID'], card)
    elif jdata['FromZone'] == eZoneType.ZONE_CARDPILE.value and jdata['ToZone'] == eZoneType.ZONE_STACK.value:
        # 涯角的技能第一次更新response_data,完整动作需要在第二次21209中才会生成
        if len(jdata['CardIDs']) == jdata['CardCount'] and jdata['DataCount'] > 0:
            for card in jdata['CardIDs']:
                moveSpellInfo(card, jdata)
                add_stack_card(jdata['SpellID'], card)
                remove_spell_card(jdata['SpellID'], card)
    # 85 从技能使用的牌的区域，属于具体spell 到手牌区
    elif jdata['FromZone'] == eZoneType.ZONE_CARDPILE.value and jdata['ToZone'] == eZoneType.ZONE_DISACARPILE.value:
        # 涯角的技能第一次更新response_data,完整动作需要在第二次21209中才会生成
        if jdata['SpellID'] in [6] and len(jdata['CardIDs']) == jdata['CardCount'] and jdata['DataCount'] > 0:
            for card in jdata['CardIDs']:
                remove_spell_card(jdata['SpellID'], card)
    # 85 从技能使用的牌的区域，属于具体spell 到手牌区
    elif jdata['FromZone'] == eZoneType.ZONE_DISACARPILE.value and jdata['ToZone'] == eZoneType.ZONE_HAND.value:
        # 涯角的技能第一次更新response_data,完整动作需要在第二次21209中才会生成
        if len(jdata['CardIDs']) == jdata['CardCount'] and jdata['DataCount'] > 0:
            templay = get_player_by_seat(jdata['ToID'])
            if templay == -1 or templay.characterID == 0:
                return
            for card in jdata['CardIDs']:
                templay.add_handcard(card)
                addMoveCardInfo(templay, card, jdata)
    # 85 从技能使用的牌的区域，属于具体spell 到手牌区
    elif jdata['FromZone'] == eZoneType.ZONE_SPELL.value and jdata['ToZone'] == eZoneType.ZONE_HAND.value:
        # 处理五谷丰登的选牌
        if (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['ToID'])
            if templay == -1 or templay.characterID == 0:
                return
            for card in jdata['CardIDs']:
                moveSpellInfo(card, jdata)
                templay.add_handcard(card)
                remove_spell_card(jdata['SpellID'], card)
    # 72 判定区到弃牌
    elif jdata['FromZone'] == eZoneType.ZONE_JUDGE.value and jdata['ToZone'] == eZoneType.ZONE_DISACARPILE.value:
        if (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['FromID'])
            if templay == -1 or templay.characterID == 0:
                return
            for card in jdata['CardIDs']:
                moveJudgeInfo(templay, card, jdata)
                templay.remove_judgecard(card)  
    elif jdata['FromZone'] == eZoneType.ZONE_JUDGE.value and jdata['ToZone'] == eZoneType.ZONE_STACK.value:
        if (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['FromID'])
            if templay == -1 or templay.characterID == 0:
                return
            for card in jdata['CardIDs']:
                add_stack_card(jdata['SpellID'], card)
                moveJudgeInfo(templay, card, jdata)
                templay.remove_judgecard(card) 
    elif jdata['FromZone'] == eZoneType.ZONE_JUDGE.value and jdata['ToZone'] == eZoneType.ZONE_HAND.value:
        if (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['FromID'])
            if templay == -1 or templay.characterID == 0:
                return
            
            toplay = get_player_by_seat(jdata['ToID'])
            if toplay == -1 or toplay.characterID == 0:
                return
            for card in jdata['CardIDs']:
                toplay.add_handcard(card)
                moveJudgeInfo(templay, card, jdata)
                templay.remove_judgecard(card) 
    # 62 装区到弃牌区
    elif jdata['FromZone'] == eZoneType.ZONE_EQUIP.value and jdata['ToZone'] == eZoneType.ZONE_DISACARPILE.value:
        if (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['FromID'])
            if templay == -1 or templay.characterID == 0:
                return
            for card in jdata['CardIDs']:
                moveequipinfo(templay, card, jdata)
                templay.remove_equiscard(card) 
    # 65 装区到手牌区
    elif jdata['FromZone'] == eZoneType.ZONE_EQUIP.value and jdata['ToZone'] == eZoneType.ZONE_HAND.value:
         if (jdata['DataCount']) > 0:
            for card in jdata['CardIDs']:
                templay = get_player_by_seat(jdata['FromID'])
                if templay == -1:
                    return
                moveequipinfo(templay, card, jdata)
                templay.remove_equiscard(card) 
                toplay = get_player_by_seat(jdata['ToID'])
                if toplay == -1:
                    return
                toplay.add_handcard(card)
           # 61 从区 到摸牌堆
    elif jdata['FromZone'] == eZoneType.ZONE_EQUIP.value and jdata['ToZone'] == eZoneType.ZONE_CARDPILE.value:
        if (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['FromID'])
            if templay == -1:
                return
            for card in jdata['CardIDs']:
                moveequipinfo(templay, card, jdata)
                templay.remove_equiscard(card) 
     # 51 从手 到摸牌堆
    elif jdata['FromZone'] == eZoneType.ZONE_HAND.value and jdata['ToZone'] == eZoneType.ZONE_CARDPILE.value:
        if (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['FromID'])
            if templay == -1:
                return
            for card in jdata['CardIDs']:
                moveHandInfo(templay, card, jdata)
                templay.remove_handcard(card)
    elif jdata['FromZone'] == eZoneType.ZONE_HAND.value and jdata['ToZone'] == eZoneType.ZONE_SPELL.value:
        if (jdata['DataCount']) > 0:
            templay = get_player_by_seat(jdata['FromID'])
            if templay == -1:
                return
            add_spell_card(jdata['SpellID'], jdata['CardIDs'])
            for card in jdata['CardIDs']:
                moveHandInfo(templay, card, jdata)
                templay.remove_handcard(card)
     # 25 从弃牌堆到手牌堆
    elif jdata['FromZone'] == eZoneType.ZONE_REMOVED.value and jdata['ToZone'] == eZoneType.ZONE_HAND.value:
        if (jdata['DataCount']) > 0:
            toplay = get_player_by_seat(jdata['ToID'])
            if toplay == -1:
                return
            fromplay = get_player_by_seat(jdata['FromID'])
            for card in jdata['CardIDs']:
                remove_remove_zone_card(jdata['SpellID'], fromplay, card)
                addMoveCardInfo(toplay, card, jdata)
                toplay.add_handcard(card)
    #44 从场外到场外
    elif jdata['FromZone'] == eZoneType.ZONE_REMOVED.value and jdata['ToZone'] == eZoneType.ZONE_REMOVED.value:
        if (jdata['DataCount']) > 0:
            toplay = get_player_by_seat(jdata['ToID'])
            if toplay == -1:
                return
            fromplay = get_player_by_seat(jdata['FromID'])
            if fromplay == -1:
                return
            for card in jdata['CardIDs']:
                remove_remove_zone_card(jdata['SpellID'], fromplay, card)
                add_remove_zone_card(jdata['SpellID'], toplay, card)
     # 54 从手牌到场外
    elif jdata['FromZone'] == eZoneType.ZONE_HAND.value and jdata['ToZone'] == eZoneType.ZONE_REMOVED.value:
        if (jdata['DataCount']) > 0:
            toplay = get_player_by_seat(jdata['ToID'])
            if toplay == -1:
                return
            fromplay = get_player_by_seat(jdata['FromID'])
            if fromplay == -1:
                return
            for card in jdata['CardIDs']:
                moveHandInfo(fromplay, card, jdata)
                add_remove_zone_card(jdata['SpellID'], toplay, card)
                fromplay.remove_handcard(card)
             # 54 从手牌到场外
    elif jdata['FromZone'] == eZoneType.ZONE_EQUIP.value and jdata['ToZone'] == eZoneType.ZONE_REMOVED.value:
        if (jdata['DataCount']) > 0:
            toplay = get_player_by_seat(jdata['ToID'])
            if toplay == -1:
                return
            fromplay = get_player_by_seat(jdata['FromID'])
            if fromplay == -1:
                return
            for card in jdata['CardIDs']:
                moveequipinfo(fromplay, card, jdata)
                add_remove_zone_card(jdata['SpellID'], toplay, card)
                fromplay.remove_equiscard(card)
    # 43 从场外到堆叠
    elif jdata['FromZone'] == eZoneType.ZONE_REMOVED.value and jdata['ToZone'] == eZoneType.ZONE_STACK.value:
        if (jdata['DataCount']) > 0 and (jdata['MoveType']) == 2 and jdata['SpellID'] != 0:
            fromplay = get_player_by_seat(jdata['FromID'])
            if fromplay == -1:
                return
            for card in jdata['CardIDs']:
                spell = jdata['SpellID']
                if jdata['SpellID']  == 139:
                    spell = 123
                elif jdata['SpellID']  == 3116:
                    spell = 3114
                add_stack_card(jdata['SpellID'], card)
                remove_remove_zone_card(spell, fromplay, card)
    # 43 从场外到堆叠
    elif jdata['FromZone'] == eZoneType.ZONE_STACK.value and jdata['ToZone'] == eZoneType.ZONE_REMOVED.value:
        if (jdata['DataCount']) > 0 and (jdata['MoveType']) in [8,15] and jdata['SpellID'] != 0:
            toplay = get_player_by_seat(jdata['ToID'])
            if toplay == -1:
                return
            for card in jdata['CardIDs']:
                remove_stack_card(jdata['SpellID'], card)
                add_remove_zone_card(jdata['SpellID'], toplay, card)
            if jdata['SpellID'] in [248] :
                labelinfo = {'actionPID':21219, 'seatId':str(jdata['SrcSeatID']),"roleOpt":{'seatId':str(jdata['SrcSeatID']),'optType':2, }}
                save_simulatInfo_addaction(21219,  labelinfo, '2')
    # 63 从装备区到堆叠区
    elif jdata['FromZone'] == eZoneType.ZONE_EQUIP.value and jdata['ToZone'] == eZoneType.ZONE_STACK.value:
        if (jdata['DataCount']) > 0:
            fromplay = get_player_by_seat(jdata['FromID'])
            if fromplay == -1:
                return
            for card in jdata['CardIDs']:
                add_stack_card(jdata['SpellID'], card)
                moveequipinfo(fromplay, card, jdata)
                fromplay.remove_equiscard(card)
     # 510 从手牌堆到临时区,如交换时使用
    elif jdata['FromZone'] == eZoneType.ZONE_HAND.value and jdata['ToZone'] == eZoneType.ZONE_TEMP.value:
        if (jdata['DataCount']) > 0:
            fromplay = get_player_by_seat(jdata['FromID'])
            if fromplay == -1:
                return
            for card in jdata['CardIDs']:
                moveHandInfo(fromplay, card, jdata)
                fromplay.remove_handcard(card)
    elif jdata['FromZone'] == eZoneType.ZONE_TEMP.value and jdata['ToZone'] == eZoneType.ZONE_HAND.value:
        if (jdata['DataCount']) > 0:
            fromplay = get_player_by_seat(jdata['ToID'])
            if fromplay == -1:
                return
            for card in jdata['CardIDs']:
                addMoveCardInfo(fromplay, card, jdata)
                fromplay.add_handcard(card)
    # 77 从判定堆到判定堆
    elif jdata['FromZone'] == eZoneType.ZONE_JUDGE.value and jdata['ToZone'] == eZoneType.ZONE_JUDGE.value:
        # print("77 从判定堆到判定堆  例如闪电",jsdata['CardIDs'])
        if (jdata['DataCount']) > 0:
            toplay = get_player_by_seat(jdata['ToID'])
            if toplay == -1:
                return
            fromplay = get_player_by_seat(jdata['FromID'])
            if fromplay == -1:
                return
            for card in jdata['CardIDs']:
                moveJudgeInfo(fromplay, card, jdata)
                toplay.add_judgecard(card)
                fromplay.remove_judgecard(card)
     # 66 从装备区域堆到装备区
    elif jdata['FromZone'] == eZoneType.ZONE_EQUIP.value and jdata['ToZone'] == eZoneType.ZONE_EQUIP.value:
        if (jdata['DataCount']) > 0:
            toplay = get_player_by_seat(jdata['ToID'])
            if toplay == -1:
                return
            fromplay = get_player_by_seat(jdata['FromID'])
            if fromplay == -1:
                return
            for card in jdata['CardIDs']:
                moveequipinfo(fromplay, card, jdata)
                toplay.add_equiscard(card)
                fromplay.remove_equiscard(card)

#sudo nohup python -u sgs_json2SimulatorInfoFromSql.py > sgs_json2SimulatorInfoFromSql_21.log 2>&1 &
delete_files_in_folder(save_json_path)

# parser = cysimdjson.JSONParser()
for tidx in find_idx:#,
    redis_key_index = tidx
    file_index = 0
    csvfiles, csvflieSeatDict = getDatasFromMysql(DataType.WinSeat, tidx, 2)
    for i in tqdm(range(0, len(csvfiles))):
        if i % maxline == 0:
            file_index += 1
            save_json_path = f'{find_data_path}/{redis_key_index}/{file_index}/'
            pathIsExists(save_json_path)
        timescnt = 0
        file_name_path = csvfiles[i]
        cur_file_name = file_name_path.split('/')[-1].split('.')[0]
        gameid = cur_file_name.split("_")[-2]
        timestamp = cur_file_name.split("_")[-1]
        # print(file_name_path)
        if not os.path.exists(file_name_path):
            print(file_name_path)
            # print("!!!")
            continue
        with open(file_name_path, 'r', encoding='utf-8-sig') as f:
            json_data = json.load(f)
        character_dic = {}
        for jdata in json_data:
            if 'id' not in jdata:
                continue
            if jdata["id"] == 21208:  # 桌面信息
                deal_xieyi_21208(jdata)
            elif jdata["id"] == 21223:  # 桌面信息
                deal_xieyi_21223(jdata)
            elif jdata["id"] == 21227 and jdata["Count"] == len(table_players):  # 玩家武将设置
                # 如果明牌的座位号不在要处理的武将情况 
                deal_xieyi_21227(jdata)
            elif jdata["id"] == 21252:
                deal_xieyi_21252(jdata)
            elif jdata["id"] == 21216:
                deal_xieyi_21216(jdata)
            elif jdata["id"] == 21209:
                if jdata["SpellID"] in [461,460,3262,405,9008,3204,264,414,474,701,295,370,364,382,120,986,945,3123,704,24,870,127,128,126,703,304,713,35,869,
                                        818,728,480,484,485,814,414,424,371,382,92,125,967,766,603,3315,493,480,248,126,3202,709,495,463,] :#特殊处理
                    deal_special_spell(jdata)
                deal_xieyi_21209(jdata)
            elif jdata["id"] == 21213:
                deal_xieyi_21213(jdata)
            elif jdata["id"] == 21214:  # 处理巡数中的各个阶段
                deal_xieyi_21214(jdata)
            elif jdata["id"] == 21265:  # 技能触发（新的技能触发协议）
                deal_xieyi_21265(jdata)
            elif jdata["id"] == 21217:  # 询问role是否触发技能
                deal_xieyi_21217(jdata)
            elif jdata["id"] == 21215:  # 通知角色对目标操作
                deal_xieyi_21215(jdata)
            elif jdata["id"] == 21210:  # 使用牌协议
                deal_xieyi_21210(jdata)
            elif jdata["id"] == 21212:  # 使用技能
                deal_xieyi_21212(jdata)
            elif jdata["id"] == 21219:  # 取消选择
                deal_xieyi_21219(jdata)
            elif jdata["id"] == 21220:  # 技能响应
                deal_xieyi_21220(jdata)
            elif jdata["id"] == 21218:  # 更新角色信息
                deal_xieyi_21218(jdata)
            elif jdata["id"] == 21241:  # 更新角色信息
                deal_xieyi_21241(jdata)
            elif jdata['id'] == 21373:
                deal_xieyi_21373(jdata)
            # elif jdata["id"] == 21228:  # 游戏结算
        #     #     delete_files_in_folder(save_json_temp_path)
        # break