import sys

import http.cookiejar
import json
import urllib.parse
import urllib.request


def get_code(url):
    query = urllib.parse.urlparse(url).query
    codes = urllib.parse.parse_qs(query).get('code')
    if codes:
        return codes.pop()
    else:
        raise ValueError("Code not found in URL")


def get_cookie_string(code):
    cookiejar = http.cookiejar.MozillaCookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))
    response = opener.open(
        "http://wechat.v2.traceint.com/index.php/urlNew/auth.html?" + urllib.parse.urlencode({
            "r": "https://web.traceint.com/web/index.html",
            "code": code,
            "state": 1
        })
    )
    cookie_items = []
    for cookie in cookiejar:
        cookie_items.append(f"{cookie.name}={cookie.value}")
    cookie_string = '; '.join(cookie_items)
    return cookie_string

def saveCookie(cookieStr,num=1):
    '''
    储存cookie到Users.json
    :param cookieStr:
    :param num: 用户名 ,例如user1
    :return:
    '''
    #读取数据
    with open('../config/Users.json', 'r', encoding='utf-8') as fp:
       data= json.load(fp)

    # 如果传入的数据,长度小于200,说明是无效的,函数结束
    if len(cookieStr)<200:
        print("Cookie string: \n")
        print(f'处理后的数据:{cookieStr}')
        print('\n此cookie似乎是无效的,请重试(如果没有出现"Authorization="这个东西,请重新扫码或者手动输入cookie)')
        return False
    #有效cookie,打印数据,并修改读取的data
    print("\nCookie string: \n")
    print(f'处理后的数据:{cookieStr}')
    data[f'{num}']['Cookie']=cookieStr

    #储存数据
    with open('../config/Users.json', 'w', encoding='utf-8') as fp:
        fp.write(json.dumps(data,ensure_ascii=False))
    print(f'{num}的cookie注入成功!')

def userNameCheck():
    '''
    检验输入的用户名是否符合格式
    :return:
    '''
    while True:
        num = input("请输入您要注入的用户名:(user1,user2或者user3):")
        if num[0:len(num) - 1] == "user" and type(eval(num[-1])) == type(1):
            print('用户名无误,检测成功!')
            return num
        else:
            print('用户名存在错误,请检查后重试!')

def main(num):
    """
    获取cookie的主程序
    :param num: 就是用户名字
    :return:
    """
    while True:
        choice = input('功能1:输入url更新数据(需要输入1)\n功能2:输入cookie更新数据(需要输入2)\n功能3:直接更新数据(需要输入3)\n请问您要输入:')
        if choice == '1':
            url = input("请输入url:")
            code = get_code(url)
            cookie_string = get_cookie_string(code)
            print(f'\n解析后的源数据:\n{cookie_string}\n')
            # 解析后的cookie
            splitCookie = cookie_string.split(";")[0]
            # 先将cookie保存到users.json
            e = saveCookie(splitCookie, num)
            if e ==False:
                return
            # 再将users.json里面的数据更新到config.json里面去
            saveConfig()
            break

        elif choice == '2':
            cookie = input("请输入cookie:")
            # 先将cookie保存到users.json
            saveCookie(cookie, num)
            # 再将users.json里面的数据更新到config.json里面去
            saveConfig()
            break

        elif choice == '3':
            # 直接读取user.json进行cookie更新
            saveConfig()
            break

        else:
            print('----------------------请输入正确的指令,不用的话直接叉掉-----------------------')


def getConfig(address):
    '''
    用于读取config.json配置文件
    :return:
    '''
    try:
        with open(address, 'r', encoding='utf-8') as config:
            return json.load(config)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("exc_type:", exc_type)
        print("exc_value:", exc_value)
        print("exc_traceback:", exc_traceback)

def switchData():
    #1、读取UserData.json,放到字典里面
    configDict=getConfig('../config/Users.json')
    #2、读取configN.json到列表
    BeforeConfigList=[]
    #3、读取和修改后的数据
    AfterConfigList=[]
    for i in range(1,4):#左闭右开,[1,4)
        config=getConfig(f'../config/config{i}.json')
        BeforeConfigList.append(config)
        #选中第i-1个元素
        configN=BeforeConfigList[i-1]
        BeforeConfigList[i-1]['openTime']=configDict[f'user{i}']['openTime']
        BeforeConfigList[i-1].get('header')['Cookie']=configDict[f'user{i}']['Cookie']
        BeforeConfigList[i-1].get('queue_header')["Cookie"] = configDict[f'user{i}']['Cookie']
        AfterConfigList.append(configN)
    # print(AfterConfigList)
    return AfterConfigList

def saveConfig():
    for content in switchData():
        with open(f'../config/config{switchData().index(content)+1}.json', 'w', encoding='utf-8') as fp:
            fp.write(json.dumps(content,ensure_ascii=False))
    print('\n-------------------------------------！用户数据数据正在更新！----------------------------------------\n'
          '-------------------------------------！用户数据数据更新完成！----------------------------------------')


if __name__ == '__main__':
    try:
        main(userNameCheck())
        input('按任意键退出')
    except Exception as e:
        print(e)
        print('#如果报错说找不到文件中的某个属性，去看一下json文件是不是被清了,或者数据输入乱了')


