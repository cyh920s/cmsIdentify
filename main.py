import argparse
import hashlib
import json
import threading
import time
import os
from threading import Thread

import gevent
import requests

from queue import Queue

import urllib3
from colorama import *

class CmsScan(object):

    #初始化构造函数
    def __init__(self,url,proxy):
        self.url = url                  # 需要匹配的url
        self.verify_url = ''            # 本地cms指纹url
        self.cmsa_queue = Queue()       # cmsprintA队列
        self.cmsb_queue = Queue()       # cmsprintB队列
        self.next_cms = False           # 是否进行下一个字典匹配
        self.proxy = proxy              # 是否开启代理
        self.proxys = {                 # 代理存储池
            'proxy':''
        }
        requests.packages.urllib3.disable_warnings()
    # 随机获取一个代理
    def getProxy(self):
        try:
            requ = requests.get('http://47.103.208.189:9876/get/')
            if requ.status_code != 200:
                print(Fore.RED + '代理设置失败,请等待一会再设置代理......')
                return 0
            requ.content.decode("utf-8")
            # 将 JSON 对象转换为 Python 字典
            proxy = json.loads(requ.text)
            if proxy['https']:
                res = requests.get('https://' + proxy['proxy'])
                if res.status_code != 200:
                    return self.getProxy()
                print(Fore.BLUE + 'ProxyIP:\t' + 'http://' + proxy['proxy'])
                self.proxys['proxy'] = proxy['proxy']
            else:
                res = requests.get('http://' + proxy['proxy'])
                if res.status_code != 200:
                    return self.getProxy()
                print(Fore.BLUE + 'ProxyIP:\t' + 'http://' + proxy['proxy'])
                self.proxys['proxy'] = proxy['proxy']
        except Exception as e:
            print(e)
            return self.getProxy()
    # 扫描两个本地json 文件,分别组成队列存储
    def CmsFingereQueue (self):
        cmsa_file = open('data\cmsprintA.json', 'r')
        CmsDataA = json.load(cmsa_file)
        for i in CmsDataA:
            self.cmsa_queue.put(i)
        cmsa_file.close()

        cmsb_file = open('data\cmsprintB.json', 'r')
        CmsDataB = json.load(cmsb_file)
        for i in CmsDataB:
            self.cmsb_queue.put(i)
        cmsb_file.close()

    # 开始批量检测CMS指纹
    def verifyCMSA(self):
        while not self.cmsa_queue.empty():
            if self.next_cms:
                break
            try:
                cmsa_data = self.cmsa_queue.get()
                print(Fore.GREEN+'cmsprintA.json:\t'+cmsa_data['remark'] + '\t' + cmsa_data['staticurl'] + cmsa_data['homeurl'])
                if cmsa_data['staticurl']:
                    md5_url = self.url + cmsa_data['staticurl']
                    md5 = self.getWebMD5(md5_url)
                    if md5 == cmsa_data['checksum']:
                        print(Fore.BLUE + 'CMS name:  ' + cmsa_data['remark'] + ' 验证条件：    ' + cmsa_data['staticurl'])
                        self.next_cms = True
                        break
                        #return False
                # else:
                #     if cmsa_data['homeurl']:
                #         if self.proxy:
                #             reques = requests.get(self.url + cmsa_data['homeurl'], timeout=3,proxies=self.proxys, verify=False)
                #             if reques.status_code == 200:
                #                 keyword = reques.content
                #                 name = str(keyword).find(cmsa_data['keyword'])
                #                 if name != -1:
                #                     print(Fore.BLUE + 'CMS name:  ' + cmsa_data['remark'] + '验证条件：    ' + cmsa_data[
                #                         'homeurl'])
                #                     self.next_cms = True
                #                     break
                #         else:
                #             reques = requests.get(self.url + cmsa_data['homeurl'], timeout=3)
                #             if reques.status_code == 200:
                #                 keyword = reques.content
                #                 name = str(keyword).find(cmsa_data['keyword'])
                #                 if name != -1:
                #                     print(Fore.BLUE + 'CMS name:  ' + cmsa_data['remark'] + '验证条件：    ' + cmsa_data[
                #                         'homeurl'])
                #                     self.next_cms = True
                #                     break
            except requests.exceptions.ReadTimeout as e:
                if self.proxy:
                    print(Fore.RED + 'ip被封----------------------------------------------------------')
                    print(Fore.RED + '正在重新设置IP---------------------------------------------------')
                    self.getProxy()
                    print(e)
                print(e)
                #self.getProxy()
        # return True
    def verifyCMSB(self):
        while not self.cmsb_queue.empty():
            if self.next_cms:
                break
            try:
                cmsb_data = self.cmsb_queue.get()
                print(Fore.GREEN+'cmsprintB.json:\t' + cmsb_data['name'] + '\t' + cmsb_data['url'])
                url = self.url + cmsb_data['url']
                # if self.proxy:
                #     reques = requests.get(url, timeout=3,proxies=self.proxys, verify=False)
                #     if reques.status_code == 200:
                #         keyword = reques.content
                #         if cmsb_data['re']:
                #             name = str(keyword).find(cmsb_data['re'])
                #             if name != -1:
                #                 print(Fore.BLUE + 'CMS name:  ' + cmsb_data['name'] + '验证条件：    ' + cmsb_data['url'])
                #                 self.next_cms = True
                #                 break
                #     else:
                #         reques = requests.get(url, timeout=3)
                #         if reques.status_code == 200:
                #             keyword = reques.content
                #             if cmsb_data['re']:
                #                 name = str(keyword).find(cmsb_data['re'])
                #                 if name != -1:
                #                     print(
                #                         Fore.BLUE + 'CMS name:  ' + cmsb_data['name'] + '验证条件：    ' + cmsb_data['url'])
                #                     self.next_cms = True
                #                     break
                if cmsb_data['md5']:
                    md5 = self.getWebMD5(url)
                    if md5 == cmsb_data['md5']:
                        print(Fore.BLUE + 'CMS name:  ' + cmsb_data['name'] + ' 验证条件：    ' + cmsb_data['url'])
                        self.next_cms = True
                        break
            except requests.exceptions.ReadTimeout as e:
                if self.proxy:
                    print(Fore.RED + 'ip被封----------------------------------------------------------')
                    print(Fore.RED + '正在重新设置IP---------------------------------------------------')
                    self.getProxy()
                    print(e)
                print(e)

    def getWebRe(self,url):
        reques = requests.get(url, timeout=3)
        if reques.status_code == 200:
            keyword = reques.content
            return keyword
        return -1

    # 获取Web端MD5值
    def getWebMD5(self,url):
        if self.proxy:
            reques = requests.get(url, timeout=3,proxies=self.proxys, verify=False)
            reques_txt = reques.content
            md5 = hashlib.md5()
            # 拿到web端MD5
            md5.update(reques_txt)
            web_md5 = md5.hexdigest()
            return web_md5
        else:
            reques = requests.get(url, timeout=3)
            reques_txt = reques.content
            md5 = hashlib.md5()
            # 拿到web端MD5
            md5.update(reques_txt)
            web_md5 = md5.hexdigest()
            return web_md5
    # 开始运行
    def Run(self):
        print('''
*===============================================================================*
                           cms指纹批量识别系统   
                            Author:@京墨                   
                            Version:1.0                             
*===============================================================================*
        ''')
        print(Fore.MAGENTA+'开始运行......')
        print(Fore.MAGENTA+'是否设置代理：\t'+str(self.proxy))
        if self.proxy:
            print(Fore.MAGENTA + '正在获取代理IP......')
            self.getProxy()
        self.CmsFingereQueue()
        self.verifyCMSA()
        if self.next_cms == False:
            self.verifyCMSB()
            if self.next_cms == False:
                print('未查询到CMS')
        # threads = [threading.Thread(target=self.verifyCMSA()) for i in range(4)]
        # for thread in threads:
        #     thread.start()
        # threads2 = [threading.Thread(target=self.verifyCMSA()) for i in range(4)]
        # for thread2 in threads2:
        #     thread2.start()
        #self.next_cms = self.verifyCMSA()
        if self.next_cms == False:
            print('未查询到CMS')



def Args():
    parse = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, add_help=False, description='''
    ===============================================================================
         请设置 -u 参数!     
         Author:@京墨                   
         Version:1.0                             
    ===============================================================================
    ''')
    #parse.add_argument('-f', '--file', help='请设置url文件路径')
    parse.add_argument('-u', '--url', help="请设置URL链接")
    parse.add_argument('-p', '--proxy', default=False, help='设置是否用代理匹配cms指纹，默认为False',
                       type=bool)  # 设置是否用代理匹配cms指纹，默认为False
    args = parse.parse_args()
    if args.url is None:
        print(parse.print_help())
        exit()
    else:
        return args
    return args


# 容易被封，记的改IP
if __name__ == "__main__":
    init(autoreset=True)
    arg = Args()
    c = CmsScan(arg.url,arg.proxy)
    c.Run()