import sys
import time

import base64
import json
from Crypto.Cipher import AES
import datetime
import random
import requests
import urllib3

cookie ="FROM_TYPE=weixin; v=5.5; wechatSESS_ID=8faf46faf507e4b0deb70459a901d7ba3916fa2db8f4be15; Authorization=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1c2VySWQiOjQwMTYwOTk4LCJzY2hJZCI6MjAwNTgsImV4cGlyZUF0IjoxNjk1OTE4OTUwfQ.IKwC-eP3VJX9Dk90wutsluVclOB3dqhf-brT-txzjIRXlYqVl0q0zUabxsNHSvTL9NkHYrRjzVx7kDxaYu4ie2row1OdYuqQptlsnIQagNLrjxxVJYwZItoro0batK6_c8BfzYCpFCkUBU24aZVpoAktrdLEKWsKDGrpe7a4vmN3K4utQqbjUcTZ0dJrj6PAqnU6MI86mTTqE24Autphwlaes1Hbvu_8RgXaLmyEAzA4Btu2ii0KYKXx7lJIJexITXWEDWbxvcM0drXy0OSXKbv6Nq35RYrsXX_7K2iIEkL2KBGLdveuLyMtjXASL1F5pTjKcLdMoavvi4rYmTG3iA; Hm_lvt_7ecd21a13263a714793f376c18038a87=1695195530,1695218871,1695341977,1695911750; Hm_lpvt_7ecd21a13263a714793f376c18038a87=1695911813; SERVERID=d3936289adfff6c3874a2579058ac651|1695911814|1695911746"
header= {
    "Host": "wechat.v2.traceint.com",
    "Connection": "keep-alive",
    "Content-Length": "194",
    "App-Version": "2.0.14",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x6309021a) XWEB/8237 Flue",
    "Content-Type": "application/json",
    "Accept": "'*/*'",
    "Origin": "https://web.traceint.com",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://web.traceint.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cookie" : cookie
}

url = 'https://wechat.v2.traceint.com/index.php/graphql/ '


def test1():
    data = {
        "operationName": "offenSeatIndex",
        "query": "query offenSeatIndex {\n userAuth {\n reserve {\n libs(libType: -1) {\n lib_floor\n is_open\n lib_name\n lib_type\n lib_id\n }\n }\n oftenseat {\n list {\n id\n info\n lib_id\n seat_key\n status\n }\n }\n }\n}"
    }
    data2={"operationName":"index","query":"query index {\n userAuth {\n user {\n prereserveAuto: getSchConfig(extra: true, fields: \"prereserve.auto\")\n }\n currentUser {\n sch {\n isShowCommon\n }\n }\n prereserve {\n libs {\n is_open\n lib_floor\n lib_group_id\n lib_id\n lib_name\n num\n seats_total\n }\n }\n oftenseat {\n prereserveList {\n id\n info\n lib_id\n seat_key\n status\n }\n }\n }\n}"}
    a = requests.session()
    rsp = a.post(url=url, headers=header, json=data2,verify=False)
    j = rsp.json()
    print(j['data']['userAuth']['oftenseat']['prereserveList'])
    print(j['data']['userAuth']['prereserve']['libs'][0])


def test0():
    data={"operationName":"prereserve","query":"query prereserve {\n userAuth {\n prereserve {\n prereserve {\n day\n lib_id\n seat_key\n seat_name\n is_used\n user_mobile\n id\n lib_name\n }\n }\n }\n}"}
    a = requests.session()
    rsp = a.post(url=url, headers=header, json=data,verify=False)
    j=rsp.json()
    print(j)

def test2():
    data={"operationName":"libLayout","query":"query libLayout($libId: Int!) {\n userAuth {\n prereserve {\n libLayout(libId: $libId) {\n max_x\n max_y\n seats_booking\n seats_total\n seats_used\n seats {\n key\n name\n seat_status\n status\n type\n x\n y\n }\n }\n }\n }\n}","variables":{"libId":114223}}
    a = requests.session()
    rsp = a.post(url=url, headers=header, json=data,verify=False)
    j=rsp.json()
    print(j)

def test3():
    data={"operationName":"save","query":"mutation save($key: String!, $libid: Int!, $captchaCode: String, $captcha: String) {\n userAuth {\n prereserve {\n save(key: $key, libId: $libid, captcha: $captcha, captchaCode: $captchaCode)\n }\n }\n}","variables":{"key":"10,20.","libid":114226,"captchaCode":"","captcha":""}}
    a = requests.session()
    rsp = a.post(url=url, headers=header, json=data,verify=False)
    j=rsp.json()
    print(j)

def test4():
    data={"operationName":"prereserve","query":"query prereserve {\n userAuth {\n prereserve {\n prereserve {\n day\n lib_id\n seat_key\n seat_name\n is_used\n user_mobile\n id\n lib_name\n }\n }\n }\n}"}
    a = requests.session()
    rsp = a.post(url=url, headers=header, json=data,verify=False)
    j=rsp.json()
    print(j)


# AES-demo
'''
采用AES对称加密算法
'''
# str不是16的倍数那就补足为16的倍数
def add_to_16(value):
    while len(value) % 16 != 0:
        value += '\0'
    return str.encode(value)  # 返回bytes


# 加密方法
def encrypt_oracle(data):
    # 秘钥
    key = 'lwx20010322'
    # 待加密文本
    text = data
    # 初始化加密器
    aes = AES.new(add_to_16(key), AES.MODE_ECB)
    # 先进行aes加密
    encrypt_aes = aes.encrypt(add_to_16(text))
    # 用base64转成字符串形式
    encrypted_text = str(base64.encodebytes(encrypt_aes), encoding='utf-8')  # 执行加密并转码返回bytes
    print(encrypted_text)


# 解密方法
def decrypt_oralce(data):
    # 秘钥
    key = 'lwx20010322'
    # 待解密文本
    text = data
    # 初始化加密器
    aes = AES.new(add_to_16(key), AES.MODE_ECB)
    # 优先逆向解密base64成bytes
    base64_decrypted = base64.decodebytes(text.encode(encoding='utf-8'))
    # 执行解密密并转码返回str
    decrypted_text = str(aes.decrypt(base64_decrypted), encoding='utf-8').replace('\0', '')
    print(decrypted_text)


def bookSeat(url, header):
    # 开始选座
    print('--------------开始选座----------------------')
    startTime = time.time()
    response = requests.session()
    count = 0
    while True:
        count += 1
        print(f'\n***********************第{count}轮选座请求开始****************************')
        # 各个接口请求参数
        home = {"operationName":"index","query":"query index($pos: String!, $param: [hash]) {\n userAuth {\n oftenseat {\n list {\n id\n info\n lib_id\n seat_key\n status\n }\n }\n message {\n new(from: \"system\") {\n has\n from_user\n title\n num\n }\n indexMsg {\n message_id\n title\n content\n isread\n isused\n from_user\n create_time\n }\n }\n reserve {\n reserve {\n token\n status\n user_id\n user_nick\n sch_name\n lib_id\n lib_name\n lib_floor\n seat_key\n seat_name\n date\n exp_date\n exp_date_str\n validate_date\n hold_date\n diff\n diff_str\n mark_source\n isRecordUser\n isChooseSeat\n isRecord\n mistakeNum\n openTime\n threshold\n daynum\n mistakeNum\n closeTime\n timerange\n forbidQrValid\n renewTimeNext\n forbidRenewTime\n forbidWechatCancle\n }\n getSToken\n }\n currentUser {\n user_id\n user_nick\n user_mobile\n user_sex\n user_sch_id\n user_sch\n user_last_login\n user_avatar(size: MIDDLE)\n user_adate\n user_student_no\n user_student_name\n area_name\n user_deny {\n deny_deadline\n }\n sch {\n sch_id\n sch_name\n activityUrl\n isShowCommon\n isBusy\n }\n }\n }\n ad(pos: $pos, param: $param) {\n name\n pic\n url\n }\n}","variables":{"pos":"App-首页"}}
        liblist = {"operationName":"list","query":"query list {\n userAuth {\n reserve {\n libs(libType: -1) {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n libGroups {\n id\n group_name\n }\n reserve {\n isRecordUser\n }\n }\n record {\n libs {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_color_name\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n }\n rule {\n signRule\n }\n }\n}"}


        # 主页常用座位状态 0为空闲 1为被选 查询场馆是否还有剩余位置 num>=0 表示场馆还未满
        responseOftenSeats = response.post(url=url, headers=header, json=home, verify=False).json()
        responseInfo=responseOftenSeats['data']['userAuth']['reserve']['reserve']

        # 查询预约信息
        if responseInfo != None:
            if responseInfo['status'] >= 0: # 具体是多少不知道,反正肯定大于0
                print(f'您貌似已经预定了座位,请在手机上查看')
                return
        print('您尚未预定座位')
        oftenseatsList = responseOftenSeats['data']['userAuth']['oftenseat']['list']

        # 开始选座中的所有场馆的字典,循环查看是否开放,这里我是随机选了一个场馆,一般只要开了一个其他的也应该开了
        while True:
            responseliblist = response.post(url=url, headers=header, json=liblist, verify=False).json()
            libs = responseliblist['data']['userAuth']['reserve']['libs']

            # 随便找一个看看有没有开放
            is_open=libs[0]['is_open']
            if is_open == True:
                print("is_open:",is_open)
                print('场馆已开放')
                break

            print('场馆暂未开放! 请稍等......')


# ========================如果座位所在场馆未满,且座位未被选,则添加到列表中;如果说列表为空,则说明两个座位都没法选=========================
        dataList = []
        for seat in oftenseatsList:
            if seat['status']==0:
                print(seat['info']+'是空闲状态')
                # 座位的请求发送需要在坐标后面加一个英文的 .  例如:12,23.
                key = seat['seat_key']
                libid = seat['lib_id']
                # 查询场馆是否满人
                for lib in libs:
                    # 场馆id符合and 场馆剩余位置数量不为0 num是座位剩余数
                    num=lib['lib_rt']['seats_total']-lib['lib_rt']['seats_used']
                    if lib['lib_id'] ==libid  and num != 0:
                        seat = {"operationName": "reserueSeat",
                         "query": "mutation reserueSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserueSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}",
                         "variables": {"seatKey": key, "libId": libid, "captchaCode": "", "captcha": ""}}
                        dataList.append(seat)
                        print(lib['lib_name']+'场馆还未满',f'剩余位置:{num}')
                        break

                    # 场馆id符合 and 场馆剩余位置数量等于0
                    if lib['lib_id'] == libid and num == 0:
                        print(lib['lib_name']+'场馆已满')
                        break
            else:
                print(seat['info']+'已经被占用状态')

        # 选座
        # print(dataList)
        if len(dataList) > 0:  # 用于判断是否还有座位可选,因为每次抢被选座位都会清除一个座位
            for data in dataList:

                # 发送一个 选座 的请求
                libid = data['variables']['libId']
                libInfo = {"operationName": "libLayout",
                 "query": "query libLayout($libId: Int, $libType: Int) {\n userAuth {\n reserve {\n libs(libType: $libType, libId: $libId) {\n lib_id\n is_open\n lib_floor\n lib_name\n lib_type\n lib_layout {\n seats_total\n seats_booking\n seats_used\n max_x\n max_y\n seats {\n x\n y\n key\n type\n name\n seat_status\n status\n }\n }\n }\n }\n }\n}",
                 "variables": {"libId": libid}}
                # 模拟 选择场馆 按钮请求
                response.post(url=url, headers=header, json=libInfo, verify=False)

                # 先发送选座请求
                time.sleep(random.uniform(0.1, 0.2))
                r = response.post(url=url, headers=header, json=data, verify=False)
                r_json = r.json()

                # 判断请求是否通过
                if r_json['data']['userAuth']['reserve']['reserueSeat'] != None:  # 如果返回的是True
                        print(f'\n====座位{data["variables"]["seatKey"]}号通过请求和信息查询===\n'
                              f'抢座成功!\n'
                              f'请求的状态:{r.status_code}\n'
                              f'响应的内容:{r_json}\n'
                              f'抢座用时:{r.elapsed.total_seconds()}\n'
                              f'座位信息和时间:{datetime.datetime.now()}\n'
                              f'====座位{data["variables"]["seatKey"]}号   通过  请求和信息查询===\n')
                        return

                # 请求没通过 打印错误信息
                print(f'\n====座位{data["variables"]["seatKey"]}号 请求异常===\n'
                      f'座位{dataList.index(data) + 1}号 请求异常的信息!\n'
                              f'请求的状态:{r.status_code}\n'
                              f'响应的内容:{r_json}\n'
                              f'抢座用时:{r.elapsed.total_seconds()}\n'
                              f'座位信息和时间:{datetime.datetime.now()}\n'
                      f'====座位{data["variables"]["seatKey"]}号 请求异常===\n')
                dataList.remove(data)  # 移除这个座位
                time.sleep(random.uniform(0.5, 0.9))

        # 超过30秒直接退出
        elif (time.time() - startTime) >= 30:
            print(f'\n抢座核心运行已超过{time.time() - startTime},无论抢不抢到都将自动停止!\n')
            return

# =================================两个常用都选不上,就轰炸两个常用座位对应的场馆=================================
        else:
            print('\n==============两个座位都没选上,进入场馆轰炸模式!==================')

            # 遍历常用座位所在的场馆,获取场馆信息
            for i in [0,1]:
                # 从常用中获取场馆id,info
                libid = oftenseatsList[i]["lib_id"]
                libName=oftenseatsList[i]["info"].split(' ')[0]
                print("\n场馆id:",libid,",场馆名字:",libName)

                #获取场馆信息的请求参数
                libInfo = {"operationName": "libLayout",
                           "query": "query libLayout($libId: Int, $libType: Int) {\n userAuth {\n reserve {\n libs(libType: $libType, libId: $libId) {\n lib_id\n is_open\n lib_floor\n lib_name\n lib_type\n lib_layout {\n seats_total\n seats_booking\n seats_used\n max_x\n max_y\n seats {\n x\n y\n key\n type\n name\n seat_status\n status\n }\n }\n }\n }\n }\n}",
                           "variables": {"libId": libid}}

                # 模拟 选择场馆 按钮请求
                lib=response.post(url=url, headers=header, json=libInfo, verify=False).json()
                seatsInfo=lib['data']['userAuth']['reserve']['libs'][0]['lib_layout']
                seatsFree=seatsInfo['seats_total']-seatsInfo['seats_used']
                print('剩余数:',seatsFree," 这里的剩余座位数因为包括了一些没有名字的座位比如沙发,所以请以抢到的座位为准!")
                if seatsFree <= 0:
                    print(f"{libName}场馆已满")
                    continue
                seatsList=seatsInfo['seats']

                num = 1  # 计数器
                for seat in seatsList:

                    # 获取该场馆的每个座位对应的信息
                    seatName = seat['name']
                    seatStatus = seat['seat_status'] # 状态为1表示没被选, 3是被选
                    status = seat['status'] # False表示未被选, True表示被选
                    Type = seat['type'] # type=1 是表示座位正常的,其他都是不正常

                    # 如果座位没问题,就发送请求
                    if seatStatus == 1 and status == False and Type == 1 and seatName is not None:
                        key = seat['key']
                        data = {"operationName": "reserueSeat",
                                "query": "mutation reserueSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserueSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}",
                                "variables": {"seatKey": key, "libId": libid, "captchaCode": "", "captcha": ""}}

                        # 先发送选座请求
                        print(f'\n发送第{num}次请求')
                        time.sleep(random.uniform(0.1, 0.2))
                        r = response.post(url=url, headers=header, json=data, verify=False)
                        r_json = r.json()

                        # 判断请求是否通过
                        if r_json['data']['userAuth']['reserve']['reserueSeat'] != None:  # 如果返回的是True
                            print(f'===={libName}座位{seatName}号通过请求和信息查询===\n'
                                  f'{libName}座位{seatName}号抢座成功!\n'
                                  f'请求的状态:{r.status_code}\n'
                                  f'响应的内容:{r_json}\n'
                                  f'抢座用时:{r.elapsed.total_seconds()}\n'
                                  f'座位信息和时间:{datetime.datetime.now()}\n'
                                  f'====座位{libName}{seatName}号   通过  请求和信息查询===\n')
                            return

                        # 请求没通过 打印错误信息
                        print(f'===={libName}座位{seatName}号 请求异常===\n'
                              f'{libName}座位{seatName}号 请求异常的信息!\n'
                              f'请求的状态:{r.status_code}\n'
                              f'响应的内容:{r_json}\n'
                              f'抢座用时:{r.elapsed.total_seconds()}\n'
                              f'座位信息和时间:{datetime.datetime.now()}\n'
                              f'===={libName}座位{seatName}号 请求异常===\n')
                        time.sleep(random.uniform(0.2, 0.3))
                        num += 1

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


def getLocalSeatInfo():
    configSet = getConfig("User.json")
    localSeats = configSet['expand_seats']
    print(f"本地座位:{localSeats}")

    # 获取场馆名字 id
    response = requests.session()

    liblist = {"operationName": "list",
               "query": "query list {\n userAuth {\n reserve {\n libs(libType: -1) {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n libGroups {\n id\n group_name\n }\n reserve {\n isRecordUser\n }\n }\n record {\n libs {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_color_name\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n }\n rule {\n signRule\n }\n }\n}"}

    responseliblist = response.post(url=url, headers=header, json=liblist, verify=False).json()
    # 获取场馆的id
    libs = responseliblist['data']['userAuth']['reserve']['libs']

    # 获取本地场馆名对应的场馆id
    lib_name_id = []
    for lib in libs:
        for localSeat in localSeats:
            if lib["lib_name"] == localSeats[localSeat]["lib_name"]:
                Name = lib["lib_name"]
                Id = lib["lib_id"]
                Dict = {'Name': Name, 'Id': Id, 'Seat': localSeats[localSeat]["seat_name"]}
                lib_name_id.append(Dict)

    # 获取场馆对应的座位名字的 座位key
    lib_seats = []
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
                lib_seats.append(
                    {"libName": lib['Name'], "libId": libid, "seatName": seat['name'], "seatKey": seat['key']})
    return lib_seats


if __name__ == '__main__':
    # 不输出警告
    urllib3.disable_warnings()
    response = requests.session()
    libInfo = {"operationName": "libLayout",
               "query": "query libLayout($libId: Int!) {\n userAuth {\n prereserve {\n libLayout(libId: $libId) {\n max_x\n max_y\n seats_booking\n seats_total\n seats_used\n seats {\n key\n name\n seat_status\n status\n type\n x\n y\n }\n }\n }\n }\n}",
               "variables": {"libId": 114222}}
    # 模拟 “选择场馆” 按钮请求,获取场馆座位信息
    lib = response.post(url=url, json=libInfo,headers=header, verify=False).json()

    # 获取场馆信息，判断是否已满
    seatsInfo = lib['data']['userAuth']['prereserve']['libLayout']['seats']
    print(seatsInfo)

    # # bookSeat(url,header)
    #
    # getLocalSeatInfo()

    # print(time.localtime(time.time()+86400))

    #获取被害者的馆室和常用座位
    # home = {"operationName":"index","query":"query index($pos: String!, $param: [hash]) {\n userAuth {\n oftenseat {\n list {\n id\n info\n lib_id\n seat_key\n status\n }\n }\n message {\n new(from: \"system\") {\n has\n from_user\n title\n num\n }\n indexMsg {\n message_id\n title\n content\n isread\n isused\n from_user\n create_time\n }\n }\n reserve {\n reserve {\n token\n status\n user_id\n user_nick\n sch_name\n lib_id\n lib_name\n lib_floor\n seat_key\n seat_name\n date\n exp_date\n exp_date_str\n validate_date\n hold_date\n diff\n diff_str\n mark_source\n isRecordUser\n isChooseSeat\n isRecord\n mistakeNum\n openTime\n threshold\n daynum\n mistakeNum\n closeTime\n timerange\n forbidQrValid\n renewTimeNext\n forbidRenewTime\n forbidWechatCancle\n }\n getSToken\n }\n currentUser {\n user_id\n user_nick\n user_mobile\n user_sex\n user_sch_id\n user_sch\n user_last_login\n user_avatar(size: MIDDLE)\n user_adate\n user_student_no\n user_student_name\n area_name\n user_deny {\n deny_deadline\n }\n sch {\n sch_id\n sch_name\n activityUrl\n isShowCommon\n isBusy\n }\n }\n }\n ad(pos: $pos, param: $param) {\n name\n pic\n url\n }\n}","variables":{"pos":"App-首页"}}
    # liblist = {"operationName":"list","query":"query list {\n userAuth {\n reserve {\n libs(libType: -1) {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n libGroups {\n id\n group_name\n }\n reserve {\n isRecordUser\n }\n }\n record {\n libs {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_color_name\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n }\n rule {\n signRule\n }\n }\n}"}
    #
    # response = requests.session()
    # response.headers = header
    #
    # # 常用座位1所在的馆室id 获取
    # responseOftenSeats = response.post(url=url,json=home, verify=False).json()
    # responseOftenSeatsInfo=responseOftenSeats['data']['userAuth']['oftenseat']['list'][0]
    #
    # oftenlibid = responseOftenSeatsInfo['lib_id']
    # oftenlibinfo = responseOftenSeatsInfo['info']
    # print(oftenlibinfo+"----"+str(oftenlibid))
    #
    # # 所有馆室的列表
    # responseLib = response.post(url=url,json=liblist, verify=False).json()
    # libs = responseLib['data']['userAuth']['reserve']['libs']
    # print(libs)
    #
    # is_open = None
    # open_num = 1
    # while True:
    #     if is_open == True:
    #         break
    #     print(f'No.{open_num}次请求场馆是否开放中,请稍稍候......')
    #     for openLib in libs:
    #         if oftenlibid == openLib['lib_id'] and openLib['is_open'] == True:
    #             print(oftenlibinfo+'所在的场馆已开放')
    #             is_open = True
    #             break
    #     open_num += 1

    # with open('newCookie.txt', 'w', encoding='utf-8') as fp:
    #     fp.write(f"{datetime.datetime.now()}更新的cookie为:" +"\n"+ cookie)
    #     print('已保存本次的新的cookie,可以在newCookie.txt文件中查看')



    # 加密
    # a=input('请输入加密时间:')
    # encrypt_oracle(a)
    # # 解密
    # decrypt_oralce("aXmakjvijOmecsudPH4Hz3fmfnVejA9NMjXqJtUlAuE=")

    #     print(str(datetime.datetime.now()))
    #     urllib3.disable_warnings()
    #     # test0()
    #     # test1()
    #     # test2()
    #     # test3()
    #     # test4()
    #     test5()
