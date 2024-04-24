import sys

import datetime
import http.cookiejar
import json
import requests
import urllib.parse
import urllib.request
import urllib3


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

def saveCookie(cookieStr):
    '''
    储存cookie到User.json
    :param cookieStr:
    :return:
    '''
    #读取数据
    with open('../config/User.json', 'r', encoding='utf-8') as fp:
       data= json.load(fp)

    # 如果传入的数据,长度小于200,说明是无效的,函数结束
    if len(cookieStr)<200:
        print(f'\nCookie string:\n处理后的数据:{cookieStr}')
        print('\n此cookie似乎是无效的,请重试(如果没有出现"Authorization="这个东西,请重新扫码或者手动输入cookie)')
        return False
    #有效cookie,打印数据,并修改读取的data
    print(f'\nCookie string:\n处理后的数据:{cookieStr}')
    data['user']['Cookie'] = cookieStr

    #储存数据
    with open('../config/User.json', 'w', encoding='utf-8') as fp:
        fp.write(json.dumps(data,ensure_ascii=False))
    print('用户的的cookie注入成功!\n')

    # 将最初的cookie注入到newCookie.txt文件中,防止在第一次断线未超2h的情况下,读取不到有效的cookie
    with open('newCookie.txt', 'w', encoding='utf-8') as fp:
        #  这里的 "更新的cookie为:" 这一段不要改,特别是 : 号,我用来断线的时候分割出cookie用的
        fp.write(f"{datetime.datetime.now()}数据写入时候初始化的的cookie为:" + cookieStr)
        print('已经将初始化的cookie保存到了newCookie.txt中!')


def main():
    """
    获取cookie的主程序
    :return:
    """
    while True:
        choice = input('功能1:输入url更新数据(需要输入1)\n功能2:输入cookie更新数据(需要输入2)\n功能3:直接更新数据(建立在1或者2的基础上，需要已经更新的cookie,输入3)\n请问您要输入:')
        if choice == '1':
            url = input("请输入url:")
            code = get_code(url)
            cookie_string = get_cookie_string(code)
            print(f'\n解析后的源数据:\n{cookie_string}\n')
            # 解析后的cookie
            splitCookie = cookie_string.split(";")[0]
            # 先将cookie保存到users.json
            e = saveCookie(splitCookie)
            if e ==False:
                return
            # 再将users.json里面的数据更新到config.json里面去
            saveConfig()
            break

        elif choice == '2':
            cookie = input("请输入cookie:")
            # 先将cookie保存到users.json
            saveCookie(cookie)
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
    configDict = getConfig('../config/User.json')

    #2、获取本地文件中的自定义拓展座位
    seatsList = getLocalSeatInfo(configDict,configDict['user']['Cookie'])
    seats = {}
    num = 1
    for seat in seatsList:
        seats[f'seat0{num}'] = seat[f'seat0{num}']
        num += 1
    print(f"处理后的座位字典集:{seats}")
    if len(seats) == 0:
        print("WARNING：！！！您的字典集合没有任何值！！！！！\n请调整User.json中的数据,使得外置座位可以被正常读取！！！！")

    #2、读取config.json到列表
    BeforeConfigList = []
    #3、读取和修改后的数据
    AfterConfigList = []

    config = getConfig(f'../config/config.json')
    BeforeConfigList.append(config)

    configN=BeforeConfigList[0]
    configN['openTime'] =configDict['user']['openTime']
    configN.get('header')['Cookie']=configDict['user']['Cookie']
    configN.get('queue_header')['Cookie'] = configDict['user']['Cookie']
    configN['map_seats'] = seats


    AfterConfigList.append(configN)
    return AfterConfigList

def saveConfig():
    for content in switchData():
        with open(f'../config/config.json', 'w', encoding='utf-8') as fp:
            fp.write(json.dumps(content,ensure_ascii=False))
    print('\n-------------------------------------！用户数据数据正在更新！----------------------------------------\n'
          '-------------------------------------！用户数据数据更新完成！----------------------------------------')

def getLocalSeatInfo(configSet,cookie):
    url = "https://wechat.v2.traceint.com/index.php/graphql/"
    header = {
        "Host": "wechat.v2.traceint.com",
        "Connection": "keep-alive",
        "Content-Length": "311",
        "App-Version": "2.0.14",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090621) XWEB/8391 Flue",
        "Content-Type": "application/json",
        "Accept": "',*/*'",
        "X-Requested-With": "",
        "Origin": "https://web.traceint.com",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://web.traceint.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh",
        "Cookie": cookie
    }

    configSet = configSet
    localSeats = configSet['expand_seats']
    print(f"\n本地座位:{localSeats}")

    # 获取场馆名字 id
    response = requests.session()

    liblist = {"operationName": "list",
               "query": "query list {\n userAuth {\n reserve {\n libs(libType: -1) {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n libGroups {\n id\n group_name\n }\n reserve {\n isRecordUser\n }\n }\n record {\n libs {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_color_name\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n }\n rule {\n signRule\n }\n }\n}"}

    responseliblist = response.post(url=url, headers=header, json=liblist, verify=False).json()
    # 获取场馆的id
    libs = responseliblist['data']['userAuth']['reserve']['libs']

    # 获取本地场馆名对应的场馆id
    lib_name_id = []
    for localSeat in localSeats:
        for lib in libs:
            if lib["lib_name"] == localSeats[localSeat]["lib_name"]:
                Name = lib["lib_name"]
                Id = lib["lib_id"]
                Dict = {'Name': Name, 'Id': Id, 'Seat': localSeats[localSeat]["seat_name"]}
                lib_name_id.append(Dict)

    # 获取场馆对应的座位名字的 座位key
    lib_seats = []
    # 本地seat的座位号
    num = 1

    for lib in lib_name_id:
        libid = lib['Id']
        libInfo = {"operationName": "libLayout",
                   "query": "query libLayout($libId: Int!) {\n userAuth {\n oftenseat {\n libLayout(libId: $libId) {\n max_x\n max_y\n seats_booking\n seats_total\n seats_used\n seats {\n key\n name\n seat_status\n status\n type\n x\n y\n }\n }\n }\n }\n}",
                   "variables": {"libId": libid}}
        responseSeatsList = response.post(url=url, headers=header, json=libInfo, verify=False).json()
        seats = responseSeatsList['data']['userAuth']['oftenseat']['libLayout']['seats']

        for seat in seats:
            if seat['name'] == lib['Seat']:
                print(f"场馆名字:{lib['Name']}  场馆id:{libid}  座位号:{seat['name']}  座位坐标:{seat['key']}")
                lib_seats.append({f"seat0{num}": {"libName": lib['Name'], "libId": libid, "seatName": seat['name'], "seatKey": seat['key']}})
                num += 1

    return lib_seats

if __name__ == '__main__':
    try:
        urllib3.disable_warnings()
        main()
        input('按任意键退出')
    except Exception as e:
        print(e)
        print('#如果报错说找不到文件中的某个属性，去看一下json文件是不是被清了,或者数据输入乱了')


