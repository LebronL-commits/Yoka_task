import pandas as pd
import json
import numpy as np
import sys, copy, redis, os

############################根据ip配置基础信息########################
from netifaces import interfaces, ifaddresses, AF_INET
base_path_config = {
    '10.225.136.101':{
        'wangweiqing':'/data-p4/sgs_mlai_dev/nbs/',
        'louxiaojun':'/home/louxiaojun/file/nbs/'
    },
    '10.225.21.248':{
        'wwq':'/devdata5/sgs_mlai_dev/nbs/',
        'lxj':'/home/lxj/sgs_program/nbs/',
        'hujiankang':'/home/hujiankang/sgs_mlai_dev/nbs/',
    },
    '10.225.21.203':{
        'wwq':'/home/wwq/sgs_mlai_dev/nbs/',
        'lxj':'/home/lxj/sgs_program/nbs/'
    }
}

find_data_path_config = {
    '10.225.136.101':{
        'wangweiqing':'/data-p4/newsimlator/',
        'louxiaojun':'/home/louxiaojun/zaiqi_data/simulator'
    },
    '10.225.21.248':{
        'wwq':'/devdata5/newsimlator/',
        'lxj':'/home/lxj/zaiqi_data/simulator',
        'hujiankang':'/devdata5/newsimlator/',
    },
    '10.225.21.203':{
        'wwq':'/devdata2/smilator/',
        'lxj':'/home/lxj/zaiqi_data/simulator'
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
from public_file.global_define_online import base_card_space, target_action_space, cardId_2_cardSpace, \
    sha_type_space, target_seat_list

###############################################
character = pd.read_csv(base_path + "base_data_file/character.csv")
playcard = pd.read_csv(base_path +  "base_data_file/playcard.csv")

test_list = []

is_savetoredis = True
redis_server = 248
find_gameid = '00'
find_timestamp = '00'
read_redis_key = 'kf_248_0110_01'
find_index = 0
redis_conn = redis.Redis(host='10.225.21.248', port=6379, db=0, password='foobaredaabb')
pushredis_conn = redis.Redis(host='10.225.136.101', port=6379, db=0, password='foobaredaabb')


def pushDataToRedis(xieyi, jsondata, inputdata):
    if not is_savetoredis:
        return
    savekey = f'kf_{read_redis_key}_{find_gameid}_{find_timestamp}_{find_index}_{xieyi}'
    jsondata['inputdata'] = ','.join([str(ii) for ii in inputdata])
    pushredis_conn.rpush(savekey, json.dumps(jsondata))


def pushDataToRedisWithStep(xieyi, jsondata, inputdata, step):
    if not is_savetoredis:
        return
    savekey = f'kf_{read_redis_key}_{find_gameid}_{find_timestamp}_{find_index}_{xieyi}_{step}'
    jsondata['inputdata'] = ','.join([str(ii) for ii in inputdata])
    pushredis_conn.rpush(savekey, json.dumps(jsondata))


def pushDataToRedisWithSpell(xieyi, jsondata, inputdata, spell):
    if not is_savetoredis:
        return
    savekey = f'kf_{read_redis_key}_{find_gameid}_{find_timestamp}_{find_index}_{xieyi}_{spell}'
    jsondata['inputdata'] = ','.join([str(ii) for ii in inputdata])
    pushredis_conn.rpush(savekey, json.dumps(jsondata))


def test_is_lenerror(input, lens):
    if len(input) != lens:
        print(test_list[1])


def getColorAndNumber(card):
    if not card:
        return -1, -1, '', -1, -1
    item = playcard.loc[playcard['id'] == card]
    if len(item) < 1:
        return -1, -1, '', -1, -1

    color, number, name, type, subtype = getattr(item, 'color').values, getattr(item, 'number').values, getattr(item,
                                                                                                                'name').values, getattr(
        item, 'type').values, getattr(item, 'subType').values
    return color[0], number[0], name[0], type[0], subtype[0]


def getGenerById(id):
    item = character.loc[character['id'] == int(id)]
    if len(item) < 1:
        return 0

    gender = getattr(item, 'gender').values
    return gender[0]


def getIsOpposite_sex(curid, targetid):
    return 0 if getGenerById(curid) == getGenerById(targetid) else 1


def getHandCardlist(player):
    handcards = player['handinfo']['cards'].split(';') if 'cards' in player['handinfo'] else []
    if len(handcards) > 0:
        if handcards[-1] == "":
            handcards = handcards[0:-1]
    return handcards


def getEquipCardlist(player):
    equipcards = player['equipinfo']['cards'].split(';') if 'cards' in player['equipinfo'] else []
    if len(equipcards) > 0:
        if equipcards[-1] == "":
            equipcards = equipcards[0:-1]
    return [int(e) for e in equipcards]

def getJudgeCardlist(info):
    ret = []
    for ini in info:
        ret.append(ini['cardid'])
    return ret

def getCanUseTaoJiu(cards):
    return 1 if getCardNumBySpell(cards, 3) + getCardNumBySpell(cards, 82) > 0 else 0
############################################
curplayseat = 0
color2suitdict = {1: [1, 2], 2: [3, 4]}
arms_spell_list = [28, 29, 23, 24, 25, 26, 27, 87, 86, 30, 201,388,1128,1135,6008,6010,6009,]#subtype=1
equis_spell_list = [16, 200, 88, 89, 391,390,1129,1131,2055,6011,] ##subtype=2
add1_spell_list = [22, 21, 20, 90, ] #subType=3
red1_spell_list = [17, 18, 19, ] #subType=4
extar_spell_list = [700,3060,3061,3062,389,1134,6014,6015,6016,6018] #subtype=9

all_equip_list = arms_spell_list + equis_spell_list + add1_spell_list + red1_spell_list + extar_spell_list



#########################################
def getTablePhase(jdata, curseat):
    for item in jdata['Simulator']:
        if int(item['stateinfo']['baseinfo']['seatid']) == curseat:
            return int(item['stateinfo']['baseinfo']['curPhase'])


def getFriSeat(curseat):
    if curseat == 0:
        return 1
    elif curseat == 1:
        return 0
    elif curseat == 2:
        return 3
    elif curseat == 3:
        return 2


def getNextSeat(curseat):
    if curseat in [0, 1]:
        return 2
    else:
        return 0


def getOtherSeat(curseat):
    if curseat in [0, 1]:
        return 3
    else:
        return 1


### 座位号转换
def getTranSeat(tarseat, curseat):
    if curseat in [0, 1]:
        return tarseat
    else:
        if tarseat in [0, 1]:
            return tarseat + 2
        else:
            return tarseat - 2

def getPlayerSkillList(stateinfo):
    baseinfo = stateinfo['baseinfo']
    if 'charinfo' in baseinfo:
        skillinfo = [int(ii) for ii in baseinfo['charinfo'][1].split(';') if ii != ''] if baseinfo['isdead'] == '0' and  baseinfo['charinfo'][1] != '' else []
    else:
        skillinfo = [int(item['skillid']) for item in stateinfo['skillinfo']]
    
    return skillinfo

### 玩家信息
def getPlayerInfoWay1(stateinfo, curseat, needsex=True, maxspell=3):
    baseinfo = stateinfo['baseinfo']

    if int(baseinfo['isdead']) == 1:
        if needsex == True:
            ret = [0, 0, 0, 0, 0]
            ret.extend([0 for i in range(maxspell)])
        else:
            ret = [0, 0, 0, 0]
            ret.extend([0 for i in range(maxspell)])
        return ret

    skillinfo = getPlayerSkillList(stateinfo)
    ret = []
    # seat
    ret.append(int(getTranSeat(int(baseinfo['seatid']), curseat)))
    # charid
    ret.append(int(baseinfo['charid']))
    # gender
    if needsex:
        ret.append(getGenerById(int(baseinfo['charid'])))
    # spell
    for i in range(maxspell):
        if i < len(skillinfo):
            ret.append(int(skillinfo[i]))
        else:
            ret.append(0)
    # cur_nor_np or curhp
    ret.append(int(baseinfo['maxhp']))
    ret.append(int(baseinfo['curhp']))
    # curheromaxhp
    return ret

### 玩家信息
def getPlayerInfoWay2(stateinfo, curseat, maxspell=3, needsex=True, needcountry=False):
    baseinfo = stateinfo['baseinfo']

    if int(baseinfo['isdead']) == 1:
        if needsex == True and needcountry == True:
            ret = [0, 0, 0, 0, 0, 0]
            ret.extend([0 for i in range(maxspell)])
        elif needsex == True or needcountry == True:
            ret = [0, 0, 0, 0, 0]
            ret.extend([0 for i in range(maxspell)])
        else:
            ret = [0, 0, 0, 0]
            ret.extend([0 for i in range(maxspell)])
        return ret
    skillinfo =  getPlayerSkillList(stateinfo)
    ret = []
    # seat
    ret.append(getTranSeat(int(baseinfo['seatid']), curseat))
    # charid
    ret.append(int(baseinfo['charid']))
    # gender
    if needsex:
        ret.append(getGenerById(int(baseinfo['charid'])))
    # country
    if needcountry:
        ret.append(int(baseinfo['country']))

    # spell
    for i in range(maxspell):
        if i < len(skillinfo):
            ret.append(int(skillinfo[i]))
        else:
            ret.append(0)
    # cur_nor_np
    ret.append(int(baseinfo['maxhp']))
    # curheromaxhp
    ret.append(int(baseinfo['curhp']))
    return ret


### 玩家信息
def getPlayerInfoWay3(stateinfo, needsex=True):
    baseinfo = stateinfo['baseinfo']

    if int(baseinfo['isdead']) == 1:
        if needsex:
            return [0, 0, 0, 0, 0, 0, 0]
        else:
            return [0, 0, 0, 0, 0, 0]

    skillinfo = getPlayerSkillList(stateinfo)
    ret = []
    # charid
    ret.append(int(baseinfo['charid']))
    # gender
    if needsex:
        ret.append(getGenerById(int(baseinfo['charid'])))
    # spell
    for i in range(3):
        if i < len(skillinfo):
            ret.append(int(skillinfo[i]))
        else:
            ret.append(0)
    # cur_nor_np
    ret.append(int(baseinfo['maxhp']))
    # curheromaxhp
    ret.append(int(baseinfo['curhp']))
    return ret


### 玩家信息
def getPlayerInfoWay4(stateinfo, curseat):
    baseinfo = stateinfo['baseinfo']

    if int(baseinfo['isdead']) == 1:
            return [0, 0, 0, 0]
    ret = []
    # seat
    ret.append(getTranSeat(int(baseinfo['seatid']), curseat))
    # gender
    ret.append(getGenerById(int(baseinfo['charid'])))
    # cur_nor_np
    ret.append(int(baseinfo['maxhp']))
    # curheromaxhp
    ret.append(int(baseinfo['curhp']))
    return ret


#######################################
#### 手牌数据
#######################################
##old
def getCardSpellNumberColor(cards):
    ret = [0 for i in base_card_space]
    retnum = len(cards)
    for card in cards:
        if int(card) not in cardId_2_cardSpace:
            continue
        ret[base_card_space.index(cardId_2_cardSpace[int(card)])] += 1
    ret[0] = retnum
    return ret


############

def getHandCardSpellCount(cards):
    spellnum = [0 for i in range(59)]
    spellnum[0] = len(cards)
    for card in cards:
        if int(card) not in cardId_2_cardSpace:
            continue
        item = cardId_2_cardSpace[int(card)].split('_')
        if int(item[0]) == 1:
            if item[-1] == '0':
                spellnum[1] += 1
            elif item[-1] == '6':  # 火杀
                spellnum[2] += 1
            elif item[-1] == '7':  # 雷杀
                spellnum[3] += 1
        elif int(item[0]) == 2:  # 闪
            spellnum[4] += 1
        elif int(item[0]) == 3:  # 桃
            spellnum[5] += 1
        elif int(item[0]) == 4:  # 顺手牵羊
            spellnum[6] += 1
        elif int(item[0]) == 5:  # 过河拆桥
            spellnum[7] += 1
        elif int(item[0]) == 6:  # 五谷丰登
            spellnum[8] += 1
        elif int(item[0]) == 7:  # 无中生有
            spellnum[9] += 1
        elif int(item[0]) == 8:  # 决斗
            spellnum[10] += 1
        elif int(item[0]) == 9:  # 南蛮入侵
            spellnum[11] += 1
        elif int(item[0]) == 10:  # 万箭齐发
            spellnum[12] += 1
        elif int(item[0]) == 11:  # 闪电
            spellnum[13] += 1
        elif int(item[0]) == 12:  # 桃园结义
            spellnum[14] += 1
        elif int(item[0]) == 13:  # 无懈可击
            spellnum[15] += 1
        elif int(item[0]) == 14:  # 借刀杀人
            spellnum[16] += 1
        elif int(item[0]) == 15:  # 乐不思蜀
            spellnum[17] += 1
        elif int(item[0]) == 16:  # 八卦阵
            spellnum[18] += 1
        elif int(item[0]) == 17:  # 赤兔
            spellnum[19] += 1
        elif int(item[0]) == 18:  # 紫H
            spellnum[20] += 1
        elif int(item[0]) == 19:  # 大宛
            spellnum[21] += 1
        elif int(item[0]) == 20:  # 绝影
            spellnum[22] += 1
        elif int(item[0]) == 21:  # 的卢
            spellnum[23] += 1
        elif int(item[0]) == 22:  # 爪黄飞电
            spellnum[24] += 1
        elif int(item[0]) == 23:  # 诸葛连弩
            spellnum[25] += 1
        elif int(item[0]) == 24:  # 雌雄双股剑
            spellnum[26] += 1
        elif int(item[0]) == 25:  # 青G剑
            spellnum[27] += 1
        elif int(item[0]) == 26:  # 青龙偃月刀
            spellnum[28] += 1
        elif int(item[0]) == 27:  # 丈八蛇矛
            spellnum[29] += 1
        elif int(item[0]) == 28:  # 贯石斧
            spellnum[30] += 1
        elif int(item[0]) == 29:  # 方天画戟
            spellnum[31] += 1
        elif int(item[0]) == 30:  # 麒麟弓
            spellnum[32] += 1
        elif int(item[0]) == 82:  # 酒
            spellnum[33] += 1
        elif int(item[0]) == 83:  # 火攻
            spellnum[34] += 1
        elif int(item[0]) == 84:  # 兵粮寸断
            spellnum[35] += 1
        elif int(item[0]) == 85:  # 铁索连环
            spellnum[36] += 1
        elif int(item[0]) == 86:  # 古锭刀
            spellnum[37] += 1
        elif int(item[0]) == 87:  # 朱雀羽扇
            spellnum[38] += 1
        elif int(item[0]) == 88:  # 藤甲
            spellnum[39] += 1
        elif int(item[0]) == 89:  # 白银狮子
            spellnum[40] += 1
        elif int(item[0]) == 90:  # 骅骝
            spellnum[41] += 1
        elif int(item[0]) == 200:  # 仁王盾
            spellnum[42] += 1
        elif int(item[0]) == 201:  # 寒冰剑
            spellnum[43] += 1
        elif int(item[0]) == 388:  # 无双方天戟
            spellnum[44] += 1
        elif int(item[0]) == 390:  # 红棉百花袍
            spellnum[45] += 1
        elif int(item[0]) == 391:  # 玲珑狮蛮带
            spellnum[46] += 1
        elif int(item[0]) == 700:  # 木牛流马
            spellnum[47] += 1
        elif int(item[0]) == 1128:  # 鬼龙斩月刀
            spellnum[48] += 1
        elif int(item[0]) == 1129:  # 国风玉袍
            spellnum[49] += 1
        elif int(item[0]) == 1131:  # 奇门八阵
            spellnum[50] += 1
        elif int(item[0]) == 1135:  # 赤血青锋
            spellnum[51] += 1
        elif int(item[0]) == 2055:  # 护心镜
            spellnum[52] += 1
        elif int(item[0]) == 3060:  # 琼梳
            spellnum[53] += 1
        elif int(item[0]) == 3061:  # 犀梳
            spellnum[54] += 1
        elif int(item[0]) == 3062:  # 金梳
            spellnum[55] += 1
        elif int(item[0]) == 6008:  # 镔铁双戟
            spellnum[56] += 1
        elif int(item[0]) == 6009:  # 乌铁锁链
            spellnum[57] += 1
        elif int(item[0]) == 6010:  # 五行鹤翎扇
            spellnum[58] += 1
    return spellnum


def getCardNumColorList(cards):
    """
    根据输入的卡牌列表，统计黑色和红色卡牌的数量。

    参数:
    cards - 一个包含卡牌编号的列表，假设所有卡牌编号都是有效的。

    返回值:
    返回一个包含两个元素的列表，第1个元素表示红桃和方块的总数。 第2个元素表示黑桃和梅花的总数，
    """

    # 初始化结果列表，两个元素分别代表黑桃/梅花和红桃/方块的数量
    ret = [0 for i in range(2)]
    for card in cards:
        # 如果卡牌编号不在预定义的卡牌空间中，则跳过该卡牌
        if int(card) not in cardId_2_cardSpace:
            continue
        # 从卡牌编号中解析出花色信息
        suit = int(cardId_2_cardSpace[int(card)].split('_')[-2])

        # 根据花色，将卡牌计数加到相应的结果中
        ret[0 if suit in [1,2] else 1] += 1
    return ret

def getCardNumBySpellAndColor(cards, spell,color):
    retnum = 0
    for card in cards:
        if int(card) not in cardId_2_cardSpace:
            continue
        if int(cardId_2_cardSpace[int(card)].split('_')[0]) == spell and int(cardId_2_cardSpace[int(card)].split('_')[2]) in color:
            retnum += 1
    return retnum

def getCardNumSuitList(cards):
    ret = [0 for i in range(4)]
    for card in cards:
        if int(card) not in cardId_2_cardSpace:
            continue
        ret[int(cardId_2_cardSpace[int(card)].split('_')[-2]) - 1] += 1
    return ret


def getCardNumSuitListWithOutSpell(cards, spell):
    ret = [0 for i in range(4)]
    for card in cards:
        if int(card) not in cardId_2_cardSpace:
            continue
        item = cardId_2_cardSpace[int(card)].split('_')
        if int(item[0]) == spell:
            continue
        ret[int([-2]) - 1] += 1
    return ret


def getCardNumBySpell(cards, spell):
    retnum = 0
    for card in cards:
        if int(card) not in cardId_2_cardSpace:
            continue
        if int(cardId_2_cardSpace[int(card)].split('_')[0]) == spell:
            retnum += 1
    return retnum


def getCardNumBySpellAndSubtype(cards, spell, subtype):
    retnum = 0
    for card in cards:
        if int(card) not in cardId_2_cardSpace:
            continue
        if int(cardId_2_cardSpace[int(card)].split('_')[0]) == spell and int(
                cardId_2_cardSpace[int(card)].split('_')[3]) == subtype:
            retnum += 1
    return retnum


def getCardNumberColorSubType(cards):
    ret = [0 for i in base_card_space]
    retnum = len(cards)
    for card in cards:
        if int(card) not in cardId_2_cardSpace:
            continue
        ret[base_card_space.index(cardId_2_cardSpace[int(card)])] += 1
    ret[0] = retnum
    return ret


def getCardNumberColorSubTypeBySuit(cards, suit):
    retnum = 0
    ret = [0 for i in base_card_space]
    for card in cards:
        if int(card) not in cardId_2_cardSpace:
            continue
        if int(cardId_2_cardSpace[int(card)].split('_')[-1]) == suit:
            ret[base_card_space.index(cardId_2_cardSpace[int(card)])] += 1
            retnum += 1
    ret[0] = retnum
    return ret


def getCardNumberColorSubTypeByColor(cards, color):
    retnum = 0
    ret = [0 for i in base_card_space]
    for card in cards:
        if int(card) not in cardId_2_cardSpace:
            continue
        if int(cardId_2_cardSpace[int(card)].split('_')[-1]) in color2suitdict[color]:
            ret[base_card_space.index(cardId_2_cardSpace[int(card)])] += 1
    ret[0] = retnum
    return ret


def getCardNumberColorSubTypeBySpell(cards, spell):
    retnum = 0
    ret = [0 for i in base_card_space]
    for card in cards:
        if int(card) not in cardId_2_cardSpace:
            continue
        if int(cardId_2_cardSpace[int(card)].split('_')[0]) == spell:
            ret[base_card_space.index(cardId_2_cardSpace[int(card)])] += 1
    ret[0] = retnum
    return ret


######################################
##### 装备信息 old
######################################
equipspell2label = {
    28: 'curarms_gsf', 29: 'curarms_fthj', 23: 'curarms_zgln', 24: 'curarms_cxsgj', 25: 'curarms_qgj',
    26: 'curarms_qlyyd', 27: 'curarms_zbsm', 87: 'curarms_zqys', 86: 'curarms_gdd',
    30: 'curarms_qlg', 201: 'curarms_hbj', 16: 'curequis_bgz', 200: 'curequis_rwd', 88: 'curequis_tengjia',
    89: 'curequis_bysz', 22: 'curadd1_zhfd', 21: 'curadd1_dilu', 20: 'curadd1_jueying',
    90: 'curadd1_hualiu', 17: 'curreduce1_chitu', 18: 'curreduce1_zixin', 19: 'curreduce1_dawan',
}
equiparams = ['curarms_gsf', 'curarms_fthj', 'curarms_zgln', 'curarms_cxsgj', 'curarms_qgj', 'curarms_qlyyd',
              'curarms_zbsm', 'curarms_zqys', 'curarms_gdd',
              'curarms_qlg', 'curarms_hbj', 'curequis_bgz', 'curequis_rwd', 'curequis_tengjia', 'curequis_bysz',
              'curadd1_zhfd', 'curadd1_dilu', 'curadd1_jueying',
              'curadd1_hualiu', 'curreduce1_chitu', 'curreduce1_zixin', 'curreduce1_dawan', ]


def getEquipSpellOneHot(cards):
    ret = [0 for e in equiparams]
    for card in cards:
        if card not in cardId_2_cardSpace:
            continue
        item = cardId_2_cardSpace[int(card)].split('_')
        ret[equiparams.index(equipspell2label[int(item[0])])] = 1
    return ret


def getHaveEquisColor(cards):
    ret = [0 for i in range(5)]
    for card in cards:
        if card not in cardId_2_cardSpace:
            continue
        item = cardId_2_cardSpace[int(card)].split('_')
        if int(item[0]) in arms_spell_list:
            ret[0] = int(item[-2])
        elif int(item[0]) in equis_spell_list:
            ret[1] = int(item[-2])
        elif int(item[0]) in add1_spell_list:
            ret[2] = int(item[-2])
        elif int(item[0]) in red1_spell_list:
            ret[3] = int(item[-2])
        elif int(item[0]) in extar_spell_list:
            ret[4] = int(item[-2])
    return ret

def getHaveEquisColor_old(cards):
    ret = [0 for i in range(5)]
    for card in cards:
        if card not in cardId_2_cardSpace:
            continue
        item = cardId_2_cardSpace[int(card)].split('_')
        if int(item[0]) in arms_spell_list:
            ret[0] = int(item[-2])
        elif int(item[0]) in equis_spell_list:
            ret[1] = int(item[-2])
        elif int(item[0]) in add1_spell_list:
            ret[2] = int(item[-2])
        elif int(item[0]) in red1_spell_list:
            ret[3] = int(item[-2])
    return ret

def getEquisMark(cards):
    ret = [0 for i in range(5)]
    for card in cards:
        if card not in cardId_2_cardSpace:
            continue
        item = cardId_2_cardSpace[int(card)].split('_')
        if int(item[0]) in arms_spell_list:
            ret[0] = 1
        elif int(item[0]) in equis_spell_list:
            ret[1] = 1
        elif int(item[0]) in add1_spell_list:
            ret[2] = 1
        elif int(item[0]) in red1_spell_list:
            ret[3] = 1
        elif int(item[0]) in extar_spell_list:
            ret[4] = 1
    return ret


def getEquisIndex(cards):
    ret = [0 for i in range(5)]
    for card in cards:
        if card not in cardId_2_cardSpace:
            continue
        item = cardId_2_cardSpace[int(card)].split('_')
        if int(item[0]) in arms_spell_list:
            ret[0] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in equis_spell_list:
            ret[1] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in add1_spell_list:
            ret[2] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in red1_spell_list:
            ret[3] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in extar_spell_list:
            ret[4] = base_card_space.index(cardId_2_cardSpace[int(card)])
    return ret


def getEquisSpell(cards):
    ret = [0 for i in range(5)]
    for card in cards:
        if card not in cardId_2_cardSpace:
            continue
        item = cardId_2_cardSpace[int(card)].split('_')
        if int(item[0]) in arms_spell_list:
            ret[0] = int(item[0])
        elif int(item[0]) in equis_spell_list:
            ret[1] = int(item[0])
        elif int(item[0]) in add1_spell_list:
            ret[2] = int(item[0])
        elif int(item[0]) in red1_spell_list:
            ret[3] = int(item[0])
        elif int(item[0]) in extar_spell_list:
            ret[4] = int(item[0])
    return ret

def getEquisSpell_no_mnlm(cards):
    ret = [0 for i in range(4)]
    for card in cards:
        item = cardId_2_cardSpace[int(card)].split('_')
        if int(item[0]) in arms_spell_list:
            ret[0] = int(item[0])
        elif int(item[0]) in equis_spell_list:
            ret[1] = int(item[0])
        elif int(item[0]) in add1_spell_list:
            ret[2] = int(item[0])
        elif int(item[0]) in red1_spell_list:
            ret[3] = int(item[0])
    return ret


def getEquisIndexBySuit(cards, suit):
    ret = [0 for i in range(5)]
    for card in cards:
        if card not in cardId_2_cardSpace:
            continue
        item = cardId_2_cardSpace[int(card)].split('_')
        if int(item[-2]) != suit:
            continue
        if int(item[0]) in arms_spell_list:
            ret[0] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in equis_spell_list:
            ret[1] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in add1_spell_list:
            ret[2] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in red1_spell_list:
            ret[3] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in extar_spell_list:
            ret[4] = base_card_space.index(cardId_2_cardSpace[int(card)])
    return ret


def getEquisIndexByColor(cards, color):
    ret = [0 for i in range(5)]
    for card in cards:
        if card not in cardId_2_cardSpace:
            continue
        item = cardId_2_cardSpace[int(card)].split('_')
        if int(item[-2]) not in color2suitdict[color]:
            continue
        if int(item[0]) in arms_spell_list:
            ret[0] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in equis_spell_list:
            ret[1] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in add1_spell_list:
            ret[2] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in red1_spell_list:
            ret[3] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in extar_spell_list:
            ret[4] = base_card_space.index(cardId_2_cardSpace[int(card)])
    return ret


def getEquisIndexBySpell(cards, spell):
    ret = [0 for i in range(5)]
    for card in cards:
        if card not in cardId_2_cardSpace:
            continue
        item = cardId_2_cardSpace[int(card)].split('_')
        if int(item[0]) == spell:
            continue
        if int(item[0]) in arms_spell_list:
            ret[0] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in equis_spell_list:
            ret[1] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in add1_spell_list:
            ret[2] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in red1_spell_list:
            ret[3] = base_card_space.index(cardId_2_cardSpace[int(card)])
        elif int(item[0]) in extar_spell_list:
            ret[4] = base_card_space.index(cardId_2_cardSpace[int(card)])
    return ret


#####################################
#### 判定区信息 old
#################################、
def getJudgeSpellMark(info):
    ret = [0, 0, 0]
    for ini in info:
        if ini['spellid'] == '15':
            ret[0] = 1
        elif ini['spellid'] == '84':
            ret[1] = 1
        elif ini['spellid'] =='11':
            ret[2] = 1
    return ret


def getJudgeSpell(info):
    ret = [0, 0, 0]
    for ini in info:
        if ini['spellid'] == '15':
            ret[0] = 15
        elif ini['spellid'] == '84':
            ret[1] = 84
        elif ini['spellid'] == '11':
            ret[2] = 11
    return ret


def getJudgeSpellForFlash(info):
    for ini in info:
        if int(ini['spellid']) == 11:
            return 1
    return 0

def getJudgeSpellForLbss(info):
    for ini in info:
        if int(ini['spellid']) == 15:
            return 1
    return 0

def getJudgeSpellForBlcd(info):
    for ini in info:
        if int(ini['spellid']) == 84:
            return 1
    return 0


#####################################
#### 判定区信息
#################################
def getJudgeCardIndex(info):
    ret = [0, 0, 0]
    for ini in info:
        if int(ini['spellid']) == 15:
            ret[0] = base_card_space.index(cardId_2_cardSpace[int(ini['cardid'])])
        elif int(ini['spellid']) == 84:
            ret[1] = base_card_space.index(cardId_2_cardSpace[int(ini['cardid'])])
        elif int(ini['spellid']) == 11:
            ret[2] = base_card_space.index(cardId_2_cardSpace[int(ini['cardid'])])
    return ret


def getJudgeCardHaveSpell(info, spell):
    for ini in info:
        if int(ini['spellid']) == spell:
            return 1
    return 0


### 获取cansha状态
def getStatusCanSha(curplayer, sinfo):
    if int(curplayer['baseinfo']['charid']) == 3:
        return 1

    if len(curplayer['equipinfo']) > 0:
        equisCard = getEquipCardlist(curplayer)
        for card in equisCard:
            if int(cardId_2_cardSpace[int(card)].split('_')[0]) == 23:
                return 1

    for info in sinfo:
        if int(info['skillid']) == 1:
            return 1 if int(info['datas'].split(';')[0]) > 0 else 0
    return 0

def getNeedGiveupCard(curplayer):
    baseinfo = curplayer['baseinfo']
    curcardsnum = len(getHandCardlist(curplayer))
    curhp = int(baseinfo['curhp'])
    maxhp = int(baseinfo['maxhp'])
    skillinfo =  getPlayerSkillList(curplayer)

    if  712 in skillinfo:
        if curcardsnum > maxhp:
            return 1
    else:
        if curcardsnum > curhp:
            return 1
    return 0

### 获取usesha状态
def getStatusHaveUseSha(sinfo):
    for info in sinfo:
        if int(info['skillid']) == 1:
            # print(info['datas'], info['datas'].split(';'))
            return 1 if int(info['datas'].split(';')[1]) > 0 else 0
    return 0

def getChouFaCard(sinfo):
    ret = []
    for info in sinfo:
        if int(info['skillid']) == 7013:
            items = info['statusvalue'].split(';')
            for ii in range(3, len(items)):
                ret.append(ii)
    return ret

### 获取酒状态
def getStatusJiu(sinfo):
    for info in sinfo:
        if int(info['skillid']) == 82:
            return int(info['datas'].split(';')[1])
    return 0


### 获取铁索连环状态
def getStatusTslh(sinfo):
    for info in sinfo:
        if int(info['skillid']) == 85 and 'statusvalue' in info:
            return int(info['statusvalue'])
    return 0


###关
def deal_relationship_by_seat(tarseat, curseat):
    curseat = int(curseat)
    tarseat = int(tarseat)
    if tarseat == curseat:
        return 0
    elif curseat == 0 and tarseat == 1:
        return 1
    elif curseat == 1 and tarseat == 0:
        return 1
    elif curseat == 2 and tarseat == 3:
        return 1
    elif curseat == 3 and tarseat == 2:
        return 1
    return 2


###关系
def deal_relationship_by_seat_for_13(datas, curseat):
    curseat = int(curseat)
    if datas[1] in [4, 5, 6, 7, 8, 9, 10, 15, 83, 84, 11]:
        return deal_relationship_by_seat(datas[3], curseat)
    elif datas[1] == 14:
        return deal_relationship_by_seat(datas[5], curseat)
    elif datas[1] in [12, 85]:
        return deal_relationship_by_seat(datas[2], curseat)


##can_save
def get_feather_can_save(curplayer, curcolorinfo, equiscolor, relationship, curnum_tao, curnum_jiu):
    if relationship == 0:
        if curnum_tao + curnum_jiu > 0:
            return 1
        elif int(curplayer['baseinfo']['charid']) == 45:  # 董卓
            if curcolorinfo[2] > 0:
                return 1
        elif int(curplayer['baseinfo']['charid']) == 22:  # 华佗
            if (curcolorinfo[0] + curcolorinfo[1] > 0) or (equiscolor[0] in [1, 2]) or (equiscolor[1] in [1, 2]) or (equiscolor[2] in [1, 2]) or (equiscolor[3] in [1, 2]):
                return 1
    else:
        if curnum_tao > 0:
            return 1
        elif int(curplayer['baseinfo']['charid']) == 22:  # 华佗
            if (curcolorinfo[0] + curcolorinfo[1] > 0) or (equiscolor[0] in [1, 2]) or (equiscolor[1] in [1, 2]) or (equiscolor[2] in [1, 2]) or (equiscolor[3] in [1, 2]):
                return 1
    return 0


##是否可以无懈
def get_feather_can_change(curplayer, curcolorinfo, equiscolor, curnum_wxkj):
    if curnum_wxkj > 0:
        return 1
    elif int(curplayer['baseinfo']['charid']) == 37 and curcolorinfo[2] + curcolorinfo[3] > 0:  # 魏延
        return 1
    elif int(curplayer['baseinfo']['charid']) == 29 and np.sum(equiscolor) > 0:  # 诸葛卧龙
        return 1
    return 0


### 获取是否翻面状态
def getStatusIsTurnOver(binfo):
    return int(binfo['isTurnOver'])


### 获取当前玩家的信息
def getPlayerInfoBySeat(jdata, curseat):
    for item in jdata['Simulator']:
        if int(item['stateinfo']['baseinfo']['seatid']) == int(curseat):
            return item['stateinfo']
    return {}

##黑杀仁王盾
def getFeature_hs_rwd(jdata):
    actionPID = int(jdata['Labelinfo'][0]['actionPID'])
    if actionPID == 21219:
        return 0
    if actionPID == 21210:
        spellId = int(jdata['Labelinfo'][0]['useCard']['spellId'])
    elif actionPID == 21212:
        spellId = int(jdata['Labelinfo'][0]['useSpell']['spellId'])

    if actionPID == 21210 and int(jdata['Labelinfo'][0]['useCard']['spellId']) == 1:
        tarseat = [int(seat) for seat in jdata['Labelinfo'][0]['useCard']['datas'].split(';')][0]
        usecard = int(jdata['Labelinfo'][0]['useCard']['cardId'])
    elif actionPID == 21212 and int(jdata['Labelinfo'][0]['useSpell']['spellId']) in [33, 27]:
        datas = [card for card in jdata['Labelinfo'][0]['useSpell']['datas'].split(';')]
        datas = datas if datas[-1] != "" else datas[0:-1]
        tarseat = int(datas[0])
        if spellId == 33:
            usecard = int(datas[-1])
        elif spellId == 37:
            usecard = int(datas[-1])
    else:
        return 0
    if spellId in [1, 33, 37]:
        targetPlayer = getPlayerInfoBySeat(jdata, tarseat)
        if len(targetPlayer['equipinfo']) > 0:
            equipspell = getEquisSpell(getEquipCardlist(targetPlayer))
            if int(equipspell[1]) == 200:
                if spellId != 27 and int(cardId_2_cardSpace[usecard].split("_")[-2]) in [3, 4]:
                    return 1
                else:
                    if int(cardId_2_cardSpace[usecard].split("_")[-2]) in [3, 4] and int(
                            cardId_2_cardSpace[usecard].split("_")[-2]) in [3, 4]:
                        return 1
    return 0

#普通杀藤甲
def getFeature_norsha_tj(jdata, curseat):
    actionPID = int(jdata['Labelinfo'][0]['actionPID'])

    if actionPID in [21219, 21220, 21209]:
        return 0

    if actionPID == 21210:
        spellId = int(jdata['Labelinfo'][0]['useCard']['spellId'])
    elif actionPID == 21212:
        spellId = int(jdata['Labelinfo'][0]['useSpell']['spellId'])

    if actionPID == 21210 and int(jdata['Labelinfo'][0]['useCard']['spellId']) == 1:
        tarseat = [int(seat) for seat in jdata['Labelinfo'][0]['useCard']['datas'].split(';')][0]
    elif actionPID == 21212 and int(jdata['Labelinfo'][0]['useSpell']['spellId']) in [33, 27, 37]:
        tarseat = int([card for card in jdata['Labelinfo'][0]['useSpell']['datas'].split(';')][0])

    curplayer = getPlayerInfoBySeat(jdata, curseat)
    curequipspell = getEquisSpell(getEquipCardlist(curplayer))
    if int(curequipspell[0]) == 87:
        return 0

    if (spellId in [27, 33, 37] and actionPID == 21212) or (
            (spellId == 1 and actionPID == 21210) and cardId_2_cardSpace[
        int(jdata['Labelinfo'][0]['useCard']['cardId'])] in sha_type_space[0]):
        targetPlayer = getPlayerInfoBySeat(jdata, tarseat)
        if len(targetPlayer['equipinfo']) > 0:
            equipspell = getEquisSpell(getEquipCardlist(targetPlayer))
            if int(equipspell[1]) == 88:
                return 1
    return 0

def get_target_within_range_attack(curPlayer, tarPlayer, own_alive_number, enemy_alive_number, cur_equips, tar_equips,
                                   actionoutcards=0):
    cur_seat = getTranSeat(int(curPlayer['baseinfo']['seatid']), int(curPlayer['baseinfo']['seatid']))
    target_seat = getTranSeat(int(tarPlayer['baseinfo']['seatid']), int(curPlayer['baseinfo']['seatid']))
    cur_heroid = int(curPlayer['baseinfo']['charid'])
    cur_hero_hp = int(curPlayer['baseinfo']['curhp'])
    target_hero_hp = int(tarPlayer['baseinfo']['curhp'])
    target_hero_id = int(tarPlayer['baseinfo']['charid'])
    if target_hero_hp == 0:
        return [0, 0]
    if cur_seat == 0:
        if target_seat == 2:
            if enemy_alive_number < 2 or own_alive_number < 2:
                distance = 0
            else:
                distance = 1
        else:
            distance = 0
    else:
        if target_seat == 3:
            if enemy_alive_number < 2 or own_alive_number < 2:
                distance = 0
            else:
                distance = 1
        else:
            distance = 0
    spell_statu_dic = curPlayer['statusinfo']
    reduce1 = cur_equips[3]
    if reduce1 > 0:
        distance -= 1

    if cur_heroid in [101]:
        distance -= 1

    add1 = tar_equips[2]
    if add1 > 0:
        distance += 1
    
    if target_hero_id in [101] and target_hero_hp <= 2:
        distance += 1

    # 烈弓杀特殊判断
    if cur_heroid in [26] and actionoutcards != 0:
        number = cardId_2_cardSpace[actionoutcards].split("_")[1]
        distance -= (number - 1)
    # 邓艾屯田特殊判断
    if cur_heroid in [51]:
        if 123 in spell_statu_dic:
            distance -= int(spell_statu_dic[123])
    # 魏延奇谋特殊判断
    if cur_heroid in [27]:
        if 296 in spell_statu_dic:
            distance -= int(spell_statu_dic[296])
    # sp潘凤特殊判断

    if cur_heroid in [6, 303, 2054, 167, 2064, 462, 39]:  # 马术距离判断
        distance -= 1

    # 界黄盖诈降特殊判断
    if cur_heroid in [307] and actionoutcards != 0:
        if 711 in spell_statu_dic:
            color = cardId_2_cardSpace[actionoutcards].split("_")[2]
            if color in [1, 2]:
                return [1, distance + 1]
    # #(界)贾诩乱武特殊判断
    # if cur_heroid in [484, 48]:
    #     if source_spell in [118, 3090]:
    #         return [1, distance + 1]

    # 界关羽特殊判断
    if cur_heroid in [300] and actionoutcards != 0:
        color = cardId_2_cardSpace[actionoutcards].split("_")[2]
        if color == 2:
            return [1, distance + 1]
    # 许攸成略特殊判断
    if cur_heroid in [406] and actionoutcards != 0:
        if 814 in spell_statu_dic:
            color = cardId_2_cardSpace[actionoutcards].split("_")[2]
            if len(spell_statu_dic[814]) > 1:
                out_color = spell_statu_dic[814].split("_")
            else:
                out_color = [spell_statu_dic[814]]
            if str(color) in out_color:
                return [1, distance + 1]
    # sp马超特殊判断
    if cur_heroid in [107]:
        if cur_hero_hp >= target_hero_hp:
            return [1, 1]
    distance_real = distance

    arm = cur_equips[0]
    if arm > 0:
        if arm in [28, 27, 26]:
            distance -= 2
        elif arm in [24, 25, 86, 201]:
            distance -= 1
        elif arm in [87, 29]:
            distance -= 3
        elif arm in [30]:
            distance -= 4

    distance_real = distance_real + 1
    if distance_real < 0:
        distance_real = max(1, distance_real)

    if distance > 0:
        return [0, distance_real]
    else:
        return [1, distance_real]


def get_target_within_range_spell(curPlayer, tarPlayer, own_alive_number, enemy_alive_number, cur_equips, tar_equips):
    cur_seat = getTranSeat(int(curPlayer['baseinfo']['seatid']), int(curPlayer['baseinfo']['seatid']))
    target_seat = getTranSeat(int(tarPlayer['baseinfo']['seatid']), int(curPlayer['baseinfo']['seatid']))
    cur_heroid = int(curPlayer['baseinfo']['charid'])

    target_hero_hp = int(tarPlayer['baseinfo']['curhp'])
    target_hero_id = int(tarPlayer['baseinfo']['charid'])
    if target_hero_hp == 0:
        return [0,0]

    if cur_seat == 0:
        if target_seat == 2:
            if enemy_alive_number < 2 or own_alive_number < 2:
                distance = 0
            else:
                distance = 1
        else:
            distance = 0
    else:
        if target_seat == 3:
            if enemy_alive_number < 2 or own_alive_number < 2:
                distance = 0
            else:
                distance = 1
        else:
            distance = 0

    spell_statu_dic = curPlayer['statusinfo']
    reduce1 = cur_equips[3]
    if reduce1 > 0:
        distance -= 1

    if cur_heroid in [101]:
        distance -= 1

    add1 = tar_equips[2]
    if add1 > 0:
        distance += 1
    
    if target_hero_id in [101] and target_hero_hp <= 2:
        distance += 1

    # 邓艾屯田特殊判断
    if cur_heroid in [51]:
        for item in spell_statu_dic:
            if 123 == int(item['skillid']):
                disitem = item['statusvalue'].split(";")
                if disitem[-1] == '':
                    disitem.pop()
                distance -= len(disitem)
                break
    # 魏延奇谋特殊判断
    if cur_heroid in [27]:
        for item in spell_statu_dic:
            if 296 == int(item['skillid']):
                disitem = item['statusvalue'].split(";")
                if disitem[-1] == '':
                    disitem.pop()
                distance -= int(disitem[0])

    # print(cur_heroid, distance)
    if cur_heroid in [6, 303, 2054, 167, 2064, 462, 39]:  # 马术距离判断
        distance -= 1

    distance_real = distance + 1
    if distance_real < 0:
        distance_real = max(1, distance_real)

    if distance > 0:
        return [0, distance_real]
    else:
        return [1, distance_real]


def getFeatureAttrRange(cur_equips):
    arm = cur_equips[0]
    distance = 1
    if arm > 0:
        if arm in [28, 27, 26, 201]:
            distance -= 3
        elif arm in [24, 25, 86]:
            distance = 2
        elif arm in [87, 29]:
            distance = 4
        elif arm in [30]:
            distance = 5
    return distance


def getFeatureLieGongSha(heroid, labelinfo, tarhandsnum, curhp, attrange):
    if int(heroid) in [26, 61] and int(labelinfo[0]['actionPID']) == 21210 and int(
            labelinfo[0]['useCard']['spellId']) == 1:
        if int(tarhandsnum) >= int(curhp) or int(tarhandsnum) <= attrange:
            return 1
    return 0


def getFeature_can_change(player1, player2):
    if int(player1['baseinfo']['charid']) in [16, 212] or int(player2['baseinfo']['charid']) in [16, 212]:
        return 1
    return 0


def getFeature_hs_rwd(jdata):
    actionPID = int(jdata['Labelinfo'][0]['actionPID'])
    if actionPID == 21219:
        return 0
    if actionPID == 21210:
        spellId = int(jdata['Labelinfo'][0]['useCard']['spellId'])
    elif actionPID == 21212:
        spellId = int(jdata['Labelinfo'][0]['useSpell']['spellId'])

    if actionPID == 21210 and int(jdata['Labelinfo'][0]['useCard']['spellId']) == 1:
        tarseat = [int(seat) for seat in jdata['Labelinfo'][0]['useCard']['datas'].split(';')][0]
        usecard = int(jdata['Labelinfo'][0]['useCard']['cardId'])
    elif actionPID == 21212 and int(jdata['Labelinfo'][0]['useSpell']['spellId']) in [33, 27]:
        datas = [card for card in jdata['Labelinfo'][0]['useSpell']['datas'].split(';')]
        datas = datas if datas[-1] != "" else datas[0:-1]
        tarseat = int(datas[0])
        if spellId == 33:
            usecard = int(datas[-1])
        elif spellId == 37:
            usecard = int(datas[-1])
    else:
        return 0
    if spellId in [1, 33, 37]:
        targetPlayer = getPlayerInfoBySeat(jdata, tarseat)
        if len(targetPlayer['equipinfo']) > 0:
            equipspell = getEquisSpell(getEquipCardlist(targetPlayer))
            if int(equipspell[1]) == 200:
                if spellId != 27 and int(cardId_2_cardSpace[usecard].split("_")[-2]) in [3, 4]:
                    return 1
                else:
                    if int(cardId_2_cardSpace[usecard].split("_")[-2]) in [3, 4] and int(
                            cardId_2_cardSpace[usecard].split("_")[-2]) in [3, 4]:
                        return 1
    return 0


def getFeatureCanQingNang(curplayer):
    if int(curplayer['baseinfo']['charid']) != 22:
        return 0
    for item in curplayer["statusinfo"]:
        if int(item['skillid']) == 65:
            return 1 if int(item['statusvalue']) == 0 else 0
    return 1


def getFeature_js_bysz(jdata, statejiu):
    actionPID = int(jdata['Labelinfo'][0]['actionPID'])
    if actionPID in [21219, 21220, 21209]:
        return 0
    if actionPID == 21210:
        spellId = int(jdata['Labelinfo'][0]['useCard']['spellId'])
    elif actionPID == 21212:
        spellId = int(jdata['Labelinfo'][0]['useSpell']['spellId'])

    if actionPID == 21210 and int(jdata['Labelinfo'][0]['useCard']['spellId']) == 1:
        tarseat = [int(seat) for seat in jdata['Labelinfo'][0]['useCard']['datas'].split(';')][0]
    elif actionPID == 21212 and int(jdata['Labelinfo'][0]['useSpell']['spellId']) in [33, 27, 37]:
        tarseat = int([card for card in jdata['Labelinfo'][0]['useSpell']['datas'].split(';')][0])
    else:
        return 0
    if (spellId in [1, 33, 37, ] or (actionPID == 21212 and spellId == 27)) and statejiu == 1:
        targetPlayer = getPlayerInfoBySeat(jdata, tarseat)
        if len(targetPlayer['equipinfo']) > 0:
            equipspell = getEquisSpell(getEquipCardlist(targetPlayer))
            if int(equipspell[1]) == 89:
                return 1
    return 0


def getFeature_hs_tj(jdata, curseat):
    actionPID = int(jdata['Labelinfo'][0]['actionPID'])
    if actionPID in [21219, 21220, 21209]:
        return 0

    if actionPID == 21210 and int(jdata['Labelinfo'][0]['useCard']['spellId']) == 1:
        tarseat = [int(seat) for seat in jdata['Labelinfo'][0]['useCard']['datas'].split(';')][0]
        curplayer = getPlayerInfoBySeat(jdata, curseat)
        targetPlayer = getPlayerInfoBySeat(jdata, tarseat)
        cardlabel = cardId_2_cardSpace[int(jdata['Labelinfo'][0]['useCard']['cardId'])]
        if cardlabel in sha_type_space[6]:
            if len(targetPlayer['equipinfo']) > 0:
                equipspell = getEquisSpell(getEquipCardlist(targetPlayer))
                if int(equipspell[1]) == 88:
                    return 1
        elif cardlabel in sha_type_space[0] and len(curplayer['equipinfo']) > 0 and len(targetPlayer['equipinfo']) > 0:
            curequipspell = getEquisSpell(getEquipCardlist(curplayer))
            tarequipspell = getEquisSpell(getEquipCardlist(targetPlayer))
            if int(curequipspell[0]) == 87 and int(tarequipspell[1]) == 88:
                return 1
    return 0


def getFeature_norsha_tj(jdata, curseat):
    actionPID = int(jdata['Labelinfo'][0]['actionPID'])

    if actionPID in [21219, 21220, 21209]:
        return 0

    if actionPID == 21210:
        spellId = int(jdata['Labelinfo'][0]['useCard']['spellId'])
    elif actionPID == 21212:
        spellId = int(jdata['Labelinfo'][0]['useSpell']['spellId'])

    if actionPID == 21210 and int(jdata['Labelinfo'][0]['useCard']['spellId']) == 1:
        tarseat = [int(seat) for seat in jdata['Labelinfo'][0]['useCard']['datas'].split(';')][0]
    elif actionPID == 21212 and int(jdata['Labelinfo'][0]['useSpell']['spellId']) in [33, 27, 37]:
        tarseat = int([card for card in jdata['Labelinfo'][0]['useSpell']['datas'].split(';')][0])

    curplayer = getPlayerInfoBySeat(jdata, curseat)
    curequipspell = getEquisSpell(getEquipCardlist(curplayer))
    if int(curequipspell[0]) == 87:
        return 0

    if (spellId in [27, 33, 37] and actionPID == 21212) or (
            (spellId == 1 and actionPID == 21210) and cardId_2_cardSpace[
        int(jdata['Labelinfo'][0]['useCard']['cardId'])] in sha_type_space[0]):
        targetPlayer = getPlayerInfoBySeat(jdata, tarseat)
        if len(targetPlayer['equipinfo']) > 0:
            equipspell = getEquisSpell(getEquipCardlist(targetPlayer))
            if int(equipspell[1]) == 88:
                return 1
    return 0


def getFeature_is_sgjbgz(jdata):
    actionPID = int(jdata['Labelinfo'][0]['actionPID'])

    if actionPID in [21219, 21220, 21209]:
        return 0

    if actionPID == 21210:
        spellId = int(jdata['Labelinfo'][0]['useCard']['spellId'])
    elif actionPID == 21212:
        spellId = int(jdata['Labelinfo'][0]['useSpell']['spellId'])

    if actionPID == 21210 and int(jdata['Labelinfo'][0]['useCard']['spellId']) == 1:
        tarseat = [int(seat) for seat in jdata['Labelinfo'][0]['useCard']['datas'].split(';')][0]
    elif actionPID == 21212 and int(jdata['Labelinfo'][0]['useSpell']['spellId']) in [33, 27, 37]:
        tarseat = int([card for card in jdata['Labelinfo'][0]['useSpell']['datas'].split(';')][0])

    if (spellId in [27, 33, 37, ] and actionPID == 21212) or (spellId == 1 and actionPID == 21210):
        targetPlayer = getPlayerInfoBySeat(jdata, tarseat)
        if len(targetPlayer['equipinfo']) > 0:
            equipspell = getEquisSpell(getEquipCardlist(targetPlayer))
            if int(equipspell[1]) == 16 and int(targetPlayer['baseinfo']['charid']) == 20:
                return 1
    return 0


def getFeature_is_liegong(curplayer, equipspell, jdata):
    actionPID = int(jdata['Labelinfo'][0]['actionPID'])
    if actionPID in [21219, 21220, 21209]:
        return 0

    if actionPID == 21210 and int(jdata['Labelinfo'][0]['useCard']['spellId']) == 1:
        tarseat = [int(seat) for seat in jdata['Labelinfo'][0]['useCard']['datas'].split(';')][0]
        targetPlayer = getPlayerInfoBySeat(jdata, tarseat)
        if len(targetPlayer['handinfo']) > 0:
            targetcardnum = len(targetPlayer['handinfo']['cards'].split(';'))
        else:
            targetcardnum = 0
        return getFeatureLieGongSha(curplayer['baseinfo']['charid'], jdata['Labelinfo'], targetcardnum,
                                    curplayer['baseinfo']['curhp'], getFeatureAttrRange(equipspell))
    return 0


def getFeature_cxsgj_inbuff(curPlayer, targetPlayer):
    if curPlayer['baseinfo']['gender'] == targetPlayer['baseinfo']['gender']:
        return 0
    else:
        if 'cards' in curPlayer['equipinfo']:
            cur_equips = getEquisSpell(getEquipCardlist(curPlayer))
            if cur_equips[0] == 24:
                return 1
            else:
                return 0
        else:
            return 0


def getActionIdxLabelBySpell(pid, spell, subtype):
    subtype = -1 if subtype == 0 else subtype
    if pid == 21212:
        actionlabel = f"{1}_{spell}_{subtype}"
    elif pid == 21210:
        actionlabel = f"{2}_{spell}_{subtype}"
    return target_action_space.index(actionlabel)


def getCardIdxLabelBycard(card):
    return base_card_space.index(cardId_2_cardSpace[card])


def getTargetIdxLabelBySeat(targetseat1, targetseat2):
    if targetseat1 != -1 and targetseat2 != -1 and targetseat1 != targetseat2:  # 说明是多目标，特殊表示
        return target_seat_list.index((targetseat1 + 1) * 4 + targetseat2)
    return target_seat_list.index(targetseat1)


def getAcionIdxLabel(Labelinfo):
    if int(Labelinfo[0]['actionPID']) == 21212:
        actiontype = 1
        spell = Labelinfo[0]['useSpell']['spellId']
        actionlabel = f"{actiontype}_{spell}_-1"
    elif int(Labelinfo[0]['actionPID']) == 21210:
        actiontype = 2
        lspell = int(cardId_2_cardSpace[int(Labelinfo[0]['useCard']['cardId'])].split('_')[0])
        if lspell == 1:
            if cardId_2_cardSpace[int(Labelinfo[0]['useCard']['cardId'])] in sha_type_space[6]:
                actionlabel = f"{actiontype}_{lspell}_6"
            elif cardId_2_cardSpace[int(Labelinfo[0]['useCard']['cardId'])] in sha_type_space[7]:
                actionlabel = f"{actiontype}_{lspell}_7"
            else:
                actionlabel = f"{actiontype}_{lspell}_-1"
        else:
            actionlabel = f"{actiontype}_{lspell}_-1"
    elif int(Labelinfo[0]['actionPID']) == 21219:
        actionlabel = f"{0}_{-1}_-1"
    elif int(Labelinfo[0]['actionPID']) == 21209 and int(Labelinfo[0]['moveCard']['typeMove']) == 12:
        actionlabel = "1_85_-1"
    else:
        return

    return target_action_space.index(actionlabel) if actionlabel in target_action_space else -1

def getAcionSpell(Labelinfo):
    if int(Labelinfo[0]['actionPID']) == 21212:
        lspell = int(Labelinfo[0]['useSpell']['spellId'])
        return lspell
    elif int(Labelinfo[0]['actionPID']) == 21210:
        card = int(Labelinfo[0]['useCard']['cardId'])
        card_spell = cardId_2_cardSpace[card].split('_')[0]
        return int(card_spell)
        # lspell = int(Labelinfo[0]['useCard']['spellId'])
    elif int(Labelinfo[0]['actionPID']) == 21219:
        lspell = 0
    elif int(Labelinfo[0]['actionPID']) == 21209 and int(Labelinfo[0]['moveCard']['typeMove']) == 12:
        lspell = 85
    else:
        return -1

    return lspell


def getAcionTarget(Labelinfo):
    def tran_action_seat(showcard, source):
        if source <= -1 or source > 3:
            return -1
        if showcard in [0, 1]:
            return source
        elif showcard in [2, 3]:
            return (source + 2) % 4

    actionPID = int(Labelinfo[0]['actionPID'])
    targetseat1 = -1
    targetseat2 = -1
    if actionPID == 21210:
        curseat = int(Labelinfo[0]['useCard']['srcSeatId'])
        if int(Labelinfo[0]['useCard']['destCnt']) in [0, 3]:
            return 0
        elif int(Labelinfo[0]['useCard']['destCnt']) == 1:
            targetseat1 = tran_action_seat(curseat, int(Labelinfo[0]['useCard']['datas'].split(';')[0]))
        elif int(Labelinfo[0]['useCard']['destCnt']) == 2:
            targetseat1 = tran_action_seat(curseat, int(Labelinfo[0]['useCard']['datas'].split(';')[0]))
            targetseat2 = tran_action_seat(curseat, int(Labelinfo[0]['useCard']['datas'].split(';')[1]))
    elif actionPID == 21212:
        curseat = int(Labelinfo[0]['useSpell']['srcSeatId'])
        if int(Labelinfo[0]['useSpell']['destCount']) in [0, 3]:
            return 0
        elif int(Labelinfo[0]['useSpell']['destCount']) == 1:
            targetseat1 = tran_action_seat(curseat, int(Labelinfo[0]['useSpell']['datas'].split(';')[0]))
        elif int(Labelinfo[0]['useSpell']['destCount']) == 2:
            targetseat1 = tran_action_seat(curseat, int(Labelinfo[0]['useSpell']['datas'].split(';')[0]))
            targetseat2 = tran_action_seat(curseat, int(Labelinfo[0]['useSpell']['datas'].split(';')[1]))
    if targetseat1 != -1 and targetseat2 != -1 and targetseat1 != targetseat2:  # 说明是多目标，特殊表示
        return target_seat_list.index((targetseat1 + 1) * 4 + targetseat2)
    if (targetseat1 != -1 and targetseat1 is not None) or targetseat1 == targetseat2:
        return target_seat_list.index(targetseat1)
    return 0


def getAcionCardidx(Labelinfo):
    actionPID = int(Labelinfo[0]['actionPID'])
    if actionPID == 21219:
        return 0
    if actionPID == 21210:
        cardId = int(Labelinfo[0]['useCard']['cardId'])
    elif actionPID == 21212:
        cardId = 0
        if int(Labelinfo[0]['useSpell']['useCardCount']) > 0:
            cards = Labelinfo[0]['useSpell']['datas'].split(';')
            cards = cards[0:-1] if cards[-1] == "" else cards
            cards = cards[1:] if cards[0] == "" else cards
            cardId = int([card for card in cards][-1])
    elif int(Labelinfo[0]['actionPID']) == 21209:
        cards = Labelinfo[0]['moveCard']['datas'].split(';')
        cardId = int([card for card in cards][-1])
    else:
        return 0
    return base_card_space.index(cardId_2_cardSpace[cardId]) if cardId in cardId_2_cardSpace else -1


def getAcionCardList(Labelinfo):
    actionPID = int(Labelinfo[0]['actionPID'])
    cardIdlist = []
    if actionPID == 21210:
        cardIdlist.append(int(Labelinfo[0]['useCard']['cardId']))
    elif actionPID == 21212:
        if int(Labelinfo[0]['useSpell']['useCardCount']) > 0:
            destcount = int(Labelinfo[0]['useSpell']['destCount'])
            cards = Labelinfo[0]['useSpell']['datas'].split(';')
            cards = cards[0:-1] if cards[-1] == "" else cards
            cards = cards[1:] if cards[0] == "" else cards
            cardIdlist.extend([int(card) for card in cards][destcount:])
    elif int(Labelinfo[0]['actionPID']) == 21209:
        cardIdlist.append(int(Labelinfo[0]['moveCard']['datas']))
    return [base_card_space.index(cardId_2_cardSpace[cardId]) for cardId in cardIdlist if cardId in cardId_2_cardSpace ]


def get_action_FriplayerbaseInfo(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equipspell):
    ret = []
    ## 武将基础信息
    if int(friplayer['baseinfo']['isdead']) == 0:
        ret.extend(getPlayerInfoWay2(friplayer, curseat))
        # fricardnum',
        fricardnum = 0
        cards = getHandCardlist(friplayer)
        ##'fricardnum',
        fricardnum = len(cards)
        ret.append(fricardnum)
        # frinum_total_sha
        ret.append(getCardNumBySpell(cards, 1))
        # frinum_shan
        ret.append(getCardNumBySpell(cards, 2))
        # frinum_tao
        ret.append(getCardNumBySpell(cards, 3))
        # frinum_wxkj
        ret.append(getCardNumBySpell(cards, 13))
        # frinum_jiu
        ret.append(getCardNumBySpell(cards, 82))
        # equip onehot
        equipcards = getEquipCardlist(friplayer)
        ret.extend(getEquisSpell(equipcards))
        friequipMark = getEquisMark(equipcards)
        #'fri_status_lbss','fri_status_blcd','fri_status_flash',
        ret.extend(getJudgeSpell(friplayer['judgeinfo']))
        # 'fristate_tslh',
        ret.append(getStatusTslh(friplayer['statusinfo']))
        # fri_inrange_attr
        fri_inrange_attr = get_target_within_range_attack(curplayer, friplayer, own_alive_number, emery_alive_num, equipspell, friequipMark)
        ret.append(fri_inrange_attr[0])
        # fri_spell_range
        fri_spell_range = get_target_within_range_spell(curplayer, friplayer, own_alive_number, emery_alive_num, equipspell, friequipMark)
        ret.append(fri_spell_range[0])
        # fri_have_handcards
        ret.append(1 if fricardnum > 0 else 0)
    else:
        ret.extend([0 for i in range(26)])
    return ret

def get_action_EmeryplayerbaseInfo_base(curplayer, enemyplayer, own_alive_number, enemy_alive_num, equipspell):
    ret = []
    if int(enemyplayer['baseinfo']['isdead']) == 0:
        ret.extend(getPlayerInfoWay3(enemyplayer))
        emeryhandcards = getHandCardlist(enemyplayer)
        ret.append(len(emeryhandcards))
        # equisspell
        equipcards = getEquipCardlist(enemyplayer)
        ret.extend(getEquisSpell(equipcards))
        nextequipMark = getEquisMark(equipcards)
        ret.extend(getJudgeSpell(enemyplayer['judgeinfo']))
        #state_tslh
        ret.append(getStatusTslh(enemyplayer['statusinfo']))
        #inrange_attr
        inrange_attr = get_target_within_range_attack(curplayer, enemyplayer, own_alive_number, enemy_alive_num,
                                                           equipspell, nextequipMark)
        ret.append(inrange_attr[0])
        #spell_range
        spell_range = get_target_within_range_spell(curplayer, enemyplayer, own_alive_number, enemy_alive_num,
                                                         equipspell, nextequipMark)
        ret.append(spell_range[0])
        #have_handcards
        ret.append(1 if len(emeryhandcards) > 0 else 0)
        #opposite_sex
        ret.append(getIsOpposite_sex(curplayer['baseinfo']['charid'], enemyplayer['baseinfo']['charid']))
        #be_lbss
        ret.append(deal_enemy_be_lbss(curplayer, enemyplayer))
        #be_lbss
        ret.append(deal_enemy_be_blcd(curplayer, enemyplayer, len(emeryhandcards), spell_range[1]))
        #be_ssqy
        ret.append(deal_enemy_be_ssqy(curplayer, enemyplayer, spell_range))
        #be_ghcq
        ret.append(deal_enemy_be_ghcq(curplayer, enemyplayer))
        #be_sha
        ret.append(deal_enemy_be_sha(curplayer, enemyplayer, len(emeryhandcards), inrange_attr[0]))
        #be_juedou
        ret.append(deal_enemy_be_juedou(curplayer, enemyplayer, len(emeryhandcards)))
        # 是否在距离范围
        ret.append(spell_range[1])
    else:
        ret.extend([0 for i in range(28)])
    return ret

def deal_enemy_be_lbss(curp, enemyp):
    if int(enemyp['baseinfo']['isdead']) == 1:
        return 0
    
    curcards = getHandCardlist(curp)
    cureqcards = getEquipCardlist(curp)
    can_not_yanshijingnang = 283
    enemypskill = getPlayerSkillList(enemyp)
    if can_not_yanshijingnang in enemypskill:
        return 0

    have_lbss = 0
    lbss_skill_1 = 60
    lbss_skill_2 = 714
    if getCardNumBySpell(curcards, 15) <= 0:#如果有乐不思蜀的牌
        #60 国色 你可以将一张方块牌当【乐不思蜀】使
        #714 国色 将一张方块牌当【乐不思蜀】使用
        curpskill = getPlayerSkillList(curp)
        if lbss_skill_1 in curpskill or lbss_skill_2 in curpskill:
            have_lbss = 1 if int(getCardNumSuitList(curcards)[1]) + int(getCardNumSuitList(cureqcards)[1]) > 0 else 0
    else:
        have_lbss = 1

    if have_lbss == 0:
        return 0
    
    ### 判断目标能不能被乐
    # 58 谦逊 你不能成为【顺手牵羊】和【乐不思蜀】的目标
    # 649 机关 你不能成为【乐不思蜀】的目标。
    can_not_lbss_skill_1 = 58
    can_not_lbss_skill_2 = 649
    can_not_lbss_skill_3 = 822
    if can_not_lbss_skill_1 in enemypskill or can_not_lbss_skill_2 in enemypskill or can_not_lbss_skill_3 in enemypskill:
        return 0

    # 检查目标是否全被乐
    if getJudgeSpellForLbss(enemyp['judgeinfo']) == 1:
        return 0

    return 1

## 兵粮寸断 出牌阶段，对距离为1的一名其他角色使用
def deal_enemy_be_blcd(curp, enemyp, emcnum, enemy_distance):
    if int(enemyp['baseinfo']['isdead']) == 1:
        return 0
    
    hcards = getHandCardlist(curp)
    ecards = getEquipCardlist(curp)

    can_not_skill_weimu = 119
    can_not_skill_weimu_484 = 3189
    can_not_yanshijingnang_1 = 283
    can_not_yanshijingnang_2 = 822
    
    enemypskill = getPlayerSkillList(enemyp)
    if can_not_skill_weimu in enemypskill or can_not_skill_weimu_484 in enemypskill or can_not_yanshijingnang_1 in enemypskill or can_not_yanshijingnang_2 in enemypskill:
        return 0

    #你不能成为黑色锦囊牌的目标
    have_blcd = 0
    blcd_skill_1 = 104
    blcd_skill_2 = 380
    blcd_skill_3 = 3079
    curpskill = getPlayerSkillList(curp)
    if getCardNumBySpell(hcards, 84) <= 0:#如果有兵粮寸断的牌
        #104 断粮 一张黑色基本牌或黑色装备牌当【兵粮寸断】使用 你可以对距离为2的角色使用【兵粮寸断】
        #380 断粮 一张黑色基本牌或黑色装备牌当【兵粮寸断】使用。你对手牌数不小于你的角色使用【兵粮寸断】无距离限制
        #3079  断粮 可以将一张黑色基本牌或黑色装备牌当【兵粮寸断】使用。若你本回合未造成过伤害，你使用【兵粮寸断】无距离限制。
        if blcd_skill_1 in curpskill or blcd_skill_2 in curpskill or blcd_skill_3 in curpskill:
           have_blcd == 1 if getCardNumColorList(hcards)[1] + getCardNumColorList(ecards)[1] > 0 else 0
    else:
        have_blcd = 1

    if have_blcd == 0:
        return 0
    
    # 检查目标是否全被兵
    if getJudgeSpellForBlcd(enemyp.get('judgeinfo', {})) == 1:
        return 0
    
    # 距离判断
    if enemy_distance <= 1:
        return 1
    else:
        if blcd_skill_1 in curpskill and enemy_distance == 2:
            return 1
        elif blcd_skill_2 in curpskill and len(hcards) >= emcnum:
            return 1
        ## 先注释了 需要状态判断
        # elif blcd_skill_3 in curpskill:
        #     return 1
    return 0

## 判断是否目标是否可以被杀
def deal_enemy_be_sha(curp, enemyp, emcnum, enemy_distance_attr):
    if int(enemyp['baseinfo']['isdead']) == 1:
        return 0
    cur_can_sha = getStatusCanSha(curp, curp['skillinfo'])
    if cur_can_sha == 0:
        return 0
    
    #
    hcards = getHandCardlist(curp)
    ecards = getEquipCardlist(curp)
    
    curpskill = getPlayerSkillList(curp)
    curespell = getEquisSpell(ecards)
    ##
    curskill_longdan_1 = 37
    curskill_longdan_2 = 940
    curskill_wusheng_1 = 33
    curskill_wusheng_2 = 878
    curskill_wuhun_1 = 473
    find_sha = 0
    if getCardNumBySpell(hcards, 1) <= 0:
        ##龙胆 闪当杀
        if ((curskill_longdan_1 in curpskill) or (curskill_longdan_2 in curpskill)) and (getCardNumBySpell(hcards, 2) > 0):
            find_sha = 1
        ##武圣 红牌当杀
        elif ((curskill_wusheng_1 in curpskill) or (curskill_wusheng_2 in curpskill)) and (getCardNumColorList(hcards)[0] + getCardNumColorList(ecards)[0] > 0):
            find_sha = 1
        ##473 两张手牌当【杀】使用或打出
        elif (curskill_wuhun_1 in curpskill) and len(hcards) >= 2:
            find_sha = 1
        ## 丈八蛇矛 两张手牌当【杀】使用或打出
        elif int(curespell[0]) == 27 and len(hcards) >= 2:
            find_sha = 1
    else:
        find_sha = 1
        ##其他情况待补充
    if  find_sha == 0:
        return 0
    
    ### 有杀的情况 超出攻击范围
    if enemy_distance_attr == 0:
        return 0
    
    epskill = getPlayerSkillList(enemyp)

    ##空车给
    skil_kongcheng_1 = 36
    ## 不能成为杀的目标
    if skil_kongcheng_1 in epskill and emcnum == 0:
        return 0
    return 1

## 判断是否目标是否可以被杀
def deal_enemy_be_juedou(curp, enemyp, emcnum):
    if int(enemyp['baseinfo']['isdead']) == 1:
        return 0
    ##
    find_joudou = getCardNumBySpell(getHandCardlist(curp), 8)

    if find_joudou <= 0:
        return 0
    epskill = getPlayerSkillList(enemyp)
    ##空车
    skil_kongcheng_1 = 36
    ## 不能成为决斗的目标
    if skil_kongcheng_1 in epskill and emcnum == 0:
        return 0
    return 1

def getall_card_num(player):
    handcards = getHandCardlist(player)
    equipscard = getEquipCardlist(player)
    judgecard = getJudgeCardlist(player['judgeinfo'])
    return len(handcards) + len(equipscard) + len(judgecard)


def deal_enemy_be_ghcq(curp, enemyp):
    curcards = getHandCardlist(curp)
    have_ghcq = 0
    if getCardNumBySpell(curcards, 5) <= 0:  # 如果有乐不思蜀的牌
        if 57 in getPlayerSkillList(curp):
            have_ghcq = 1 if int(getCardNumColorList(curcards)[1]) > 0 else 0
        else:
            have_ghcq = 0
    else:
        have_ghcq = 1

    if have_ghcq == 0:
        return 0
    if enemyp['baseinfo']['isdead'] == '1':
        return 0
    ### 判断目标能不能被过拆
    # 119 帷幕 锁定技，你不能成为黑色锦囊牌的目标
    if 119 in getPlayerSkillList(enemyp):
        return 0
    if 3189 in getPlayerSkillList(enemyp):
        return 0
    # if 9021 in getPlayerSkillList(enemyp):
    #     return 0
    # if 2117 in getPlayerSkillList(enemyp):
    #     return 0
    ### 目标没有牌可以拆

    if getall_card_num(enemyp) == 0:
        return 0

    return 1

def deal_enemy_be_ssqy(curp, enemyp, inrange_attr_no_equis):
    
    curcards = getHandCardlist(curp)
    if inrange_attr_no_equis[0] == 0:
        return 0
    
    have_ssqy = 1 if getCardNumBySpell(curcards, 4) > 0 else 0  # 如果有乐不思蜀的牌

    if have_ssqy == 0:
        return 0
    if enemyp['baseinfo']['isdead'] == '1':
        return 0
    ### 判断目标能不能被乐
    enemypskill = getPlayerSkillList(enemyp)
    # 58 谦逊 你不能成为【顺手牵羊】和【乐不思蜀】的目标
    if 58 in enemypskill:
        return 0
    # 119 帷幕 锁定技，你不能成为黑色锦囊牌的目标
    if 119 in getPlayerSkillList(enemyp) and getCardNumBySpellAndColor(curcards,4,[3,4]) == getCardNumBySpell(curcards, 4):
        return 0
    if 3189 in getPlayerSkillList(enemyp) and getCardNumBySpellAndColor(curcards,4,[3,4]) == getCardNumBySpell(curcards, 4):
        return 0
    # if 9021 in getPlayerSkillList(enemyp) and getCardNumBySpellAndColor(curcards,4,[3,4]) == getCardNumBySpell(curcards, 4):
    #     return 0
    # if 2117 in getPlayerSkillList(enemyp) and getCardNumBySpellAndColor(curcards,4,[3,4]) == getCardNumBySpell(curcards, 4):
    #     return 0
    ### 目标没有牌可以顺
    if getall_card_num(enemyp) == 0:
        return 0

    return 1

def deal_can_jdsr(curcards, curp, frip, nextp, otherp, own_alive_number, enemy_alive_number):
    have_jdsr = 1
    flag = 0
    if getCardNumBySpell(curcards, 14) <= 0:
        return 0
    for player in [frip,nextp,otherp]:
        if flag == 1:
            break
        if player['baseinfo']['isdead'] == '1':
            have_jdsr = 0
            continue
        if 119 in getPlayerSkillList(player) and getCardNumBySpellAndColor(curcards, 14, [3, 4]) == getCardNumBySpell(
                curcards, 4):
            have_jdsr = 0
            continue
        if 3189 in getPlayerSkillList(player) and getCardNumBySpellAndColor(curcards, 14, [3, 4]) == getCardNumBySpell(
                curcards, 4):
            have_jdsr = 0
            continue
        equipscard = getEquipCardlist(player)
        equipsspell = getEquisSpell(equipscard)
        if equipsspell[0] > 0:
            for be_attacked_player in [curp,frip,nextp,otherp]:
                if be_attacked_player['baseinfo']['charid'] == player['baseinfo']['charid']:
                    continue
                if be_attacked_player['baseinfo']['isdead'] == '1':
                    have_jdsr = 0
                    continue
                if 119 in getPlayerSkillList(be_attacked_player) and getCardNumBySpellAndColor(curcards, 14,
                                                                                   [3, 4]) == getCardNumBySpell(
                        curcards, 4):
                    have_jdsr = 0
                    continue
                if 3189 in getPlayerSkillList(be_attacked_player) and getCardNumBySpellAndColor(curcards, 14,
                                                                                    [3, 4]) == getCardNumBySpell(
                        curcards, 4):
                    have_jdsr = 0
                    continue
                equipcards = getEquipCardlist(player)
                equipspell = getEquisSpell(equipcards)
                target_equips_cards = getEquipCardlist(be_attacked_player)
                target_equipMark = getEquisMark(target_equips_cards)
                if get_target_within_range_attack(player, be_attacked_player, own_alive_number,
                                               enemy_alive_number, equipspell, target_equipMark)[0] == 1:
                    have_jdsr = 1
                    flag = 1
                    break
                else:
                    have_jdsr = 0
        else:
            have_jdsr = 0
    if have_jdsr == 1:
        return 1
    else:
        return 0
    
def deal_can_use_lijian(cplay,fplay,nplay,oplay):
    used_lijian = 0
    for item in cplay['skillinfo']:
        if int(item['skillid']) == 68:
            used_lijian = 1 if int(item['datas']) == 1 else 0

    #判断回合内是否已经被使用了
    if used_lijian == 1:
        return 0#已被使用
    
    #判断是否满足使用的条件
    chands = getHandCardlist(cplay)
    cequis = getEquipCardlist(cplay)
    if len(chands) + len(cequis) == 0:
        return 0

    ##判断是否满足有两个异性的情况
    diff_sex_num = 0
    if int(fplay['baseinfo']['isdead']) == 0 and getGenerById(int(fplay['baseinfo']['charid'])) == 1:
        diff_sex_num += 1
    if int(nplay['baseinfo']['isdead']) == 0 and getGenerById(int(nplay['baseinfo']['charid'])) == 1:
        diff_sex_num += 1   
    if int(oplay['baseinfo']['isdead']) == 0 and getGenerById(int(oplay['baseinfo']['charid'])) == 1:
        diff_sex_num += 1   

    return 1 if diff_sex_num >= 2 else 0

    
def get_21214_24_diaocan_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    ##fri
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    nextplayer = getPlayerInfoBySeat(jdata, getNextSeat(curseat))
    otherplayer = getPlayerInfoBySeat(jdata, getOtherSeat(curseat))

    ##
    inputdata = []
    emery_alive_num = 0
    if nextplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    if otherplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    ##emery_inrange_attr
    own_alive_number = 2 if friplayer['baseinfo']['isdead'] == '0' else 1

    alive = 1
    if friplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if nextplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if otherplayer['baseinfo']['isdead'] != '1':
        alive += 1
    inputdata.append(alive)
    inputdata.append(emery_alive_num)
    inputdata.append(own_alive_number)
    ##'team_can_change',
    inputdata.append(getFeature_can_change(curplayer, friplayer))
    ##'emery_can_change',
    inputdata.append(getFeature_can_change(nextplayer, otherplayer))
    # phase_id
    inputdata.append(getTablePhase(jdata, curseat))
    if len(curplayer) == 0:
        print("_21214_choose_action error")

    ## 武将基础信息
    inputdata.extend(getPlayerInfoWay2(curplayer, curseat))
    ##
    curhandcards = getHandCardlist(curplayer)
    inputdata.extend(getHandCardSpellCount(curhandcards))
    inputdata.extend(getCardNumSuitList(curhandcards))
    ##
    ##equip spell
    curequiscards = getEquipCardlist(curplayer)
    equisspell = getEquisSpell(curequiscards)
    inputdata.extend(equisspell)
    ## curstate_jiu
    inputdata.append(getStatusJiu(curplayer['skillinfo']))
    #是否已有闪电
    inputdata.append(getJudgeSpellForFlash(friplayer['judgeinfo']))
    ##curstate_tslh
    inputdata.append(getStatusTslh(curplayer['statusinfo']))
    #'have_use_sha',
    inputdata.append(getStatusHaveUseSha(curplayer['skillinfo']))
    ## cur_can_sha
    inputdata.append(getStatusCanSha(curplayer, curplayer['skillinfo']))
    ## need_give_up
    inputdata.append(getNeedGiveupCard(curplayer))
    ##'can_use_tao_jiu',
    inputdata.append(1 if getCardNumBySpell(curhandcards, 3) + getCardNumBySpell(curhandcards, 82) > 0 else 0)
    ##fri
    ##'friplayer',
    inputdata.extend(get_action_FriplayerbaseInfo(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equisspell))
    ##nextplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, nextplayer, own_alive_number, emery_alive_num, equisspell))
    ##otherplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, otherplayer, own_alive_number, emery_alive_num, equisspell))
    ##can_jdsr
    inputdata.append(deal_can_jdsr(curhandcards, curplayer, friplayer, nextplayer, otherplayer, own_alive_number, emery_alive_num))
    ##can_use_lijia
    inputdata.append(deal_can_use_lijian(curplayer, friplayer, nextplayer, otherplayer))
    # action_idx
    inputdata.append(getAcionIdxLabel(jdata['Labelinfo']))
    ##
    return inputdata


def get_21214_29_caoren_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    ##fri
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    nextplayer = getPlayerInfoBySeat(jdata, getNextSeat(curseat))
    otherplayer = getPlayerInfoBySeat(jdata, getOtherSeat(curseat))

    ##
    inputdata = []
    emery_alive_num = 0
    if nextplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    if otherplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    ##emery_inrange_attr
    own_alive_number = 2 if friplayer['baseinfo']['isdead'] == '0' else 1

    alive = 1
    if friplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if nextplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if otherplayer['baseinfo']['isdead'] != '1':
        alive += 1
    inputdata.append(alive)
    inputdata.append(emery_alive_num)
    inputdata.append(own_alive_number)
    ##'team_can_change',
    inputdata.append(getFeature_can_change(curplayer, friplayer))
    ##'emery_can_change',
    inputdata.append(getFeature_can_change(nextplayer, otherplayer))
    # phase_id
    inputdata.append(getTablePhase(jdata, curseat))
    if len(curplayer) == 0:
        print("_21214_choose_action error")

    ## 武将基础信息
    inputdata.extend(getPlayerInfoWay2(curplayer, curseat))
    ##
    curhandcards = getHandCardlist(curplayer)
    inputdata.extend(getHandCardSpellCount(curhandcards))
    inputdata.extend(getCardNumSuitList(curhandcards))
    ##
    ##equip spell
    curequiscards = getEquipCardlist(curplayer)
    equisspell = getEquisSpell(curequiscards)
    inputdata.extend(equisspell)
    ## curstate_jiu
    inputdata.append(getStatusJiu(curplayer['skillinfo']))
    #是否已有闪电
    inputdata.append(getJudgeSpellForFlash(friplayer['judgeinfo']))
    ##curstate_tslh
    inputdata.append(getStatusTslh(curplayer['statusinfo']))
    #'have_use_sha',
    inputdata.append(getStatusHaveUseSha(curplayer['skillinfo']))
    ## cur_can_sha
    inputdata.append(getStatusCanSha(curplayer, curplayer['skillinfo']))
    ## need_give_up
    inputdata.append(getNeedGiveupCard(curplayer))
    ##'can_use_tao_jiu',
    inputdata.append(getCardNumBySpell(curhandcards, 3) + getCardNumBySpell(curhandcards, 82)) 
    ##fri
    ##'friplayer',
    inputdata.extend(get_action_FriplayerbaseInfo(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equisspell))
    ##nextplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, nextplayer, own_alive_number, emery_alive_num, equisspell))
    ##otherplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, otherplayer, own_alive_number, emery_alive_num, equisspell))
    ##can_jdsr
    inputdata.append(deal_can_jdsr(curhandcards, curplayer, friplayer, nextplayer, otherplayer, own_alive_number, emery_alive_num))
    # action_idx
    inputdata.append(getAcionIdxLabel(jdata['Labelinfo']))
    ##
    return inputdata

def get_21214_weiyan_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    ##fri
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    nextplayer = getPlayerInfoBySeat(jdata, getNextSeat(curseat))
    otherplayer = getPlayerInfoBySeat(jdata, getOtherSeat(curseat))

    ##
    inputdata = []
    emery_alive_num = 0
    if nextplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    if otherplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    ##emery_inrange_attr
    own_alive_number = 2 if friplayer['baseinfo']['isdead'] == '0' else 1

    alive = 1
    if friplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if nextplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if otherplayer['baseinfo']['isdead'] != '1':
        alive += 1
    inputdata.append(alive)
    inputdata.append(emery_alive_num)
    inputdata.append(own_alive_number)
    ##'team_can_change',
    inputdata.append(getFeature_can_change(curplayer, friplayer))
    ##'emery_can_change',
    inputdata.append(getFeature_can_change(nextplayer, otherplayer))

    # phase_id
    inputdata.append(getTablePhase(jdata, curseat))
    if len(curplayer) == 0:
        print("_21214_choose_action error")

    ## 武将基础信息
    inputdata.extend(getPlayerInfoWay2(curplayer, curseat))
    ##
    curhandcards = getHandCardlist(curplayer)
    inputdata.extend(getHandCardSpellCount(curhandcards))
    inputdata.extend(getCardNumSuitList(curhandcards))
    ##
    ##equip spell
    curequiscards = getEquipCardlist(curplayer)
    equisspell = getEquisSpell(curequiscards)
    inputdata.extend(equisspell)
    ## curstate_jiu
    inputdata.append(getStatusJiu(curplayer['skillinfo']))
    #是否已有闪电
    inputdata.append(getJudgeSpellForFlash(friplayer['judgeinfo']))
    ##curstate_tslh
    inputdata.append(getStatusTslh(curplayer['statusinfo']))
    #'have_use_sha',
    inputdata.append(getStatusHaveUseSha(curplayer['skillinfo']))
    ## cur_can_sha
    inputdata.append(getStatusCanSha(curplayer, curplayer['skillinfo']))
    ## need_give_up
    inputdata.append(getNeedGiveupCard(curplayer))
    ##'can_use_tao_jiu',
    inputdata.append(getCardNumBySpell(curhandcards, 3) + getCardNumBySpell(curhandcards, 82)) 
    ##fri
    ##'friplayer',
    inputdata.extend(get_action_FriplayerbaseInfo(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equisspell))
    ##nextplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, nextplayer, own_alive_number, emery_alive_num, equisspell))
    ## nextinkuangg
    inputdata.append(1 if inputdata[-1] <= 1 else 0)
    ##otherplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, otherplayer, own_alive_number, emery_alive_num, equisspell))
    ## nextinkuangg
    inputdata.append(1 if inputdata[-1] <= 1 else 0)
    ##can_jdsr
    inputdata.append(deal_can_jdsr(curhandcards, curplayer, friplayer, nextplayer, otherplayer, own_alive_number, emery_alive_num))
    # action_idx
    inputdata.append(getAcionIdxLabel(jdata['Labelinfo']))
    ##
    return inputdata

def get_21214_weiyan_param_inputdata(jdata, curseat):
    inputdata = get_21214_weiyan_inputdata(jdata, curseat)
    inputdata.append(int(jdata['Labelinfo'][0]['useSpell']['user_param0'])) 
    return inputdata

def friplayer_feather_for_activete_base(curplayer, friplayer,cur_seat,equipspell,own_alive_number,enemy_alive_number):
    result = []
    result.extend(getPlayerInfoWay1(friplayer, cur_seat, True))
    #fricardnum
    fricardnum = 0
    frihandcards = getHandCardlist(friplayer)
    fricardnum = len(frihandcards)
    result.append(fricardnum)
    #frinum_total_sha,frinum_shan,frinum_tao,frinum_wxkj,frinum_jiu
    result.append(getCardNumBySpell(frihandcards, 1))
    result.append(getCardNumBySpell(frihandcards, 2))
    result.append(getCardNumBySpell(frihandcards, 3))
    result.append(getCardNumBySpell(frihandcards, 13))
    result.append(getCardNumBySpell(frihandcards, 82))
    # friarms_spell,friequis_spell, friadd1_spell, frireduce1_spell, friextar_spell
    friequipscard = getEquipCardlist(friplayer)
    friequipsspell = getEquisSpell(friequipscard)
    result.extend(friequipsspell)
    # frijudge_lbss,frijudge_blcd,frijudge_flash
    result.extend(getJudgeSpell(friplayer['judgeinfo']))
    # fristate_tslh
    result.append(getStatusTslh(friplayer['statusinfo']))
    friequipMark = getEquisMark(friequipscard)
    fri_inrange_attr = get_target_within_range_attack(curplayer, friplayer, own_alive_number, enemy_alive_number,
                                                      equipspell, friequipMark)
    result.append(fri_inrange_attr[0])

    noequipspell = copy.deepcopy(equipspell)
    noequipspell[0] = 0
    fri_inrange_attr_no_equis = get_target_within_range_attack(curplayer, friplayer, own_alive_number,
                                                           enemy_alive_number, noequipspell, friequipMark)
    result.append(fri_inrange_attr_no_equis[0])

def deal_liubei_activate_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    ##fri
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    nextplayer = getPlayerInfoBySeat(jdata, getNextSeat(curseat))
    otherplayer = getPlayerInfoBySeat(jdata, getOtherSeat(curseat))

    ##
    inputdata = []
    emery_alive_num = 0
    if nextplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    if otherplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    ##emery_inrange_attr
    own_alive_number = 2 if friplayer['baseinfo']['isdead'] == '0' else 1

    alive = 1
    if friplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if nextplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if otherplayer['baseinfo']['isdead'] != '1':
        alive += 1
    inputdata.append(alive)
    inputdata.append(emery_alive_num)
    inputdata.append(own_alive_number)
    ##'team_can_change',
    inputdata.append(getFeature_can_change(curplayer, friplayer))
    ##'emery_can_change',
    inputdata.append(getFeature_can_change(nextplayer, otherplayer))

    # phase_id
    inputdata.append(getTablePhase(jdata, curseat))
    if len(curplayer) == 0:
        print("_21214_choose_action error")

    ## 武将基础信息
    inputdata.extend(getPlayerInfoWay2(curplayer, curseat))
    ##
    curhandcards = getHandCardlist(curplayer)
    inputdata.extend(getHandCardSpellCount(curhandcards))
    inputdata.extend(getCardNumSuitList(curhandcards))
    ##
    ##equip spell
    curequiscards = getEquipCardlist(curplayer)
    equisspell = getEquisSpell(curequiscards)
    inputdata.extend(equisspell)
    ## curstate_jiu
    inputdata.append(getStatusJiu(curplayer['skillinfo']))
    #是否已有闪电
    inputdata.append(getJudgeSpellForFlash(curplayer['judgeinfo']))
    ##curstate_tslh
    inputdata.append(getStatusTslh(curplayer['statusinfo']))
    #'have_use_sha',
    inputdata.append(getStatusHaveUseSha(curplayer['skillinfo']))
    ## cur_can_sha
    inputdata.append(getStatusCanSha(curplayer, curplayer['skillinfo']))
    ## need_give_up
    inputdata.append(getNeedGiveupCard(curplayer))
    ##'can_use_tao_jiu',
    can_use_tao_jiu = 1 if getCardNumBySpell(curhandcards, 3) + getCardNumBySpell(curhandcards, 82) >0 else 0
    inputdata.append(getCardNumBySpell(curhandcards, 3) + getCardNumBySpell(curhandcards, 82))
    ##fri
    ##'friplayer',
    inputdata.extend(get_action_FriplayerbaseInfo(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equisspell))
    ##nextplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, nextplayer, own_alive_number, emery_alive_num, equisspell))
    ##otherplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, otherplayer, own_alive_number, emery_alive_num, equisspell))
    #can_jdsr
    inputdata.append(deal_can_jdsr(curhandcards,curplayer,friplayer,nextplayer,otherplayer,own_alive_number,emery_alive_num))
    # action_idx
    inputdata.append(getAcionIdxLabel(jdata['Labelinfo']))
    ##error
    if getAcionIdxLabel(jdata['Labelinfo']) in [14,22,38] and (getFeature_hs_rwd(jdata) or getFeature_norsha_tj(jdata,curseat)):
        inputdata.append(1)
    else:
        inputdata.append(0)
    return inputdata

def rende_choose_cardnum_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    input = []
    ## 武将基础信息
    input.extend(getPlayerInfoWay2(curplayer, curseat))
    curequiscards = getEquipCardlist(curplayer)
    input.extend(getEquisSpell(curequiscards))
    ## curplayer手牌
    curhandcards = getHandCardlist(curplayer)
    input.extend(getCardSpellNumberColor(curhandcards))
    ##fri武将基础信息
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    input.extend(getPlayerInfoWay2(friplayer, curseat))
    friequiscards = getEquipCardlist(friplayer)
    input.extend(getEquisSpell(friequiscards))
    label = len(jdata['Labelinfo'][0]['useSpell']['datas'].split(';')) - 1
    input.append(label)
    return input

def zhiheng_choose_cardnum_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    input = []
    ## 武将基础信息
    input.extend(getPlayerInfoWay2(curplayer, curseat))
    curequiscards = getEquipCardlist(curplayer)
    input.extend(getEquisSpell(curequiscards))
    ## curplayer手牌
    curhandcards = getHandCardlist(curplayer)
    input.extend(getCardSpellNumberColor(curhandcards))
    label = len(jdata['Labelinfo'][0]['useSpell']['datas'].split(';')) - 1
    input.append(label)
    return input

def deal_sunquan_activate_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    ##fri
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    nextplayer = getPlayerInfoBySeat(jdata, getNextSeat(curseat))
    otherplayer = getPlayerInfoBySeat(jdata, getOtherSeat(curseat))

    ##
    inputdata = []
    emery_alive_num = 0
    if nextplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    if otherplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    ##emery_inrange_attr
    own_alive_number = 2 if friplayer['baseinfo']['isdead'] == '0' else 1

    alive = 1
    if friplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if nextplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if otherplayer['baseinfo']['isdead'] != '1':
        alive += 1
    inputdata.append(alive)
    inputdata.append(emery_alive_num)
    inputdata.append(own_alive_number)
    ##'team_can_change',
    inputdata.append(getFeature_can_change(curplayer, friplayer))
    ##'emery_can_change',
    inputdata.append(getFeature_can_change(nextplayer, otherplayer))

    # phase_id
    inputdata.append(getTablePhase(jdata, curseat))
    if len(curplayer) == 0:
        print("_21214_choose_action error")

    ## 武将基础信息
    inputdata.extend(getPlayerInfoWay2(curplayer, curseat))
    ##
    curhandcards = getHandCardlist(curplayer)
    inputdata.extend(getHandCardSpellCount(curhandcards))
    inputdata.extend(getCardNumSuitList(curhandcards))
    ##
    ##equip spell
    curequiscards = getEquipCardlist(curplayer)
    equisspell = getEquisSpell(curequiscards)
    inputdata.extend(equisspell)
    ## curstate_jiu
    inputdata.append(getStatusJiu(curplayer['skillinfo']))
    #是否已有闪电
    inputdata.append(getJudgeSpellForFlash(friplayer['judgeinfo']))
    ##curstate_tslh
    inputdata.append(getStatusTslh(curplayer['statusinfo']))
    #'have_use_sha',
    inputdata.append(getStatusHaveUseSha(curplayer['skillinfo']))
    ## cur_can_sha
    inputdata.append(getStatusCanSha(curplayer, curplayer['skillinfo']))
    ## need_give_up
    inputdata.append(getNeedGiveupCard(curplayer))
    ##'can_use_tao_jiu',
    # can_use_tao_jiu = 1 if getCardNumBySpell(curhandcards, 3) + getCardNumBySpell(curhandcards, 82) >0 else 0
    inputdata.append(getCanUseTaoJiu(curhandcards))
    ##fri
    ##'friplayer',
    inputdata.extend(get_action_FriplayerbaseInfo(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equisspell))
    ##nextplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, nextplayer, own_alive_number, emery_alive_num, equisspell))
    ##otherplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, otherplayer, own_alive_number, emery_alive_num, equisspell))
    #can_jdsr
    inputdata.append(deal_can_jdsr(curhandcards,curplayer,friplayer,nextplayer,otherplayer,own_alive_number,emery_alive_num))
    # action_idx
    inputdata.append(getAcionIdxLabel(jdata['Labelinfo']))
    ##
    if getAcionIdxLabel(jdata['Labelinfo']) in [14,22,38] and (getFeature_hs_rwd(jdata) or getFeature_norsha_tj(jdata,curseat)):
        inputdata.append(1)
    else:
        inputdata.append(0)
    # can_use_zhiheng
    skill_lst = []
    for item in curplayer['skillinfo']:
        skill_lst.append(item['skillid'])

    can_use_zhiheng = 0
    hand_cards = [int(ii) for ii in  curplayer['handinfo']['cards'].split(';')] if 'cards' in curplayer['handinfo'] else []
    equip_cards = [int(ii) for ii in  curplayer['equipinfo']['cards'].split(';')] if 'cards' in curplayer['equipinfo'] else []
    if len(hand_cards) == 0 and equip_cards == 0:
        can_use_zhiheng =  0
    else:
        for item in curplayer['skillinfo']:
            if item['skillid'] == '53' and item['datas'] == '0':
                can_use_zhiheng =  1
    if '53' not in skill_lst:
        can_use_zhiheng =  1
    inputdata.append(can_use_zhiheng)

    return inputdata

def huatuo_activate_data(jdata, curseat):
    inputdata = deal_base_activate_inputdata(jdata,curseat)
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    ##fri
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    nextplayer = getPlayerInfoBySeat(jdata, getNextSeat(curseat))
    otherplayer = getPlayerInfoBySeat(jdata, getOtherSeat(curseat))
    curhandcards = getHandCardlist(curplayer)
    skill_lst = []
    for item in curplayer['skillinfo']:
        skill_lst.append(item['skillid'])
    # can_use_qingnang
    can_use_qingnang = 0
    skill_lst = []
    for item in curplayer['skillinfo']:
        skill_lst.append(item['skillid'])
    for item in curplayer['skillinfo']:
        if item['skillid'] == '65' and item['datas'] == '0':
            can_use_qingnang = 1
    if '65' not in skill_lst and len(curhandcards) > 0 and (int(friplayer['baseinfo']['maxhp']) > int(friplayer['baseinfo']['curhp']) or int(curplayer['baseinfo']['maxhp']) > int(curplayer['baseinfo']['curhp'])):
        can_use_qingnang = 1
    inputdata.append(can_use_qingnang)
    return inputdata

def ganning_activate_data(jdata, curseat):
    inputdata = deal_base_activate_inputdata(jdata, curseat)
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    curhandcards = getHandCardlist(curplayer)
    curequiscards = getEquipCardlist(curplayer)
    have_black_card = 0
    cur_hand_card_color = getCardNumSuitList(curhandcards)
    if cur_hand_card_color[0] + cur_hand_card_color[1] > 0:
        have_black_card = 1
    equip_card_color = getCardNumSuitList(curequiscards)
    if equip_card_color[0] + equip_card_color[1] > 0:
        have_black_card = equip_card_color[0]
    inputdata.append(have_black_card)
    return inputdata

def daqiao_activate_data(jdata, curseat):
    inputdata = deal_base_activate_inputdata(jdata, curseat)
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    curhandcards = getHandCardlist(curplayer)
    curequiscards = getEquipCardlist(curplayer)
    #have_fangkuai_card
    have_fangkuai_card = 0
    cur_hand_card_color = getCardNumSuitList(curhandcards)
    if cur_hand_card_color[1] > 0:
        have_fangkuai_card = 1
    equip_card_color = getCardNumSuitList(curequiscards)
    if equip_card_color[1] > 0:
        have_fangkuai_card = 1
    inputdata.append(have_fangkuai_card)
    #can_guose
    can_guose = 0
    next_be_lbss = inputdata[133]
    other_be_lbss =  inputdata[158]
    if next_be_lbss == 1 or other_be_lbss == 1:
        can_guose = 1
    inputdata.append(can_guose)
    return inputdata

def xiaoqiao_activate_data(jdata, curseat):
    inputdata = deal_base_activate_inputdata(jdata, curseat)
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    curhandcards = getHandCardlist(curplayer)
    cur_hand_card_color = getCardNumSuitList(curhandcards)
    tianxiang_card_num = cur_hand_card_color[0] + cur_hand_card_color[2]
    inputdata.append(tianxiang_card_num)
    return inputdata

def zhangjiao_activate_data(jdata, curseat):
    inputdata = deal_base_activate_inputdata(jdata, curseat)
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    curhandcards = getHandCardlist(curplayer)
    curequiscards = getEquipCardlist(curplayer)
    cur_hand_card_color = getCardNumSuitList(curhandcards)
    equip_card_color = getCardNumSuitList(curequiscards)
    black_card_num = cur_hand_card_color[2] + cur_hand_card_color[3] + equip_card_color[2] + equip_card_color[3]
    inputdata.append(black_card_num)
    return inputdata

def sunshangxiang_activate_data(jdata, curseat):
    inputdata = deal_base_activate_inputdata(jdata, curseat)
    #can_use_jieyin
    can_use_jieyin = 0
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    curhandcards_num = len(getHandCardlist(curplayer))
    curequiscards_num = len(getEquipCardlist(curplayer))
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    if getIsOpposite_sex(curplayer['baseinfo']['charid'], friplayer['baseinfo']['charid']) and curhandcards_num + curequiscards_num >= 2:
        can_use_jieyin = 1
    inputdata.append(can_use_jieyin)
    return inputdata

def deal_base_activate_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    ##fri
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    nextplayer = getPlayerInfoBySeat(jdata, getNextSeat(curseat))
    otherplayer = getPlayerInfoBySeat(jdata, getOtherSeat(curseat))

    ##
    inputdata = []
    emery_alive_num = 0
    if nextplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    if otherplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    ##emery_inrange_attr
    own_alive_number = 2 if friplayer['baseinfo']['isdead'] == '0' else 1

    alive = 1
    if friplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if nextplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if otherplayer['baseinfo']['isdead'] != '1':
        alive += 1
    inputdata.append(alive)
    inputdata.append(emery_alive_num)
    inputdata.append(own_alive_number)
    ##'team_can_change',
    inputdata.append(getFeature_can_change(curplayer, friplayer))
    ##'emery_can_change',
    inputdata.append(getFeature_can_change(nextplayer, otherplayer))

    # phase_id
    inputdata.append(getTablePhase(jdata, curseat))
    if len(curplayer) == 0:
        print("_21214_choose_action error")

    ## 武将基础信息
    inputdata.extend(getPlayerInfoWay2(curplayer, curseat))
    ##
    curhandcards = getHandCardlist(curplayer)
    inputdata.extend(getHandCardSpellCount(curhandcards))
    inputdata.extend(getCardNumSuitList(curhandcards))
    ##
    ##equip spell
    curequiscards = getEquipCardlist(curplayer)
    equisspell = getEquisSpell(curequiscards)
    inputdata.extend(equisspell)
    ## curstate_jiu
    inputdata.append(getStatusJiu(curplayer['skillinfo']))
    #是否已有闪电
    inputdata.append(getJudgeSpellForFlash(friplayer['judgeinfo']))
    ##curstate_tslh
    inputdata.append(getStatusTslh(curplayer['statusinfo']))
    #'have_use_sha',
    inputdata.append(getStatusHaveUseSha(curplayer['skillinfo']))
    ## cur_can_sha
    inputdata.append(getStatusCanSha(curplayer, curplayer['skillinfo']))
    ## need_give_up
    inputdata.append(getNeedGiveupCard(curplayer))
    ##'can_use_tao_jiu',
    # can_use_tao_jiu = 1 if getCardNumBySpell(curhandcards, 3) + getCardNumBySpell(curhandcards, 82) >0 else 0
    inputdata.append(getCanUseTaoJiu(curhandcards))
    ##fri
    ##'friplayer',
    inputdata.extend(get_action_FriplayerbaseInfo(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equisspell))
    ##nextplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, nextplayer, own_alive_number, emery_alive_num, equisspell))
    ##otherplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, otherplayer, own_alive_number, emery_alive_num, equisspell))
    #can_jdsr
    inputdata.append(deal_can_jdsr(curhandcards,curplayer,friplayer,nextplayer,otherplayer,own_alive_number,emery_alive_num))
    # action_idx
    inputdata.append(getAcionIdxLabel(jdata['Labelinfo']))
    ##
    # if getAcionIdxLabel(jdata['Labelinfo']) in [14,22,38] and (getFeature_hs_rwd(jdata) or getFeature_norsha_tj(jdata,curseat)):
    #     inputdata.append(1)
    # else:
    #     inputdata.append(0)
    return inputdata

def deal_huanggai_activate_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    ##fri
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    nextplayer = getPlayerInfoBySeat(jdata, getNextSeat(curseat))
    otherplayer = getPlayerInfoBySeat(jdata, getOtherSeat(curseat))

    ##
    inputdata = []
    emery_alive_num = 0
    if nextplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    if otherplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    ##emery_inrange_attr
    own_alive_number = 2 if friplayer['baseinfo']['isdead'] == '0' else 1

    alive = 1
    if friplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if nextplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if otherplayer['baseinfo']['isdead'] != '1':
        alive += 1
    inputdata.append(alive)
    inputdata.append(emery_alive_num)
    inputdata.append(own_alive_number)
    ##'team_can_change',
    inputdata.append(getFeature_can_change(curplayer, friplayer))
    ##'emery_can_change',
    inputdata.append(getFeature_can_change(nextplayer, otherplayer))

    # phase_id
    inputdata.append(getTablePhase(jdata, curseat))
    if len(curplayer) == 0:
        print("_21214_choose_action error")

    ## 武将基础信息
    inputdata.extend(getPlayerInfoWay2(curplayer, curseat))
    ##
    curhandcards = getHandCardlist(curplayer)
    inputdata.extend(getHandCardSpellCount(curhandcards))
    inputdata.extend(getCardNumSuitList(curhandcards))
    ##
    ##equip spell
    curequiscards = getEquipCardlist(curplayer)
    equisspell = getEquisSpell(curequiscards)
    inputdata.extend(equisspell)
    ## curstate_jiu
    inputdata.append(getStatusJiu(curplayer['skillinfo']))
    #是否已有闪电
    inputdata.append(getJudgeSpellForFlash(friplayer['judgeinfo']))
    ##curstate_tslh
    inputdata.append(getStatusTslh(curplayer['statusinfo']))
    #'have_use_sha',
    inputdata.append(getStatusHaveUseSha(curplayer['skillinfo']))
    ## cur_can_sha
    inputdata.append(getStatusCanSha(curplayer, curplayer['skillinfo']))
    ## need_give_up
    inputdata.append(getNeedGiveupCard(curplayer))
    ##'can_use_tao_jiu',
    inputdata.append(getCardNumBySpell(curhandcards, 3) + getCardNumBySpell(curhandcards, 82))
    ##fri
    ##'friplayer',
    inputdata.extend(get_action_FriplayerbaseInfo(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equisspell))
    ##nextplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, nextplayer, own_alive_number, emery_alive_num, equisspell))
    ##otherplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, otherplayer, own_alive_number, emery_alive_num, equisspell))
    #can_jdsr
    inputdata.append(deal_can_jdsr(curhandcards,curplayer,friplayer,nextplayer,otherplayer,own_alive_number,emery_alive_num))
    # action_idx
    inputdata.append(getAcionIdxLabel(jdata['Labelinfo']))
    ##
    if getAcionIdxLabel(jdata['Labelinfo']) in [14,22,38] and (getFeature_hs_rwd(jdata) or getFeature_norsha_tj(jdata,curseat)):
        inputdata.append(1)
    else:
        inputdata.append(0)

    # can_use_kurou
    skill_lst = []
    for item in curplayer['skillinfo']:
        skill_lst.append(item['skillid'])
    can_use_kuoru = 0
    hand_cards = [int(ii) for ii in  curplayer['handinfo']['cards'].split(';')] if 'cards' in curplayer['handinfo'] else []
    equip_cards = [int(ii) for ii in  curplayer['equipinfo']['cards'].split(';')] if 'cards' in curplayer['equipinfo'] else []
    if len(hand_cards) == 0 and equip_cards == 0:
        can_use_kuoru =  0
    else:
        for item in curplayer['skillinfo']:
            if item['skillid'] == '710' and item['datas'] == '0':
                can_use_kuoru =  1
    if '710' not in skill_lst:
        can_use_kuoru =  1
    inputdata.append(can_use_kuoru)
    return inputdata


def deal_guanyu_activate_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    ##fri
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    nextplayer = getPlayerInfoBySeat(jdata, getNextSeat(curseat))
    otherplayer = getPlayerInfoBySeat(jdata, getOtherSeat(curseat))

    ##
    inputdata = []
    emery_alive_num = 0
    if nextplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    if otherplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    ##emery_inrange_attr
    own_alive_number = 2 if friplayer['baseinfo']['isdead'] == '0' else 1

    alive = 1
    if friplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if nextplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if otherplayer['baseinfo']['isdead'] != '1':
        alive += 1
    inputdata.append(alive)
    inputdata.append(emery_alive_num)
    inputdata.append(own_alive_number)
    ##'team_can_change',
    inputdata.append(getFeature_can_change(curplayer, friplayer))
    ##'emery_can_change',
    inputdata.append(getFeature_can_change(nextplayer, otherplayer))

    # phase_id
    inputdata.append(getTablePhase(jdata, curseat))
    if len(curplayer) == 0:
        print("_21214_choose_action error")

    ## 武将基础信息
    inputdata.extend(getPlayerInfoWay2(curplayer, curseat))
    ##
    curhandcards = getHandCardlist(curplayer)
    inputdata.extend(getHandCardSpellCount(curhandcards))
    inputdata.extend(getCardNumSuitList(curhandcards))
    ##
    ##equip spell
    curequiscards = getEquipCardlist(curplayer)
    equisspell = getEquisSpell(curequiscards)
    inputdata.extend(equisspell)
    ## curstate_jiu
    inputdata.append(getStatusJiu(curplayer['skillinfo']))
    #是否已有闪电
    inputdata.append(getJudgeSpellForFlash(friplayer['judgeinfo']))
    ##curstate_tslh
    inputdata.append(getStatusTslh(curplayer['statusinfo']))
    #'have_use_sha',
    inputdata.append(getStatusHaveUseSha(curplayer['skillinfo']))
    ## cur_can_sha
    inputdata.append(getStatusCanSha(curplayer, curplayer['skillinfo']))
    ## need_give_up
    inputdata.append(getNeedGiveupCard(curplayer))
    ##'can_use_tao_jiu',
    inputdata.append(getCardNumBySpell(curhandcards, 3) + getCardNumBySpell(curhandcards, 82))
    ##fri
    ##'friplayer',
    inputdata.extend(get_action_FriplayerbaseInfo(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equisspell))
    ##nextplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, nextplayer, own_alive_number, emery_alive_num, equisspell))
    ##otherplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, otherplayer, own_alive_number, emery_alive_num, equisspell))
    #can_jdsr
    inputdata.append(deal_can_jdsr(curhandcards,curplayer,friplayer,nextplayer,otherplayer,own_alive_number,emery_alive_num))
    # action_idx
    inputdata.append(getAcionIdxLabel(jdata['Labelinfo']))
    ##
    if getAcionIdxLabel(jdata['Labelinfo']) in [14,22,38] and (getFeature_hs_rwd(jdata) or getFeature_norsha_tj(jdata,curseat)):
        inputdata.append(1)
    else:
        inputdata.append(0)
    ## have_red_card
    have_red_card = 0
    cur_hand_card_color = getCardNumSuitList(curhandcards)
    if cur_hand_card_color[0] + cur_hand_card_color[1] > 0:
        have_red_card = 1
    equip_card_color = getCardNumSuitList(curequiscards)
    if equip_card_color[0] + equip_card_color[1] > 0:
        have_red_card = 1
    inputdata.append(have_red_card)
    return inputdata


#普通杀藤甲
def getFeature_norsha_tj_forPlayer(jdata, curseat, enemyplayer):
    if enemyplayer['baseinfo']['isdead'] == '1':
        return 0

    actionPID = int(jdata['Labelinfo'][0]['actionPID'])

    if actionPID in [21219, 21220, 21209]:
        return 0

    if actionPID == 21210:
        spellId = int(jdata['Labelinfo'][0]['useCard']['spellId'])
    elif actionPID == 21212:
        spellId = int(jdata['Labelinfo'][0]['useSpell']['spellId'])

    curplayer = getPlayerInfoBySeat(jdata, curseat)
    curequipspell = getEquisSpell(getEquipCardlist(curplayer))
    if int(curequipspell[0]) == 87:
        return 0

    if (spellId in [27, 33, 37] and actionPID == 21212) or (
            (spellId == 1 and actionPID == 21210) and cardId_2_cardSpace[
        int(jdata['Labelinfo'][0]['useCard']['cardId'])] in sha_type_space[0]):
        if len(enemyplayer['equipinfo']) > 0:
            equipspell = getEquisSpell(getEquipCardlist(enemyplayer))
            if int(equipspell[1]) == 88:
                return 1
    return 0

### 火杀藤甲
def getFeature_hs_tj_ForPlayer(jdata, curseat, enemyplayer):
    if enemyplayer['baseinfo']['isdead'] == '1':
        return 0

    actionPID = int(jdata['Labelinfo'][0]['actionPID'])
    if actionPID in [21219, 21220, 21209]:
        return 0

    if actionPID == 21210 and int(jdata['Labelinfo'][0]['useCard']['spellId']) == 1:
        curplayer = getPlayerInfoBySeat(jdata, curseat)
        cardlabel = cardId_2_cardSpace[int(jdata['Labelinfo'][0]['useCard']['cardId'])]
        if cardlabel in sha_type_space[6]:
            if len(enemyplayer['equipinfo']) > 0:
                equipspell = getEquisSpell(getEquipCardlist(enemyplayer))
                if int(equipspell[1]) == 88:
                    return 1
        elif cardlabel in sha_type_space[0] and len(curplayer['equipinfo']) > 0 and len(enemyplayer['equipinfo']) > 0:
            curequipspell = getEquisSpell(getEquipCardlist(curplayer))
            tarequipspell = getEquisSpell(getEquipCardlist(enemyplayer))
            if int(curequipspell[0]) == 87 and int(tarequipspell[1]) == 88:
                return 1
    return 0

### 黑杀rwd
def getFeature_hs_rwd_ForPlayer(jdata, enemyplayer):
    if enemyplayer['baseinfo']['isdead'] == '1':
        return 0

    actionPID = int(jdata['Labelinfo'][0]['actionPID'])
    if actionPID in [21219, 21220, 21209]:
        return 0

    if actionPID == 21210 and int(jdata['Labelinfo'][0]['useCard']['spellId']) == 1:
        cardSuit = cardId_2_cardSpace[int(jdata['Labelinfo'][0]['useCard']['cardId'])].split('_')[2]
        if cardSuit in ['3','4']:
            if len(enemyplayer['equipinfo']) > 0:
                equipspell = getEquisSpell(getEquipCardlist(enemyplayer))
                if int(equipspell[1]) == 200:
                    return 1
    elif actionPID == 21212 and int(jdata['Labelinfo'][0]['useSpell']['spellId']) == 37:
        card = int(jdata['Labelinfo'][0]['useSpell']['datas'].split(';')[-1])
        cardSuit = cardId_2_cardSpace[card].split('_')[2]
        if cardSuit in ['3','4']:
            if len(enemyplayer['equipinfo']) > 0:
                equipspell = getEquisSpell(getEquipCardlist(enemyplayer))
                if int(equipspell[1]) == 200:
                    return 1
    elif actionPID == 21212 and int(jdata['Labelinfo'][0]['useSpell']['spellId']) == 27:
        card1 = int(jdata['Labelinfo'][0]['useSpell']['datas'].split(';')[-2])
        card2 = int(jdata['Labelinfo'][0]['useSpell']['datas'].split(';')[-1])
        cardSuit1 = cardId_2_cardSpace[card1].split('_')[2]
        cardSuit2 = cardId_2_cardSpace[card2].split('_')[2]
        if cardSuit1 in ['3','4'] and cardSuit2 in ['3','4']:
            if len(enemyplayer['equipinfo']) > 0:
                equipspell = getEquisSpell(getEquipCardlist(enemyplayer))
                if int(equipspell[1]) == 200:
                    return 1
    return 0

def getFeature_jsbysz_ForPlayer(jdata, jiu_state, enemyplayer):
    if enemyplayer['baseinfo']['isdead'] == '1':
        return 0

    actionPID = int(jdata['Labelinfo'][0]['actionPID'])
    if actionPID in [21219, 21220, 21209]:
        return 0

    if jiu_state == 0:
        return 0

    if actionPID == 21210 and int(jdata['Labelinfo'][0]['useCard']['spellId']) == 1 or (actionPID == 21212 and int(jdata['Labelinfo'][0]['useSpell']['spellId']) in [1,33,37,27]):
        if len(enemyplayer['equipinfo']) > 0:
            equipspell = getEquisSpell(getEquipCardlist(enemyplayer))
            if int(equipspell[1]) == 89:
                return 1
    return 0


def get_21214_choose_target_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    ##fri
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    nextplayer = getPlayerInfoBySeat(jdata, getNextSeat(curseat))
    otherplayer = getPlayerInfoBySeat(jdata, getOtherSeat(curseat))

    inputdata = []

    emery_alive_num = 0
    if nextplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    if otherplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    ##emery_inrange_attr
    own_alive_number = 2 if friplayer['baseinfo']['isdead'] == '0' else 1

    alive = 1
    if friplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if nextplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if otherplayer['baseinfo']['isdead'] != '1':
        alive += 1
    inputdata.append(alive)
    inputdata.append(emery_alive_num)
    inputdata.append(own_alive_number)
    ##'team_can_change',
    inputdata.append(getFeature_can_change(curplayer, friplayer))
    ##'emery_can_change',
    inputdata.append(getFeature_can_change(nextplayer, otherplayer))

    action_idx = getAcionIdxLabel(jdata['Labelinfo'])

    ## 武将基础信息
    inputdata.extend(getPlayerInfoWay4(curplayer, curseat))
    ##
    curhandcards = getHandCardlist(curplayer)
    inputdata.extend(getHandCardSpellCount(curhandcards))
    inputdata.extend(getCardNumSuitList(curhandcards))
    ##
    ##equip spell
    curequiscards = getEquipCardlist(curplayer)
    equisspell = getEquisSpell(curequiscards)
    inputdata.extend(equisspell)
    ## curstate_jiu
    curstate_jiu = getStatusJiu(curplayer['skillinfo'])
    inputdata.append(curstate_jiu)
    #是否已有闪电
    inputdata.append(getJudgeSpellForFlash(friplayer['judgeinfo']))
    ##curstate_tslh
    inputdata.append(getStatusTslh(curplayer['statusinfo']))
    #'have_use_sha',
    inputdata.append(getStatusHaveUseSha(curplayer['skillinfo']))
    ## cur_can_sha
    inputdata.append(getStatusCanSha(curplayer, curplayer['skillinfo']))
    ## need_give_up
    inputdata.append(getNeedGiveupCard(curplayer))
    ##'can_use_tao_jiu',
    inputdata.append(1 if getCardNumBySpell(curhandcards, 3) + getCardNumBySpell(curhandcards, 82) > 0 else 0)
    ##fri
    ##'friplayer',
    inputdata.extend(get_action_FriplayerbaseInfo(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equisspell))
    ##nextplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, nextplayer, own_alive_number, emery_alive_num, equisspell))
    if action_idx in [14,22,38,63] and int(curplayer['baseinfo']['charid']) == 27 and int(nextplayer['baseinfo']['isdead']) == 0:
        ## nextinkuanggu
        inputdata.append(1 if inputdata[-1] <= 1 else 0)
    else:
        inputdata.append(0)
    ##普通杀藤甲
    inputdata.append(getFeature_norsha_tj_forPlayer(jdata, curseat, nextplayer))
    ##火杀藤甲
    inputdata.append(getFeature_hs_tj_ForPlayer(jdata, curseat, nextplayer))
    ##黑杀仁王盾
    inputdata.append(getFeature_hs_rwd_ForPlayer(jdata, nextplayer))
    ##酒杀白银狮子
    inputdata.append(getFeature_jsbysz_ForPlayer(jdata, curstate_jiu, nextplayer))

    ##otherplayer
    inputdata.extend(get_action_EmeryplayerbaseInfo_base(curplayer, otherplayer, own_alive_number, emery_alive_num, equisspell))
    if action_idx in [14,22,38,63] and int(curplayer['baseinfo']['charid']) == 27:
        ## otherinkuanggu
        inputdata.append(1 if inputdata[-1] <= 1 else 0)
    else:
        inputdata.append(0)
    ##普通杀藤甲
    inputdata.append(getFeature_norsha_tj_forPlayer(jdata, curseat, otherplayer))
    ##火杀藤甲
    inputdata.append(getFeature_hs_tj_ForPlayer(jdata, curseat, otherplayer))
    ##黑杀仁王盾
    inputdata.append(getFeature_hs_rwd_ForPlayer(jdata, otherplayer))
    ##酒杀白银狮子
    inputdata.append(getFeature_jsbysz_ForPlayer(jdata, curstate_jiu, otherplayer))
    # action_idx
    inputdata.append(action_idx)
    ## cards
    cards = getAcionCardList(jdata['Labelinfo'])
    for i in range(0, 2):
        inputdata.append(cards[0]) if i < len(cards) else inputdata.append(0)
    # target_target
    inputdata.append(getAcionTarget(jdata['Labelinfo']))
    return inputdata

def get_action_FriplayerbaseInfo_for_Cards(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equipspell):
    ret = []
    ## 武将基础信息
    if int(friplayer['baseinfo']['isdead']) == 0:
        ret.extend(getPlayerInfoWay2(friplayer, curseat))
        # equip onehot
        equipcards = getEquipCardlist(friplayer)
        # 装备牌
        ret.append(getEquisSpell(equipcards)[1])
        friequipMark = getEquisMark(equipcards)
        # fri_inrange_attr
        fri_inrange_attr = get_target_within_range_attack(curplayer, friplayer, own_alive_number, emery_alive_num, equipspell, friequipMark)
        ret.append(fri_inrange_attr[0])
        # fri_spell_range
        fri_spell_range = get_target_within_range_spell(curplayer, friplayer, own_alive_number, emery_alive_num, equipspell, friequipMark)
        ret.append(fri_spell_range[0])
    else:
        ret.extend([0 for i in range(11)])
    return ret

def get_action_EmeryplayerbaseInfo_base_ForCards(curplayer, enemyplayer, own_alive_number, enemy_alive_num, equipspell):
    ret = []
    if int(enemyplayer['baseinfo']['isdead']) == 0:
        ret.extend(getPlayerInfoWay3(enemyplayer))
        # equisspell
        equipcards = getEquipCardlist(enemyplayer)
        ret.append(getEquisSpell(equipcards)[1])
        nextequipMark = getEquisMark(equipcards)
        #inrange_attr
        inrange_attr = get_target_within_range_attack(curplayer, enemyplayer, own_alive_number, enemy_alive_num, equipspell, nextequipMark)
        ret.append(inrange_attr[0])
        #spell_range
        spell_range = get_target_within_range_spell(curplayer, enemyplayer, own_alive_number, enemy_alive_num, equipspell, nextequipMark)
        ret.append(spell_range[0])
    else:
        ret.extend([0 for i in range(10)])
    return ret

def get_21214_choose_card_inputdata(jdata, curseat):
    curplayer = getPlayerInfoBySeat(jdata, curseat)
    ##fri
    friplayer = getPlayerInfoBySeat(jdata, getFriSeat(curseat))
    nextplayer = getPlayerInfoBySeat(jdata, getNextSeat(curseat))
    otherplayer = getPlayerInfoBySeat(jdata, getOtherSeat(curseat))

    emery_alive_num = 0
    if nextplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    if otherplayer['baseinfo']['isdead'] == '0':
        emery_alive_num += 1
    ##emery_inrange_attr
    own_alive_number = 2 if friplayer['baseinfo']['isdead'] == '0' else 1

    alive = 1
    if friplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if nextplayer['baseinfo']['isdead'] != '1':
        alive += 1
    if otherplayer['baseinfo']['isdead'] != '1':
        alive += 1

    input = []
    ## 武将基础信息
    input.extend(getPlayerInfoWay4(curplayer, curseat))
    ## curplayer手牌
    curhandcards = getHandCardlist(curplayer)
    input.extend(getCardSpellNumberColor(curhandcards))
    ##
    curequiscards = getEquipCardlist(curplayer)
    equisspell = getEquisSpell(curequiscards)
    input.extend(getEquisIndex(curequiscards))
    
    ##'friplayer',
    input.extend(get_action_FriplayerbaseInfo_for_Cards(curplayer, curseat, friplayer, own_alive_number, emery_alive_num, equisspell))
    ##nextplayer
    input.extend(get_action_EmeryplayerbaseInfo_base_ForCards(curplayer, nextplayer, own_alive_number, emery_alive_num, equisspell))
    ##otherplayer
    input.extend(get_action_EmeryplayerbaseInfo_base_ForCards(curplayer, otherplayer, own_alive_number, emery_alive_num, equisspell))
    # actionidx
    input.append( getAcionIdxLabel(jdata['Labelinfo']))
    # card
    cards = getAcionCardList(jdata['Labelinfo'])
    
    inputdata = []
    for card in cards:
        temp = copy.deepcopy(input)
        temp.append(card)
        inputdata.append(temp)
    return inputdata
