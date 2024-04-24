import sys
import time

import base64
import datetime
import http
import json
import random
import requests
import traceback
import urllib3
import wmi
import http.cookies
import http.cookiejar
from Crypto.Cipher import AES


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


def start_grabSeat(openTime):
    '''
    程序倒计时
    :param openTime:
    :return:
    '''
    # 获取当前年月日 加上配置的时分秒，拼接成时间字符串
    ts = time.strftime("%Y-%m-%d", time.localtime(time.time()))
    openTime = ts+" "+openTime

    struct_openTime = openTime
    openTime = time.strptime(struct_openTime, "%Y-%m-%d %H:%M:%S")
    openTime = time.mktime(openTime)
    while True:
        # print(f'当前时间:{datetime.datetime.now()}')
        print(f'剩余时间:{openTime - time.time()}s')
        time.sleep(1)
        if time.time() >= openTime:
            print("------------------------------")
            print("倒计时结束,开始抢座!")
            grab_time = time.localtime(time.time())
            ts = time.strftime("%Y-%m-%d %H:%M:%S", grab_time)
            print('当前时间是： ' + ts)
            break


def configNameCheck():
    '''
    检验输入的用户名是否符合格式
    :return:
    '''
    while True:
        num = input("请输入您要使用的配置文件名:(config1,config2或者config3):")
        if num[0:len(num) - 1] == "config" and type(eval(num[-1])) == type(1):
            print('配置文件名无误,检测成功!')
            return num
        else:
            print('配置文件名存在错误,请检查后重试!')


def expire_date(dead):
    '''
    程序倒计时
    :return:
    '''
    try:
        expire_Time = dead
        expireTime = time.strptime(expire_Time, "%Y-%m-%d %H:%M:%S")
        deadTime = time.mktime(expireTime)

        if time.time() >= deadTime:
            return True
    except:
        print('未正确检测到过期时间')


def getDeviceInfo():
    """
    获取本地设备信息
    :return:
    """
    global diskStr, cpuStr, boardStr, biosStr

    c = wmi.WMI()

    info=[]

    # # 硬盘序列号
    for physical_disk in c.Win32_DiskDrive():
        diskStr=physical_disk.SerialNumber
        info.append(diskStr)

    # CPU序列号
    for cpu in c.Win32_Processor():
        cpuStr=cpu.ProcessorId.strip()
        info.append(cpuStr)

    # 主板序列号
    for board_id in c.Win32_BaseBoard():
        boardStr=board_id.SerialNumber
        info.append(boardStr)

    # bios序列号
    for bios_id in c.Win32_BIOS():
        biosStr=bios_id.SerialNumber.strip()
        info.append(biosStr)

    strValue=f'{diskStr};{cpuStr};{boardStr};{biosStr}'

    return strValue


# str不是16的倍数那就补足为16的倍数
def add_to_16(value):
    while len(value) % 16 != 0:
        value += '\0'
    return str.encode(value)  # 返回bytes


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
    return decrypted_text


def activeCheck():
    try:
        with open('../active/initConfig.txt', 'r+', encoding='utf-8') as fp:
            initConfig = fp.read()
        # 解密初始化中的设备信息
        bdinfo = decrypt_oralce(initConfig).split(';')
        # 解读本地初始配置的设备信息
        bd = bdinfo[0]+';'+bdinfo[1]+';'+bdinfo[2]+';'+bdinfo[3]

        # 解读本地初始配置的过期时间
        lastTime = bdinfo[-1]
        # 获取当前设备信息
        di = getDeviceInfo()
        # 一致则返回True 和版本号
        return bd == di, lastTime
    except:
        print('验证码错误/文件出错,请检查是否正确激活,配置文件是否存在')


def bookSeat(url, header,seats_expand,openTime, bookTime):
    """
    :param url:  我去图书馆的域名
    :param header: 请求头
    :param seats_expand: 外置拓展座位
    :return: 无返回值,用return是为了结束函数
    """
# =================================================================开始挂机========================================
    print('-----------------------------------开始挂机---------------------------------------------')
    # 今晚获取cookie,准备挂机!
    cookie_string = header['Cookie']
    # 使用session保持会话
    response = requests.session()

    response.headers = {
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
    "Accept-Language": "zh-CN,zh"
    }

    cookie = http.cookies.SimpleCookie()
    cookie.load(cookie_string)

    for key, morsel in cookie.items():
        response.cookies.set(key, morsel)

    # 获取开放时间的 完整年月日
    Time = None
    if bookTime == "todayTime":
        # 这个是今天的年月日,适用于明天启动挂机,一般来说不用,暂时废弃
        Time = time.localtime(time.time())
    if bookTime == "tomorrowTime":
        # 这个是明天的年月日,适用于今天启动挂机
        Time = time.localtime(time.time() + 86400)


    ts = time.strftime("%Y-%m-%d",Time)
    openTime0 = ts+" "+openTime
    
    struct_openTime = openTime0
    openTime1 = time.strptime(struct_openTime, "%Y-%m-%d %H:%M:%S")
    openTime2 = time.mktime(openTime1)
    
    while True:
        print(f'剩余时间:{(openTime2 - time.time())//60}分钟')
        intoCountTimes = (openTime2 - time.time())//1 # 取整
        if intoCountTimes < 180.0: # 最后三分钟进入倒计时
            print(f'==============离开放还剩{intoCountTimes//60}分钟左右,挂机结束!开始进入倒计时=====================')
            with open('intoCountTimeLogs.txt','w+',encoding='utf-8') as fp:
                fp.write(f'当前时间为:{datetime.datetime.now()},\n'
                         f'openTime:{openTime2//1}  ==>  对应的时间为:{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(openTime2//1))},\n'
                         f'time:{time.time()//1}  ==>  对应的时间为:{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()//1))},\n'
                         f'intoCountTimes:{intoCountTimes}s,\n'
                         f'是否进入倒计时:{intoCountTimes < 180.0},\n'
                         f'程序即将进入倒计时!')
            break

        if response.cookies.keys().count("Authorization") > 1:
            response.cookies.set("Authorization", domain="", value=None)
        res = response.post("http://wechat.v2.traceint.com/index.php/graphql/", json={
            "query": 'query getUserCancleConfig { userAuth { user { holdValidate: getSchConfig(fields: "hold_validate", extra: true) } } }',
            "variables": {},
            "operationName": "getUserCancleConfig"
        })

        try:
            result = res.json()
        except json.decoder.JSONDecodeError as err:
            print("Error: %s" % err)
            break
        if result.get("errors") and result.get("errors")[0].get("code") != 0:
            print("Session expired!")
            break
        print("Session OK.")
        print("响应信息:", result)

        # ==================================打印当前cookie=====================
        Adict = {}
        for key, morsel in response.cookies.items():
            Adict[key] = morsel
            break
        nowCookie = "Authorization" + "=" + Adict["Authorization"]
        if nowCookie == cookie_string:
            print("cookie未变:")
            print(nowCookie)
        if nowCookie != cookie_string:
            print("cookie已变,当前为:")
            print(nowCookie)
            cookie_string = nowCookie
            with open('newCookie.txt','w',encoding='utf-8') as fp:
                fp.write(f"{datetime.datetime.now()}更新的cookie为:"+nowCookie)
                print('已保存本次的新的cookie')

        # ==================================打印当前cookie=====================
        print("当前时间:",datetime.datetime.now())
        # 一分钟到三分钟随机更新一次会话
        sleep = random.uniform(60, 180)
        print(f"本次随机间隔时间为{sleep//1}秒左右\n")
        time.sleep(sleep)
    
    
    
    # ==============================================进入倒计时=====================================
    start_grabSeat(openTime) # 提前十秒结束倒计时,下面开始请求场馆状态

    # counts = 0
    # 抢座真正开始时间
    startTime = time.time()

    # while True:
    #     counts += 1
    #     print(f'\n***********************第{counts}轮选座请求开始****************************')
    pass
    # 各个接口请求参数
    home = {"operationName":"index","query":"query index($pos: String!, $param: [hash]) {\n userAuth {\n oftenseat {\n list {\n id\n info\n lib_id\n seat_key\n status\n }\n }\n message {\n new(from: \"system\") {\n has\n from_user\n title\n num\n }\n indexMsg {\n message_id\n title\n content\n isread\n isused\n from_user\n create_time\n }\n }\n reserve {\n reserve {\n token\n status\n user_id\n user_nick\n sch_name\n lib_id\n lib_name\n lib_floor\n seat_key\n seat_name\n date\n exp_date\n exp_date_str\n validate_date\n hold_date\n diff\n diff_str\n mark_source\n isRecordUser\n isChooseSeat\n isRecord\n mistakeNum\n openTime\n threshold\n daynum\n mistakeNum\n closeTime\n timerange\n forbidQrValid\n renewTimeNext\n forbidRenewTime\n forbidWechatCancle\n }\n getSToken\n }\n currentUser {\n user_id\n user_nick\n user_mobile\n user_sex\n user_sch_id\n user_sch\n user_last_login\n user_avatar(size: MIDDLE)\n user_adate\n user_student_no\n user_student_name\n area_name\n user_deny {\n deny_deadline\n }\n sch {\n sch_id\n sch_name\n activityUrl\n isShowCommon\n isBusy\n }\n }\n }\n ad(pos: $pos, param: $param) {\n name\n pic\n url\n }\n}","variables":{"pos":"App-首页"}}
    liblist = {"operationName":"list","query":"query list {\n userAuth {\n reserve {\n libs(libType: -1) {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n libGroups {\n id\n group_name\n }\n reserve {\n isRecordUser\n }\n }\n record {\n libs {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_color_name\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n }\n rule {\n signRule\n }\n }\n}"}

    # 开馆前 主页常用座位状态 0为空闲 1为被选 查询场馆是否还有剩余位置 num>=0 表示场馆还未满
    responseOftenSeats = response.post(url=url, json=home, verify=False).json()
    responseInfo=responseOftenSeats['data']['userAuth']['reserve']['reserve']

    # 1、查询预约信息
    if responseInfo != None:
        if responseInfo['status'] >= 0: # 具体是多少不知道,反正肯定大于0
            print(f'您貌似已经预定了座位,请在手机上查看')
            return
    print('您尚未预定座位')
    oftenseatsList = responseOftenSeats['data']['userAuth']['oftenseat']['list']

    # 2、检测是否开馆，开始选座中的所有场馆的字典,循环查看是否开放,这里我是随机选了一个场馆,一般只要开了一个其他的也应该开了
    # 常用座位1所在的馆室id 获取
    responseOftenSeatsInfo = oftenseatsList[0]
    oftenlibid = responseOftenSeatsInfo['lib_id']
    oftenlibinfo = responseOftenSeatsInfo['info']
    # print(oftenlibinfo + "----" + str(oftenlibid))


    is_open = None
    open_num = 1
    while True:
        # 所有馆室的列表
        responseLib = response.post(url=url, json=liblist, verify=False).json()
        libs = responseLib['data']['userAuth']['reserve']['libs']

        if is_open == True:
            break

        print(f'No.{open_num}次请求场馆是否开放,请稍稍候......')

        for openLib in libs:
            if oftenlibid == openLib['lib_id'] and openLib['is_open'] == True:
                print(oftenlibinfo + '所在的场馆已开放')
                is_open = True
                break
        open_num += 1

# ========================如果座位所在场馆未满,且座位未被选,则添加到列表中;如果说列表为空,则说明两个座位都没法选=========================   #
    pass
    print("\n====================================开始请求常用座位==========================================")
    # 开馆后 重新查主页常用状态!!!!!!
    # 主页常用座位状态 0为空闲 1为被选 查询场馆是否还有剩余位置 num>=0 表示场馆还未满
    responseOftenSeats = response.post(url=url, json=home, verify=False).json()
    AfteroftenseatsList = responseOftenSeats['data']['userAuth']['oftenseat']['list']

    oftenSeats = 2
    # dataList = []
    ofseat = None
    for seat in AfteroftenseatsList:
        # 状态是1表示被选,0是未选
        if seat['status'] != 1:
            print(seat['info']+f'是空闲状态，状态码：{seat["status"]}')
            # 座位的请求发送需要在坐标后面加一个英文的 .  例如:12,23.
            key = seat['seat_key']
            libid = seat['lib_id']
            # # 查询场馆是否满人
            # for lib in libs:
                # # 场馆id符合and 场馆剩余位置数量不为0 num是座位剩余数
                # num=lib['lib_rt']['seats_total']-lib['lib_rt']['seats_used']
                # if lib['lib_id'] ==libid  and num != 0:

            # 这个是直接在主页选座的接口
            seat = {"operationName":"reserveSeat",
                    "query":"mutation reserveSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserveSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}",
                    "variables":{"seatKey": key, "libId": libid,"captchaCode":"","captcha":""}}
            # dataList.append(seat)
            ofseat = seat
            # print(lib['lib_name']+'场馆还未满',f'剩余位置:{num}')
            
            break

                # # 场馆id符合 and 场馆剩余位置数量等于0
                # if lib['lib_id'] == libid and num == 0:
                    # print(lib['lib_name']+'场馆已满')
                    # break
        else:
            print(seat['info']+f'已经被占用状态，状态码：{seat["status"]}')
            # 如果这次访问的常用没法用,就减去一个常用,两个都不能用就全部减掉,使得后面可以直接运行外置座位
            oftenSeats -= 1

    pass

    # ===================================常用座位选座=============================================
    # if len(dataList) > 0:  # 用于判断是否还有座位可选,因为每次抢被选座位都会清除一个座位
    if ofseat != None:
        #剩余座位数
        # restSeats = len(dataList)
        # for data in dataList:
            # 发送一个 开始预约 的请求
            # libid = data['variables']['libId']
            # libInfo = {"operationName": "libLayout",
                       # "query": "query libLayout($libId: Int!) {\n userAuth {\n prereserve {\n libLayout(libId: $libId) {\n max_x\n max_y\n seats_booking\n seats_total\n seats_used\n seats {\n key\n name\n seat_status\n status\n type\n x\n y\n }\n }\n }\n }\n}",
                       # "variables": {"libId": libid}}
            
            # # 模拟开始预约按钮请求
            # response.post(url=url, json=libInfo, verify=False)

            # 先发送选座请求
            # time.sleep(random.uniform(0.1, 0.2))
            
            r = response.post(url=url, json=data, verify=False)
            r_json = r.json()


            # 判断请求是否通过 reserveSeat
            if r_json['data']['userAuth']['reserve']['reserveSeat'] != None:  # 如果返回的是True
                print(f'\n====座位{data["variables"]["seatKey"]}号通过请求===\n'
                      f'抢座成功!\n'
                      f'请求的状态:{r.status_code}\n'
                      f'响应的内容:{r_json}\n'
                      f'抢座用时:{r.elapsed.total_seconds()}\n'
                      f'座位信息和时间:{datetime.datetime.now()}\n'
                      f'====座位{data["variables"]["seatKey"]}号通过请求===\n')
                return

            print(f'请求的状态:{r.status_code}\n'
                  f'响应的内容:{r_json}\n'
                  f'抢座用时:{r.elapsed.total_seconds()}\n'
                  f'座位信息和时间:{datetime.datetime.now()}\n')
            time.sleep(random.uniform(0.2, 0.4))

    # ===================================外置座位选座=============================================
    # 注入外置座位
    expand_seats = []
    if oftenSeats == 0:
        print('\n=======================准备启用外置座位===============================================')
        for seat0 in seats_expand:
            libid = seats_expand[seat0]['libId']
            key = seats_expand[seat0]['seatKey']
            seat = {"operationName": "reserueSeat",
                    "query": "mutation reserueSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserueSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}",
                    "variables": {"seatKey": key, "libId": libid, "captchaCode": "", "captcha": ""}}
            expand_seats.append(seat)
            print(f"外置座位{seat0}信息:{seats_expand[seat0]}")
        print(f'外置座位添加成功！个数:{len(expand_seats)}\n')

    # 用于判断是否还有座位可选,因为每次抢被选座位都会清除一个座位
    if len(expand_seats) > 0 and len(dataList) == 0:
        # 剩余外置座位数
        amount = len(expand_seats)
        # 初始化data（座位参数）
        dataFree = None
        # 设置座位状态，用于跳出馆室循环
        free = None
        # 循环遍历每个座位对应的场馆
        for data in expand_seats:

            # 如果说找到了能用的座位就直接break
            if free:
                break

            # 还有外置座位就继续循环
            if amount != 0:
                # 发送一个 “选座” 按钮的请求
                libid = data['variables']['libId']
                libInfo = {"operationName": "libLayout",
                           "query": "query libLayout($libId: Int, $libType: Int) {\n userAuth {\n reserve {\n libs(libType: $libType, libId: $libId) {\n lib_id\n is_open\n lib_floor\n lib_name\n lib_type\n lib_layout {\n seats_total\n seats_booking\n seats_used\n max_x\n max_y\n seats {\n x\n y\n key\n type\n name\n seat_status\n status\n }\n }\n }\n }\n }\n}",
                           "variables": {"libId": libid}}

                # 模拟 “选择场馆” 按钮请求,获取场馆座位信息
                lib = response.post(url=url, json=libInfo, verify=False).json()
                # 获取场馆信息，判断是否已满
                seatsInfo = lib['data']['userAuth']['reserve']['libs'][0]['lib_layout']
                libName = lib['data']['userAuth']['reserve']['libs'][0]['lib_name']
                seatsFree = seatsInfo['seats_total'] - seatsInfo['seats_used']
                print(f'{libName}场馆剩余数:', seatsFree, " 这里的剩余座位数因为包括了一些没有名字的座位比如沙发,所以请以抢到的座位为准!")

                if seatsFree <= 0:
                    print(f"{libName}场馆已满")
                    # 剔除场馆满了的馆室
                    amount -= 1
                    continue

                # 如果场馆没满则获取场馆所有座位
                seatsList = seatsInfo['seats']

                # num = 1  # 计数器
                # 遍历所有座位
                for seat in seatsList:
                    # 获取该场馆的每个座位对应的信息
                    seatName = seat['name']
                    seatStatus = seat['seat_status']  # 状态为1表示没被选, 3是被选
                    status = seat['status']  # False表示未被选, True表示被选
                    Type = seat['type']  # type=1 是表示座位正常的,其他都是不正常
                    key = seat['key']

                    # 校验场馆座位是否与传入的外置座位,以及是否可使用，可以用则直接跳出这个场馆的座位遍历
                    if key == data['variables']['seatKey']:
                        if seatStatus == 1 and status == False and Type == 1 and seatName is not None:
                            dataFree = data
                            # 设置座位状态为可访问，用于跳出馆室循环
                            free = True
                            print(f'当前空闲座位:{seatName},状态:{seatStatus},是否被选{status}')
                            break
                        else:
                            print(f'外置座位{seatName}被选')
                            amount -= 1
        pass

        # 只有能用的空闲座位才可以这个地方执行,先发送选座请求
        time.sleep(random.uniform(0.1, 0.2))
        # 判断data 参数是否非空,座位是否空闲
        if free == True and dataFree != None:
            r = response.post(url=url, json=dataFree, verify=False)
            r_json = r.json()

            # 判断请求是否通过
            if r_json['data']['userAuth']['reserve']['reserueSeat'] == True:  # 如果返回的是True
                print(f'\n====外置座位{dataFree["variables"]["seatKey"]}号通过请求===\n'
                      f'外置抢座成功!\n'
                      f'请求的状态:{r.status_code}\n'
                      f'响应的内容:{r_json}\n'
                      f'抢座用时:{r.elapsed.total_seconds()}\n'
                      f'座位信息和时间:{datetime.datetime.now()}\n'
                      f'====外置座位{dataFree["variables"]["seatKey"]}号通过请求===\n')
                return

            print(f'外置座位{dataFree["variables"]["seatKey"]}号请求的状态:{r.status_code}\n'
                  f'响应的内容:{r_json}\n'
                  f'抢座用时:{r.elapsed.total_seconds()}\n'
                  f'座位信息和时间:{datetime.datetime.now()}\n'
                  f'座位{dataFree["variables"]["seatKey"]}号')
            time.sleep(random.uniform(0.2, 0.4))



    # 多轮抢座位的总时间超过10秒直接退出
    if (time.time() - startTime) >= 10:
        print(f'\n抢座核心运行已超过{time.time() - startTime},无论抢不抢到都将自动停止!\n')
        return

# =================================两个常用都选不上,就轰炸两个常用座位对应的场馆=================================

    print('\n==============所有自定义座位都没选上,进入常用馆室轰炸模式(有空闲就选)!==================')

    # 遍历常用座位所在的场馆,获取场馆信息
    num = 1  # 计数器，用于计算是第几次请求
    # 从常用的两个场馆去轰炸
    # mix = dataList+expand_seats

    for i in [0, 1]:

        # 从常用中获取场馆id,info
        libid = oftenseatsList[i]["lib_id"]
        libName=oftenseatsList[i]["info"].split(' ')[0]
        print("\n场馆id:",libid,",场馆名字:",libName)

        #获取场馆信息的请求参数
        libInfo = {"operationName": "libLayout",
                   "query": "query libLayout($libId: Int, $libType: Int) {\n userAuth {\n reserve {\n libs(libType: $libType, libId: $libId) {\n lib_id\n is_open\n lib_floor\n lib_name\n lib_type\n lib_layout {\n seats_total\n seats_booking\n seats_used\n max_x\n max_y\n seats {\n x\n y\n key\n type\n name\n seat_status\n status\n }\n }\n }\n }\n }\n}",
                   "variables": {"libId": libid}}

        # 模拟 选择场馆 按钮请求
        lib=response.post(url=url, json=libInfo, verify=False).json()
        seatsInfo=lib['data']['userAuth']['reserve']['libs'][0]['lib_layout']
        seatsFree=seatsInfo['seats_total']-seatsInfo['seats_used']
        print('剩余数:',seatsFree," 这里的剩余座位数因为包括了一些没有名字的座位比如沙发,所以请以抢到的座位为准!")
        print("如果座位数较少,而且接下来没显示成功抢到座位,那就应该是这个馆室满了")
        if seatsFree <= 0:
            print(f"{libName}场馆已满")
            continue

        # 获取场馆座位列表
        seatsList = seatsInfo['seats']

        # 遍历场馆座位
        for seat in seatsList:
            # 获取该场馆的每个座位对应的信息
            seatName = seat['name']
            seatStatus = seat['seat_status'] # 状态为1表示没被选, 3是被选
            status = seat['status'] # False表示未被选, True表示被选
            Type = seat['type'] # type=1 是表示座位正常的,其他都是不正常

            # 如果座位没问题,就发送请求
            if seatStatus == 1 and status == False and Type == 1 and seatName is not None:
                # 常用座位的key
                key = seat['key']
                data = {"operationName": "reserueSeat",
                        "query": "mutation reserueSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserueSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}",
                        "variables": {"seatKey": key, "libId": libid, "captchaCode": "", "captcha": ""}}
                # 先发送选座请求
                print(f'场馆{libName}发送第{num}次请求')
                time.sleep(random.uniform(0.1, 0.2))
                r = response.post(url=url, json=data, verify=False)
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

                # 如果返回的内容有 "刷" or "被'
                if r.text.find('u5c1d') != -1 or r.text.find('u5237') != -1:
                    print(f'===={libName}座位{seatName}号请求异常的信息===\n'
                          f'{libName}座位{seatName}号抢座成功!\n'
                          f'请求的状态:{r.status_code}\n'
                          f'响应的内容:{r_json}\n'
                          f'抢座用时:{r.elapsed.total_seconds()}\n'
                          f'座位信息和时间:{datetime.datetime.now()}\n'
                          f'====座位{libName}{seatName}号请求异常的信息===\n')
                    return

                # 其他错误  打印错误信息
                print(f'===={libName}座位{seatName}号 请求异常===\n'
                      f'{libName}座位{seatName}号 请求异常的信息!\n'
                      f'请求的状态:{r.status_code}\n'
                      f'响应的内容:{r_json}\n'
                      f'抢座用时:{r.elapsed.total_seconds()}\n'
                      f'座位信息和时间:{datetime.datetime.now()}\n'
                      f'===={libName}座位{seatName}号 请求异常===\n')
                time.sleep(random.uniform(0.2, 0.3))
                # 本轮选座请求的总次数加 1
                num += 1


def oneTread(url, header, seats_expand,openTime,bookTime):
    '''
    排队和请求的启动函数
    :param url:
    :param header:
    :return:
    '''
    # 开始选座
    num = 1
    while True:
        if num <= 10:
            try:
                bookSeat(url, header,seats_expand,openTime, bookTime)
                break
            except requests.exceptions.RequestException as e:
                print("=============================错误信息===============================\n", traceback.format_exc())
                print(f'准备重新建立选座连接:第{num}次重连......')
                num += 1
                time.sleep(0.5)
        else:
            print('重新建立选座请求超过20,不再重连,请检查网络是否存在问题!!!!!!!!\n直接进入抢座!')
            break


def test_book(url,header):
    # 选座功能接口,开放接口返回的是场馆表
    data={"operationName":"list","query":"query list {\n userAuth {\n reserve {\n libs(libType: -1) {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n libGroups {\n id\n group_name\n }\n reserve {\n isRecordUser\n }\n }\n record {\n libs {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_color_name\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n }\n rule {\n signRule\n }\n }\n}"}
    response=requests.session()
    r_test = response.post(url=url, headers=header, json=data, verify=False)

    if 'errors' in r_test.json().keys():
        print(r_test.json())
        print('cookie失效,或者未正确输入!请重试!')
        return False

    print('测试成功')
    return True


def main():
    try:
        # 返回值是元组,第一个元素是设备信息,第二个元素是版本号,第三个元素是过期时间
        active = activeCheck()
        # 1-激活校验
        if not active[0]:
            print('未激活,请激活后重试')
            return

        # 2-过期时间校验
        lastTime = active[1]

        if expire_date(lastTime) == True:  # 设置过期时间
            print('程序已经过期了!')
            return

        # 免责声明
        print("本程序所提供的服务仅供学习和参考使用,经过用户同意身份认证,使用爬虫采集数据\n"
              "如果使用本程序导致目标服务器出现不可预料故障(比如:开了特别多个号之类的导致目标服务器出问题),"
              "所导致的后果开发者概不承担,请使用者自行承担责任!\n"
              "(不同意输入n,同意则输入y或者任意键)")
        In = input("是否继续使用?:")
        if In == "n":
            print("程序退出!")
            return
        
        elif In == "y":
            print(f"您已同意上述条款(输入内容{In}),程序继续执行!")
            
        else:
            print(f"您已同意上述条款(输入内容{In}-任意键),程序继续执行!")
        
        # 不输出警告
        urllib3.disable_warnings()
        # 1、初始化配置类--------------cookie记得每天更新！！！
        print('\n配置初始化。。。')
        configSet = getConfig(f"../config02/config.json")   #导入配置
        print('配置初始化成功！')

        # 开始测试
        while True:
            bookTime = input("请输入今天选座还是今晚挂机明天选座(今天选座请输入1,今天挂机明天选请输入2):")
            if bookTime == "1":
                print('即将执行今天选座')
                bookTime = "todayTime"
                break
            if bookTime == "2":
                print('即将执行今天挂机明天选')
                bookTime = "tomorrowTime"
                break
            else:
                print('输入错误请重试!')

        cookieTest = input('是否要检验cookie有效性:(y表示是,任意键直接进入倒计时):')
        if cookieTest == 'y' or cookieTest == 'Y':
            print('开始测试cookie有效性')
            Test = test_book(configSet.get('url'),configSet.get('header'))
            if Test == True:  # 测试是否能成功排队,成功则表示cookie有效
                # 3、开始抢座
                oneTread(url=configSet.get('url'),
                         header=configSet.get('header'),
                         seats_expand=configSet.get('map_seats'),
                         openTime=configSet.get('openTime'),
                         bookTime=bookTime)
        else:
            oneTread(url=configSet.get('url'),
                     header=configSet.get('header'),
                     seats_expand=configSet.get('map_seats'),
                     openTime=configSet.get('openTime'),
                     bookTime=bookTime)#这里可以改成'test',用于直接测试选座功能(跳过排队,还要把倒计时功能注释掉!)

    except Exception as e:
        print("=============================错误信息===============================\n", traceback.format_exc())
        with open('errorlog.txt', 'a+', encoding='utf-8') as fp:
            fp.write(f"{datetime.datetime.now()}报错信息:\n" + traceback.format_exc()+'\n')

    finally:
        print('\n程序名字:SeatForEXE-version20230921')
        print("技术支持:B站:吟啸徐行alter,uid:64605340,出了bug请联系我,有空就解决")
        input('按任意键退出')


if __name__ == '__main__':
    # 这个是选座的 带 激活校验 支持一个配置文件抢一个号
    main()











