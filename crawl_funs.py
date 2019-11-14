# coding=utf-8
import os
from bs4 import BeautifulSoup
import requests
import time
import random
from fake_useragent import UserAgent
from reCoordinate.baidumap import xBaiduMap
from reCoordinate.coordTransform_utils import bd09_to_wgs84
import pandas as pd


# 判断网络是否连接
def judgenet():
    try:
        os.popen("ping www.baidu.com -n 1").read()
        return ("ok")
    except(Exception):
        print('网络连接失败')
        Error_NET = 1


def loadinfo(results, Province_name, judge):
    dataframe = pd.DataFrame(results, index=[judge])
    if (judge):
        dataframe.to_csv("Data/" + Province_name + ".csv", sep=',', encoding="utf_8_sig", mode='a', header=0, index=0, columns=list(results.keys()))
    else:
        dataframe.to_csv("Data/" + Province_name + ".csv", sep=',', encoding="utf_8_sig", mode='a', index=0, columns=list(results.keys()))


def jump_parsing(response_test, **para):
    if "自动跳转中" in response_test:
        html = BeautifulSoup(response_test, 'html.parser')
        jump_url = html.find(class_='btn-redir')['href']
        # print(jump_url)
        session = requests.Session()
        response = session.get(jump_url, **para)
        # print('jump   ',jump_url)
        return BeautifulSoup(response.text, 'html.parser')
    else:
        return BeautifulSoup(response_test, 'html.parser')


def get_distinct_list(PAGE_URL_ALL):
    session = requests.Session()
    ua = UserAgent()
    target_headers = {
        'User-Agent': ua.random,
    }
    para = {'headers': target_headers, 'timeout': 20}
    try:
        response = session.get(PAGE_URL_ALL, **para)
        # print(response.text)
        html = jump_parsing(response_test=response.text, **para)
        distinct_list = []
        distinct_div = html.find(class_='qxName').find(class_='org bold')
        for sibling in distinct_div.next_siblings:
            if sibling == '\n':
                break
            distinct_list.append({"distinct": sibling.text, "href": sibling['href']})
        return distinct_list
    except Exception as e:
        return None


import time


def repeat_find_info(url, findname, repeat_num, have_repeated_time=0, find_id=False, find_class=False, find_all=False, encode=None, returnhtml=False):
    if have_repeated_time < repeat_num:
        session = requests.Session()
        ua = UserAgent()
        target_headers = {
            'User-Agent': ua.random,
        }
        # requests.utils.add_dict_to_cookiejar(session.cookies, {
        #     'global_cookie': 'rncdrgnok2dzecnpkjb2kaba31jk2szrfzi',
        #     '__utmc': '147393320',
        #     'Integrateactivity': 'notincludemc',
        #     'city': 'cz',
        #     'lastscanpage': '0',
        #     '__utma': "147393320.1914216689.1573389990.1573389990.1573612872.2",
        #     '__utmz': '147393320.1573612872.2.2.utmcsr=search.fang.com|utmccn=(referral)|utmcmd=referral|utmcct=/captcha-c4b4c7130f329939a9/redirect',
        #     'g_sourcepage': 'esf_xq%5Elb_pc',
        #     'unique_cookie': 'U_rncdrgnok2dzecnpkjb2kaba31jk2szrfzi*34',
        #     '__utmb': '147393320.90.10.1573612872'
        # })
        session_para = {'headers': target_headers, "timeout": 100}
        response = session.get(url, **session_para)
        if encode:
            response.encoding = encode
        html = jump_parsing(response_test=response.text, **session_para)
        time.sleep(20)
        info = None
        if find_all:
            if find_id:
                info = html.find_all(id=findname)
            elif find_class:
                info = html.find_all(class_=findname)
            else:
                info = html.find_all(findname)
        else:
            if find_id:
                info = html.find(id=findname)
            elif find_class:
                info = html.find(class_=findname)
            else:
                info = html.find(findname)
        if info != None:
            if returnhtml:
                return info, html
            else:
                return info
        else:
            # print("重复·",have_repeated_time)
            have_repeated_time += 1
            info = repeat_find_info(url, findname, repeat_num, have_repeated_time, find_id, find_class)
            if returnhtml:
                return info, html
            else:
                return info
    else:
        # print("返回了空值",have_repeated_time)
        return None


def getXY(result):
    try:
        bm = xBaiduMap()
        newcoordinate = bm.getLocation(result["projname"],
                                       result["city"] + ' ' + result['district'] + ' ' + result[
                                           'comarea'])
        if newcoordinate.__str__() == "None":
            newcoordinate = bm.getLocation(result["address"], result["city"])
        if newcoordinate.__str__() == "None":
            print(result["projname"] + "===解析失败")
            # 日志
            # Error_Coordinate += onegroup_name + "-" + onegroup_href + ";"
            return None
        else:
            lat_bd, lng_bd = newcoordinate
            lng_wgs84, lat_wgs84 = bd09_to_wgs84(lng_bd, lat_bd)
            return {'lat_bd': lat_bd, 'lng_bd': lng_bd, 'lat_wgs84': lat_wgs84, 'lng_wgs84': lng_wgs84}
    except Exception as e:
        return None
