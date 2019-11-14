from bs4 import BeautifulSoup
import requests
import time
import random
from fake_useragent import UserAgent
from crawl_funs import *
import re
import time
import random
from crawl_funs import jump_parsing

# 长沙
# PAGE_URL_ALL="http://esf.cs.fang.com/housing"
# HOMR_UTL='http://esf.cs.fang.com/'
# 郑州 zz
# PAGE_URL_ALL="http://esf.zz.fang.com/housing"
# HOMR_UTL='http://esf.zz.fang.com/'
# # 无锡
# PAGE_URL_ALL = "https://wuxi.esf.fang.com/housing"
# HOMR_UTL = 'http://esf.wuxi.fang.com/'

# 常州
PAGE_URL_ALL = "https://cz.esf.fang.com/housing"
HOMR_UTL = 'http://esf.cz.fang.com/'


Priceurl = "http://fangjia.fang.com/pinggu/ajax/chartajax.aspx?dataType=proj&KeyWord={newcode}&year=2"
session = requests.Session()
ua = UserAgent()
target_headers = {'User-Agent': ua.random}
Re_groupinfo_Columnnames = ["cityss", "this_domain", "newcode", "currNewcode",
                            "city", "isqddslp", "cityin", "projname", "district",
                            "comarea", "logopic", "price", "address", "xcnum",
                            "dpNum", "citysuo", "Grade", "GradeSorce", "WuyeGrade",
                            "WuyeGradeSorce", "WuyeDescribe", "InActiveGrade",
                            "InActiveGradeSorce", "InActiveDescribe", "EducationGrade",
                            "EducationGradeSorce", "EducationDescribe", "MapBoardGrade",
                            "MapBoardGradeSorce", "MapBoardDescribe", "StationaryValue"]
Re_groupPJinfo_Columnnames = ["jsmonth", "jsguapaiscore", "jssearchscore"]
Re_groupPJinfo_surrounding_Columnnames = ["market", "entertainment", "food"]
Re_groupinfo_model = "var{Column_name}=\"(.+?)\";"
Re_groupPJinfo_model = "var{Column_name}=\[(.+?)\];"
Re_groupPJinfo_surrounding__model = "var{Column_name}=(.+?);"
Re_Description_models = {
    'completiontime': "竣工时间(.+?)年",
    'projarea': "占地面积(.+?)平方米",
    'propertytime': "为(.+?)年",
    'developers': "由(.+?)负责开发"
}
num = 0
if (judgenet() == "ok"):
    distinct_list = get_distinct_list(PAGE_URL_ALL)
    if distinct_list:
        for distinct_info in distinct_list:
            try:
                distinct_name = distinct_info["distinct"]
                distinct_href = HOMR_UTL + distinct_info["href"].replace('__0', '__1')  # replace 目的为爬去住宅
                # 获取页数
                try:
                    page_info = repeat_find_info(distinct_href, 'houselist_B14_01', 10, find_id=True)
                    page_info = page_info.find('span')
                    distinct_page = int(re.findall("\d+", page_info.text)[0])
                except Exception as e:
                    print(e)
                    print('行政区-页码-ERROR')
                    # 缺少日志
                    continue

                # 小区info获取
                distinct_href = distinct_href.replace('0_1_0', '0_{page}_0')
                for page in range(1, distinct_page + 1):
                    try:
                        group_list = repeat_find_info(distinct_href.format(page=page), 'list rel mousediv', 10, find_class=True, find_all=True)
                    except Exception as e:
                        print('小区-list-ERROR', )
                        # 缺少日志
                        continue
                    for onegroup in group_list:
                        result_info = {}  # 小区信息
                        result_price = {}  # 小区价格信息
                        result_search_index = {}  # 小区搜索指数
                        result_Listed_index = {}  # 小区挂牌指数
                        result_surrounding_info = {}  # 小区周边设施、评价信息
                        onegroup_info = onegroup.find(class_='plotTit')
                        onegroup_name = onegroup_info.text
                        onegroup_href = onegroup_info["href"]  # href需要判断是否为真，判断有没有http或者fang 即可 已判断
                        if 'fang' not in onegroup_href:
                            print(onegroup_href, '住宅小区链接无效')
                            # 缺少日志
                            continue
                        try:
                            if 'https:' not in onegroup_href:
                                onegroup_href = 'https:' + onegroup_href
                            groupinfos, groupinfo_html = repeat_find_info(onegroup_href, 'script', 10, find_all=True, encode='gb2312', returnhtml=True)
                        except Exception as e:
                            print(e)
                            print('小区-single-ERROR', )
                            # 缺少日志
                            continue
                        # 小区信息首页->数据正则处理 ===start
                        for Re_groupinfo_Columnname in Re_groupinfo_Columnnames:
                            Re_groupinfo_result = re.findall(Re_groupinfo_model.format(Column_name=Re_groupinfo_Columnname),
                                                             str(groupinfos).replace(' ', ''))
                            if (len(Re_groupinfo_result)):
                                result_info[Re_groupinfo_Columnname] = Re_groupinfo_result[0]
                            else:
                                result_info[Re_groupinfo_Columnname] = ""
                        if (result_info["newcode"]):
                            Re_groupinfo_result_zums = re.findall(r"var znums = (.+?);", str(groupinfos))
                            result_info["znums"] = Re_groupinfo_result_zums[0]
                            # 小区数据需补充，对口学校，建筑年份，物业（PJ）

                        # 竣工时间，建筑面积，产权，开发商,建筑类型,物业公司,对口学校,房屋总数,楼栋总数
                        groupinfo_Description = groupinfo_html.find(attrs={"name": "Description"})['content']
                        try:
                            for Re_Description_model in Re_Description_models.items():
                                Description_data = re.findall(Re_Description_model[1], groupinfo_Description)
                                if len(Description_data):
                                    result_info[Re_Description_model[0]] = Description_data[0]
                                else:
                                    result_info[Re_Description_model[0]] = ''
                        except Exception as e:
                            print(e, groupinfo_Description)
                            # 缺少日志
                            continue
                        Rinfolist_result = {'建筑年代': '', '二手房源': '', '建筑类型': '', '小区位置': ''}
                        try:
                            Rinfolist = groupinfo_html.find(class_='Rinfolist').find_all('li')
                            Rinfolist_namelist = [data_li.find('b').text for data_li in Rinfolist]
                            Rinfolist_contextlist = [
                                data_li.text.strip('\n').replace(data_li.find('b').text, '').strip('\n') for data_li in
                                Rinfolist]
                            for key in Rinfolist_result.keys():
                                try:
                                    Rinfolist_result[key] = Rinfolist_contextlist[Rinfolist_namelist.index(key)]
                                except:
                                    continue
                        except:
                            pass
                        result_info.update(Rinfolist_result)
                        ## 小区信息首页->数据正则处理 ===end

                        ## 小区评价信息抓取 ===start
                        try:
                            # print(onegroup_href + "pingji/")
                            groupRe_PJinfos, PJ_html = repeat_find_info(onegroup_href + "pingji/", 'script', 10, find_all=True, encode='gb2312',
                                                                        returnhtml=True)
                        except Exception as e:
                            print(e)
                            # 缺少日志
                            continue
                        Re_PJinfos = []
                        for Re_groupPJinfo_Columnname in Re_groupPJinfo_Columnnames:
                            Re_groupPJinfo_result = re.findall(
                                Re_groupPJinfo_model.format(Column_name=Re_groupPJinfo_Columnname),
                                str(groupRe_PJinfos).replace(' ', ''))
                            if (Re_groupPJinfo_result):
                                Re_PJinfos.append(Re_groupPJinfo_result[0])
                        PJinfos = []
                        if (Re_PJinfos):
                            for i in range(str(Re_PJinfos[0]).split(',').__len__()):
                                PJinfo = {}
                                PJinfo["jsmonth"] = str(Re_PJinfos[0]).split(',')[i].replace('\'', '')
                                PJinfo["jsguapaiscore"] = str(Re_PJinfos[1]).split(',')[i]
                                PJinfo["jssearchscore"] = str(Re_PJinfos[2]).split(',')[i]
                                PJinfos.append(PJinfo)
                        result_Listed_index = {'newcode': '', 'projname': '', '201906': '', '201907': '', '201908': '', '201909': '', '201910': ''}
                        result_search_index = {'newcode': '', 'projname': '', '201906': '', '201907': '', '201908': '', '201909': '', '201910': ''}
                        result_Listed_index['newcode'] = result_info["newcode"]
                        result_Listed_index['projname'] = onegroup_name
                        result_search_index['newcode'] = result_info["newcode"]
                        result_search_index['projname'] = onegroup_name
                        for PJinfo in PJinfos:
                            if PJinfo['jsmonth'].replace('-', '') in result_Listed_index.keys():
                                result_Listed_index[PJinfo['jsmonth'].replace('-', '')] = PJinfo['jsguapaiscore']
                                result_search_index[PJinfo['jsmonth'].replace('-', '')] = PJinfo['jssearchscore']

                        # 物业信息
                        wypjlist_result = {'物业服务费': '', '容积率': '', '绿化率': '', '车位配比': ''}
                        try:
                            wypjlist = PJ_html.find(class_='wypj').find_all(class_='f16')
                            wypjlist_namelist = [data.text.split(' : ')[0] for data in wypjlist]
                            wypjlist_contextlist = [data.text.split(' : ')[1] for data in wypjlist]
                            for key in wypjlist_result.keys():
                                try:
                                    wypjlist_result[key] = wypjlist_contextlist[wypjlist_namelist.index(key)]
                                except:
                                    continue
                        except:
                            pass
                        result_info.update(wypjlist_result)
                        # 板块信息
                        bkpjlist_result = {'板块均价': '', '板块面积': '', '板块东西跨度': '', '板块南北跨度': ''}
                        try:
                            bkpjlist = PJ_html.find(class_='bk_zhancon').find_all(class_='f16')
                            bkpjlist_namelist = [data.text.strip('\n').split('：')[0] for data in bkpjlist]
                            bkpjlist_contextlist = [data.text.strip('\n').split('：')[1] for data in bkpjlist]
                            for key in bkpjlist_result.keys():
                                try:
                                    bkpjlist_result[key] = bkpjlist_contextlist[bkpjlist_namelist.index(key)]
                                except:
                                    continue
                        except:
                            pass
                        result_info.update(bkpjlist_result)
                        ## 小区评价信息抓取 ===end
                        # 价格信息抓取 ===start
                        try:
                            result_price = {'newcode': '', 'projname': '', '201712': '', '201801': '', '201802': '', '201803': '',
                                            '201804': '', '201805': '', '201806': '', '201807': '', '201808': '', '201809': '',
                                            '201810': '', '201811': '', '201812': '', '201901': '', '201902': '', '201903': '',
                                            '201904': '', '201905': '', '201906': '', '201907': '', '201908': '', '201909': '', '201910': '', '201911': ''}
                            result_price["newcode"] = result_info["newcode"]
                            result_price["projname"] = onegroup_name
                            # print(Priceurl.format(newcode=result_info["newcode"]))
                            Princeresponse = session.get(Priceurl.format(newcode=result_info["newcode"]),
                                                         headers=target_headers, timeout=10)
                            Princehtml = BeautifulSoup(Princeresponse.text.encode('utf-8'), 'html5lib')  # 待修改
                            # Princehtml = jump_parsing(response_test=Princeresponse.text.encode('utf-8'), **{'headers': target_headers, 'timeout': 10})
                            Re_Prince = r'\[\[(.+?)\]]&'
                            Priceendre = re.findall(Re_Prince, Princehtml.text)
                            if (len(Priceendre)):
                                data_price_list = Priceendre[0].split('],[')
                                for data_price in data_price_list:
                                    # print(data_price)
                                    timestamp, h_price = data_price.split(',')
                                    timestamp = int(timestamp[:10])
                                    time_local = time.localtime(timestamp)
                                    dt = time.strftime("%Y%m", time_local)
                                    if dt in result_price.keys():
                                        result_price[dt] = h_price
                        except Exception as e:
                            print(e)
                            print(onegroup_name + "价格抓取失败" + e.__str__())
                            # Error_GroupPJ += onegroup_name + "-" + Priceurl.format(groupid=result["newcode"]) + ";"
                            continue
                        # 价格信息抓取 ===end
                        # 坐标解析 ===start
                        coordinate = getXY(result_info)
                        if coordinate != None:
                            result_info.update(coordinate)
                        else:
                            print('坐标解析失败')
                            continue
                        loadinfo(result_info, 'projinfo', num, )
                        loadinfo(result_price, 'projprice', num)
                        loadinfo(result_search_index, 'prosearchindex', num)
                        loadinfo(result_Listed_index, 'prolistindex', num)
                        print(onegroup_name, 'ok')
                        num += 1
                        time.sleep(random.random() * 5)
            except Exception as e:
                print(e, '未知错误')
                if judgenet() == "ok":
                    continue
                else:
                    print('请尽快连接网络！！！')
                    time.sleep(100)
                    continue
            time.sleep(random.random() * 10)
        print('num:', str(num))
        time.sleep(random.random() * 20)

        # 郑州周边数据
        # print(result_surrounding_info)

        ####信息抓取完毕，准备存储
