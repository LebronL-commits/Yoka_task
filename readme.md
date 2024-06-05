**作业介绍**  
我的作业是制作一个三国杀的武将AI，他可以通过模型来输出想要做出的动作（2v2场景下）。  
针对这个问题，我们需要首先对三国杀的游戏场景进行建模，对每个动作做出特征切片，从而便于我们对做出动作时进行特征提取。切片中需要有在场的4个武将的所有基本信息，比如武将id，技能id，武将血量，武将的手牌，装备牌，判定区域的牌等   
有了特征切片（kf）之后，我们可以基于（kf）来获取有用的特征信息，从而对任务场景进行建模。   
根据模型的准确率，我们就可以衡量该游戏ai的一级动作的准确性  
**运行流程**  
1、连接数据库 10.225.136.101:3306   
2、运行sgs_json2SimulatorInfoFromSql.py ,其中在getDatasFromMysql函数中可以根据喜好设置想要查找的数据,运行完毕之后对应
的kf切片会存在本地.   
3、运行kf2xieyidict_21214.py, mysql数据库中会储存kf对应的真实路径，后续我没对mysql进行查找,获取路径之后在去本地寻找对应的kf切片。  
4、运行deal_activate_data_for_base_charactor.ipynb, 对于每个主动技能spell，我会取10000条数据，比如说10000条杀的动作数据
该文件运行完之后会将生成的特征feather文件保存到指定目录。   
5、运行sgs_model_base_character.ipynb,运行之后模型会保存到指定目录。  
**代码文件介绍**  
1、目录/active_model_base  
a、data_script_base.py 进行数据处理的python脚本文件。  
b、deal_activate_data_for_base_charactor.ipynb 进行数据处理的jupyter文件。   
c、sgs_model_base_character.ipynb 进行模型训练的jupyter文件。  
2、/data_process  
a、kf2xieyidict_21214.py 将切片文件的地址映射存储到mysql的python文件  
b、sgs_json2SimulatorInfoFromSql.py 从mysql中读取三国杀回放json文件，并生成切片储存在本地的python文件。  
2、/public_file
a、global_define_online.py 公用定义   
b、global_func_online.py 共用函数  
3、/xieyi21214new
a、publicfuc_kf2input.py 从切片中读取数据，并将数据转化为模型所需特征的python文件。

**备注**  
数据库需要权限才能连接，sgs_model_base_character.ipynb有之前运行的结果，可以直观的体现武将AI的准确率~