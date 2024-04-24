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
    """
    用于获取本地配置文件内容
    :param address: 本地配置文件路径
    :return: 配置里面的json数据
    """
    try:
        with open(address, 'r', encoding='utf-8') as config:
            return json.load(config)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("exc_type:", exc_type)
        print("exc_value:", exc_value)
        print("exc_traceback:", exc_traceback)


def configNameCheck():
    """
    检验输入的文件名是否符合格式
    :return: 输入的,正确的,配置文件名
    """
    while True:
        num = input("请输入您要使用的配置文件名:(config1,config2或者config3):")
        if num[0:len(num) - 1] == "config" and type(eval(num[-1])) == type(1):
            print('配置文件名无误,检测成功!')
            return num
        else:
            print('配置文件名存在错误,请检查后重试!')


def expire_date(dead):
    """
    程序过期时间校验
    :param dead: 过期时间
    :return: 过期则返True
    """
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
    :return:设备信息字符串
    """
    global diskStr, cpuStr, boardStr, biosStr
    c = wmi.WMI()
    info = []

    # 硬盘序列号
    for physical_disk in c.Win32_DiskDrive():
        diskStr = physical_disk.SerialNumber
        info.append(diskStr)

    # CPU序列号
    for cpu in c.Win32_Processor():
        cpuStr = cpu.ProcessorId.strip()
        info.append(cpuStr)

    # 主板序列号
    for board_id in c.Win32_BaseBoard():
        boardStr = board_id.SerialNumber
        info.append(boardStr)

    # bios序列号
    for bios_id in c.Win32_BIOS():
        biosStr = bios_id.SerialNumber.strip()
        info.append(biosStr)

    strValue = f'{diskStr};{cpuStr};{boardStr};{biosStr}'

    return strValue


def add_to_16(value):
    """
    str不是16的倍数那就补足为16的倍数
    用于将输入的加密数据补位为16的倍数
    :param value: 待加密的明文
    :return: 处理好的待加密数据,长度为16的倍数
    """
    while len(value) % 16 != 0:
        value += '\0'
    return str.encode(value)  # 返回bytes


def decrypt_oralce(data):
    """
    解密方法
    :param data: 待解密的密文
    :return: 解密后的文本
    """
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
    """
    激活校验,检测激活后的本地初始化数据是否正确
    :return: 返回初始化信息与运行设备信息是否一致的boolean以及最终过期时间
    """
    try:
        with open('../active/initConfig.txt', 'r+', encoding='utf-8') as fp:
            initConfig = fp.read()
        # 解密初始化中的设备信息
        bdinfo = decrypt_oralce(initConfig).split(';')
        # 解读本地初始配置的设备信息
        bd = bdinfo[0] + ';' + bdinfo[1] + ';' + bdinfo[2] + ';' + bdinfo[3]

        # 解读本地初始配置的过期时间
        lastTime = bdinfo[-1]
        print(f"过期时间是:{lastTime}")

        # 获取当前设备信息
        di = getDeviceInfo()
        # 一致则返回True 和版本号
        return bd == di, lastTime
    except:
        print('验证码错误/文件出错,请检查是否正确激活,配置文件是否存在')


def test_book(url, header):
    """
    测试cookie有没有用
    :param url: 我去图书馆的url
    :param header: 请求头
    :return: 测试成功返回True
    """
    # 选座功能接口,开放接口返回的是场馆表
    data = {"operationName": "list",
            "query": "query list {\n userAuth {\n reserve {\n libs(libType: -1) {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n libGroups {\n id\n group_name\n }\n reserve {\n isRecordUser\n }\n }\n record {\n libs {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_color_name\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n }\n rule {\n signRule\n }\n }\n}"}
    response = requests.session()
    r_test = response.post(url=url, headers=header, json=data, verify=False)
    if 'errors' in r_test.json().keys():
        print(r_test.json())
        print('cookie失效,或者未正确输入!请重试!')
        return False
    print('测试成功')
    return True


def start_grabSeat(openTime):
    """
    用于倒计时
    :param openTime: 场馆开放时间,一般要提前10秒
    :return: 无
    """
    # 获取当前年月日 加上配置的时分秒，拼接成时间字符串
    ts = time.strftime("%Y-%m-%d", time.localtime(time.time()))
    openTime = ts + " " + openTime

    struct_openTime = openTime
    openTime = time.strptime(struct_openTime, "%Y-%m-%d %H:%M:%S")
    openTime = time.mktime(openTime)

    delaytime = 1
    direct = False
    while True:
        print(f'剩余时间:秒数= {openTime - time.time()}s 分数= {(openTime - time.time())//60}mins')

        # TODO 提前三秒结束粗略倒计时,并开启精确读秒倒计时
        if direct == False:
            if time.time() + 3 >= openTime:
                delaytime = 0
                direct = True

        time.sleep(delaytime)

        if time.time() >= openTime:
            print("==================================结束倒计时====================================")
            print("倒计时结束,开始提前进行抢座(场馆开放才是真正抢座,现在是提前请求场馆信息和预约信息)!")
            grab_time = time.localtime(time.time())
            ts = time.strftime("%Y-%m-%d %H:%M:%S", grab_time)
            print('当前时间是： ' + ts)
            print(f"精确到毫秒:{datetime.datetime.now()}")
            break


def bookSeat(url, header, seats_expands, openTime, bookTime, directBook):
    """
    核心功能,抢座实现
    :param directBook: 是否跳过馆室开放校验直接请求作为信息
    :param url: 我去图书馆的url
    :param header: 请求头
    :param seats_expands: 外置拓展座位
    :param openTime: 场馆开放时间
    :param bookTime: 开始挂机的时间,是时间戳
    :return: 无,仅用于停止抢座功能
    """
    # ===================================== 开始挂机======================================== #
    # 主页的请求参数
    home = {"operationName": "index",
            "query": "query index($pos: String!, $param: [hash]) {\n userAuth {\n oftenseat {\n list {\n id\n info\n lib_id\n seat_key\n status\n }\n }\n message {\n new(from: \"system\") {\n has\n from_user\n title\n num\n }\n indexMsg {\n message_id\n title\n content\n isread\n isused\n from_user\n create_time\n }\n }\n reserve {\n reserve {\n token\n status\n user_id\n user_nick\n sch_name\n lib_id\n lib_name\n lib_floor\n seat_key\n seat_name\n date\n exp_date\n exp_date_str\n validate_date\n hold_date\n diff\n diff_str\n mark_source\n isRecordUser\n isChooseSeat\n isRecord\n mistakeNum\n openTime\n threshold\n daynum\n mistakeNum\n closeTime\n timerange\n forbidQrValid\n renewTimeNext\n forbidRenewTime\n forbidWechatCancle\n }\n getSToken\n }\n currentUser {\n user_id\n user_nick\n user_mobile\n user_sex\n user_sch_id\n user_sch\n user_last_login\n user_avatar(size: MIDDLE)\n user_adate\n user_student_no\n user_student_name\n area_name\n user_deny {\n deny_deadline\n }\n sch {\n sch_id\n sch_name\n activityUrl\n isShowCommon\n isBusy\n }\n }\n }\n ad(pos: $pos, param: $param) {\n name\n pic\n url\n }\n}",
            "variables": {"pos": "App-首页"}}

    # 当前获取cookie,准备挂机!
    cookie_string = header['Cookie']

    # 使用session保持会话,运行一次抢座函数只会保持一个会话,实现存活
    response = requests.session()

    # 这里的请求头是没有cookie的,因为后面会自动携带,就不需要自己写入
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

    # 给session设置cookie
    cookie = http.cookies.SimpleCookie()
    cookie.load(cookie_string)
    for key, morsel in cookie.items():
        response.cookies.set(key, morsel)

    # 用于将挂机方式的时间转化成时间戳
    ts = time.strftime("%Y-%m-%d", bookTime)
    # 这个是将预约时间和开放时间拼接后的时间
    openTime0 = ts + " " + openTime
    struct_openTime = openTime0
    # 这个是开放时间的格式化
    openTime1 = time.strptime(struct_openTime, "%Y-%m-%d %H:%M:%S")
    # 这个就是开放时间的时间戳
    openTime2 = time.mktime(openTime1)

    # 如果不是因为重刷session执行这个函数,就表示是正常的挂机或者断线,那么就要执行下面的这个分支
    if not directBook:
        print('\n==================================开始挂机=========================================')
        # 保持cookie活性,检测当前当前挂机剩余时间,如果开放时间减去剩余时间小于180秒(3分钟),则结束挂机,将进入倒计时
        # 初始化新的cookie
        nowCookie = None
        while True:
            print(f'剩余时间:{(openTime2 - time.time()) // 60}分钟')
            # 取整
            intoCountTimes = (openTime2 - time.time()) // 1

            # 4分钟到5分钟随机更新一次会话
            sleep = random.uniform(240, 300)
            # 最后五分钟进入倒计时
            if intoCountTimes < sleep:
                print(
                    f'==============离开放还剩{intoCountTimes // 60}分钟左右,挂机结束!开始进入倒计时=====================')
                with open('intoCountTimeLogs.txt', 'w+', encoding='utf-8') as fp:
                    fp.write(f'当前时间为:{datetime.datetime.now()},\n'
                             f'openTime:{openTime2 // 1}  ==>  对应的时间为:{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(openTime2 // 1))},\n'
                             f'time:{time.time() // 1}  ==>  对应的时间为:{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() // 1))},\n'
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
                print("Error挂机时出了bug,由于返回数据有异常！！！: %s" % err)
                # 打印导致解码错误的源文本,
                print("返回数据异常的内容.text:"+res.text)
                # 将错误写入日志中
                with open('errorlog.txt', 'a+', encoding='utf-8') as fp:
                    fp.write(f"{datetime.datetime.now()}报错信息:\n" + traceback.format_exc() + '\n'+'返回数据异常的内容:'+res.text+'\n')
                # 休眠十分钟,再进行尝试
                time.sleep(600)
                continue
            if result.get("errors") and result.get("errors")[0].get("code") != 0:
                print("Session expired!,请重新扫码!")
                return

            print("Session OK.")
            print("响应信息:", result)
            # 拼接新的cookie字符串
            Adict = {}
            for key, morsel in response.cookies.items():
                Adict[key] = morsel
                break
            # 判断返回的cookie字段中是否含有叫做 "Authorization"的key
            if 'Authorization' in Adict.keys():
                nowCookie = "Authorization" + "=" + Adict["Authorization"]
            # nowCookie已经设置了None,所以就算没有也不会怎么样
            if nowCookie == cookie_string:
                print("cookie未变:")
                print(nowCookie)
            # 新的cookie必须与旧的不一样而且还不能为空
            if nowCookie != cookie_string and nowCookie is not None:
                print("cookie已变!,当前为:")
                # 重置初始cookie,用于判断下次是否为新的
                cookie_string = nowCookie
                print(nowCookie)
                with open('newCookie.txt', 'w', encoding='utf-8') as fp:
                    #  这里的 "更新的cookie为:" 这一段不要改,特别是 : 号,我用来断线的时候分割出cookie用的
                    fp.write(f"{datetime.datetime.now()}更新的cookie为:" + nowCookie)
                    print('已保存本次的新的cookie')
                    
                # TODO 因为更新的新曲奇可以撑住起码两个小时,所以如果更新了,就设置延迟一小时以上
                # 如果剩余时间比随机间隔时间大,就可以执行间隔长点
                if intoCountTimes > 3600:
                    sleep = random.uniform(1800, 3600)
                    
            # 随即间隔时间打印当前cookie
            print("当前时间:", datetime.datetime.now())


            print(f"本次随机间隔时间为:{sleep//1}秒,大约{sleep //1 / 60}分钟左右\n")
            time.sleep(sleep)


    # ==============================================进入倒计时=============================================================================
    start_grabSeat(openTime)
    # 抢座真正开始时间，这个算是总时间，不过常用抢座就用自己独有的一套时间
    startTime = time.time()
    # ========================如果座位所在场馆未满,且座位未被选,则添加到列表中;如果说列表为空,则说明两个座位都没法选=========================
    print("\n====================================开始请求常用座位==========================================")
    # 初始两个常用座位
    ofseats = 2
    # 初始化座位请求参数
    ofseat = None

    while True:
        if ofseats <= 0:
            print("没有常用座位可以用,结束常用请求!")
            break
        """
        常用这里我有一些顾忌,担心就算掐点了也被被人选了,出现空闲,但是未选上,所以直接创建一个新的session,,这样就算常用出了问题,也不用等0.75秒重刷session
        """
        # 常用抢座的时间
        ofstartTime = time.time()


        # 主页常用座位状态 0为空闲 1为被选 查询场馆是否还有剩余位置 num>=0 表示场馆还未满
        responseOftenSeats = response.post(url=url, json=home, verify=False).json()
        # 这个是开馆后的请求返回的常用座位信息列表
        AfteroftenseatsList = responseOftenSeats['data']['userAuth']['oftenseat']['list']

        # 开馆之后看一下座位在不在,不在去选
        for seat in AfteroftenseatsList:
            # 状态是1表示被选,0是未选 如果是已选就跳过去查下一个
            # 开放时间比
            if seat['status'] == 0:
                # 没被选就设置好座位
                print(seat['info'] + f'没被选，状态码：{seat["status"]}')
                # 获取座位的场馆id和key
                key = seat['seat_key']
                libid = seat['lib_id']
                # 这个是直接在主页选常用座位的接口,是最快地抢座方式
                seat = {"operationName": "reserveSeat",
                        "query": "mutation reserveSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserveSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}",
                        "variables": {"seatKey": key, "libId": libid, "captchaCode": "", "captcha": ""}}
                # 设置ofseat为有一个座位是空闲状态
                ofseat = seat
                break

            print(seat['info'] + f'被选，状态码：{seat["status"]}')
            ofseats -= 1
            continue

        # 如果有常用可以用
        if ofseats > 0 and ofseat is not None:
            # 先进行选座
            r = response.post(url=url, json=ofseat, verify=False)
            r_json = r.json()

            #再进行查询
            responseOftenSeats = response.post(url=url, json=home, verify=False).json()
            responseInfo = responseOftenSeats['data']['userAuth']['reserve']['reserve']

            # 判断请求是否通过 reserveSeat
            if r_json['data']['userAuth']['reserve']['reserveSeat'] and responseInfo is not None:
                # 如果返回的是True,则选座成功
                print(f'\n====座位{ofseat["variables"]["seatKey"]}号通过请求===\n'
                      f'抢座成功!\n'
                      f'请求的状态:{r.status_code}\n'
                      f'响应的内容:{r_json}\n'
                      f'响应用时:{r.elapsed.total_seconds()}\n'
                      f'座位信息和时间:{datetime.datetime.now()}\n'
                      f'用户信息:{responseInfo["user_nick"]} 馆室:{responseInfo["lib_name"]} 座位号:{responseInfo["seat_name"]}\n'
                      f'====座位{ofseat["variables"]["seatKey"]}号通过请求===\n')
                print(f"本次抢座从场馆开放到选上常用座位用时{time.time() - ofstartTime}s")
                return
            # 否则就打印错误信息
            print(f'请求的状态:{r.status_code}\n'
                  f'响应的内容:{r_json}\n'
                  f'响应用时:{r.elapsed.total_seconds()}\n'
                  f'座位信息和时间:{datetime.datetime.now()}')
            print('抛出异常并重新刷新session')
            raise ConnectionError("选座请求异常!")


    # ===================================外置座位选座======================================================================================
    print("\n===================================外置座位选座=============================================")
    # 用于判断是否存在外置座位,以及常用是否不可用
    if len(seats_expands) == 0:
        print("没有外置座位!")

    if len(seats_expands) > 0 and ofseats == 0:
        # 剩余外置座位数
        amount = len(seats_expands)
        # 初始化data（座位参数）
        dataFree = None
        # 设置座位状态，用于跳出馆室循环
        free = None
        # 循环遍历每个座位对应的场馆
        for data in seats_expands:

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
                print(f'\n {libName}场馆剩余数:', seatsFree,
                      " 这里的剩余座位数因为包括了一些没有名字的座位比如沙发,所以请以抢到的座位为准!")

                if seatsFree <= 0:
                    print(f"{libName}场馆已满")
                    # 剔除场馆满了的馆室
                    amount -= 1
                    continue

                # 如果场馆没满则获取场馆所有座位
                seatsList = seatsInfo['seats']

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
        # 判断data 参数是否非空,座位是否空闲
        if free == True and dataFree is not None:
            # 先进行选座
            time.sleep(random.uniform(0.1, 0.2))
            r = response.post(url=url, json=dataFree, verify=False)
            r_json = r.json()

            #再进行查询
            responseOftenSeats = response.post(url=url, json=home, verify=False).json()
            responseInfo = responseOftenSeats['data']['userAuth']['reserve']['reserve']

            # 判断请求是否通过
            if r_json['data']['userAuth']['reserve']['reserueSeat'] and responseInfo is not None:  # 如果返回的是True
                print(f'====外置座位{dataFree["variables"]["seatKey"]}号通过请求===\n'
                      f'外置抢座成功!\n'
                      f'请求的状态:{r.status_code}\n'
                      f'响应的内容:{r_json}\n'
                      f'抢座用时:{r.elapsed.total_seconds()}\n'
                      f'座位信息和时间:{datetime.datetime.now()}\n'
                      f'用户信息:{responseInfo["user_nick"]} 馆室:{responseInfo["lib_name"]} 座位号:{responseInfo["seat_name"]}\n'
                      f'====外置座位{dataFree["variables"]["seatKey"]}号通过请求===\n')
                print(f"本次抢座从场馆开放到选上外置座位用时{time.time() - startTime}s")
                return

            print(f'外置座位{dataFree["variables"]["seatKey"]}号请求的状态:{r.status_code}\n'
                  f'响应的内容:{r_json}\n'
                  f'抢座用时:{r.elapsed.total_seconds()}\n'
                  f'座位信息和时间:{datetime.datetime.now()}\n'
                  f'座位{dataFree["variables"]["seatKey"]}号')
            print('抛出异常并重新刷新session')
            raise ConnectionError("选座请求异常!")

    # =================================两个常用以及外置座位 都选不上,就轰炸两个常用座位对应的场馆======================================================
    print('\n==============所有自定义座位都没选上,进入常用馆室轰炸模式(有空闲就选)!==================')
    # 遍历常用座位所在的场馆,获取场馆信息
    num = 1  # 计数器，用于计算是第几次请求
    # 从常用的两个场馆去轰炸
    oftenseatsList = responseOftenSeats['data']['userAuth']['oftenseat']['list']  # 常用座位列表
    for i in [0, 1]:
        # 从常用中获取场馆id,info
        libid = oftenseatsList[i]["lib_id"]
        libName = oftenseatsList[i]["info"].split(' ')[0]
        print("\n场馆id:", libid, ",场馆名字:", libName)

        # 获取场馆信息的请求参数
        libInfo = {"operationName": "libLayout",
                   "query": "query libLayout($libId: Int, $libType: Int) {\n userAuth {\n reserve {\n libs(libType: $libType, libId: $libId) {\n lib_id\n is_open\n lib_floor\n lib_name\n lib_type\n lib_layout {\n seats_total\n seats_booking\n seats_used\n max_x\n max_y\n seats {\n x\n y\n key\n type\n name\n seat_status\n status\n }\n }\n }\n }\n }\n}",
                   "variables": {"libId": libid}}

        # 模拟 选择场馆 按钮请求
        lib = response.post(url=url, json=libInfo, verify=False).json()
        seatsInfo = lib['data']['userAuth']['reserve']['libs'][0]['lib_layout']
        seatsFree = seatsInfo['seats_total'] - seatsInfo['seats_used']
        print('剩余数:', seatsFree, " 这里的剩余座位数因为包括了一些没有名字的座位比如沙发,所以请以抢到的座位为准!")
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
            seatStatus = seat['seat_status']  # 状态为1表示没被选, 3是被选
            status = seat['status']  # False表示未被选, True表示被选
            Type = seat['type']  # type=1 是表示座位正常的,其他都是不正常

            # 如果座位没问题,就发送请求
            if seatStatus == 1 and status == False and Type == 1 and seatName is not None:
                # 常用座位的key
                key = seat['key']
                data = {"operationName": "reserueSeat",
                        "query": "mutation reserueSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserueSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}",
                        "variables": {"seatKey": key, "libId": libid, "captchaCode": "", "captcha": ""}}
                # 这个是直接在主页选常用座位的接口,是最快地抢座方式
                # data = {"operationName": "reserveSeat",
                #         "query": "mutation reserveSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserveSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}",
                #         "variables": {"seatKey": key, "libId": libid, "captchaCode": "", "captcha": ""}}

                # 先发送选座请求
                print(f'场馆{libName}发送第{num}次请求')
                time.sleep(random.uniform(0.1, 0.2))
                r = response.post(url=url, json=data, verify=False)
                r_json = r.json()

                # 再进行查询
                responseOftenSeats = response.post(url=url, json=home, verify=False).json()
                responseInfo = responseOftenSeats['data']['userAuth']['reserve']['reserve']

                # 判断请求是否通过
                if r_json['data']['userAuth']['reserve']['reserueSeat'] and responseInfo is not None:  # 如果返回的是True
                    print(f'===={libName}座位{seatName}号通过请求和信息查询===\n'
                          f'{libName}座位{seatName}号抢座成功!\n'
                          f'请求的状态:{r.status_code}\n'
                          f'响应的内容:{r_json}\n'
                          f'抢座用时:{r.elapsed.total_seconds()}\n'
                          f'座位信息和时间:{datetime.datetime.now()}\n'
                          f'用户信息:{responseInfo["user_nick"]} 馆室:{responseInfo["lib_name"]} 座位号:{responseInfo["seat_name"]}\n'
                          f'====座位{libName}{seatName}号   通过  请求和信息查询===\n')
                    print(f"本次抢座从场馆开放到选上轰炸座位用时{time.time() - startTime}s")
                    return

                # 如果返回的内容有 "刷" or "被',那么多半无了,直接退出程序
                if r.text.find('u5c1d') != -1 or r.text.find('u5237') != -1:
                    print(f'===={libName}座位{seatName}号请求异常的信息===\n'
                          f'{libName}座位{seatName}号抢座失败!\n'
                          f'请求的状态:{r.status_code}\n'
                          f'响应的内容:{r_json}\n'
                          f'抢座用时:{r.elapsed.total_seconds()}\n'
                          f'座位信息和时间:{datetime.datetime.now()}\n'
                          f'====座位{libName}{seatName}号请求异常的信息===\n')
                    print('抛出异常并重新刷新session')
                    raise ConnectionError("选座请求异常!")

                # 其他错误  打印错误信息
                print(f'===={libName}座位{seatName}号 请求异常===\n'
                      f'{libName}座位{seatName}号 请求异常的信息!\n'
                      f'请求的状态:{r.status_code}\n'
                      f'响应的内容:{r_json}\n'
                      f'抢座用时:{r.elapsed.total_seconds()}\n'
                      f'座位信息和时间:{datetime.datetime.now()}\n'
                      f'===={libName}座位{seatName}号 请求异常===\n')
                print('抛出异常并重新刷新session')
                raise ConnectionError("选座请求异常!")


def oneTread(url, header, seats_expand, openTime, bookTime):
    """
    抢座位主程序启动器,可以断线重连
    :param url: 我去图书馆ur
    :param header: 请求头
    :param seats_expand: 外置座位
    :param openTime: 场馆开放时间
    :param bookTime: 启动方式(今天做or挂机到明天选),传入的值是"todayTime"或者"tomorrowTime"
    :return: 无
    """
    # 短线的次数
    num = 1
    # 重刷session的次数
    sessioncounts = 1
    # 接收第一次扫码的header,里面存了第一次的cookie
    newheader = header
    # 用来判断是不是选座异常所导致的选座失败
    directBook = False
    # 为了重连之后能使用最新的倒计时间,这里先用newbookTime中转一下
    newbookTime = None  # 第一次的时间跟用户设置的一样
    # 初始化程序启动时间
    programStartTime = None
    # 获取用户输入的先要如何启动的方式的 完整年月日
    if bookTime == "todayTime":
        # 这个是今天的年月日,适用于明天,或者当晚0点之后启动挂机
        newbookTime = time.localtime(time.time())
        programStartTime = datetime.datetime.now().date()

    if bookTime == "tomorrowTime":
        # 这个是明天的年月日,适用于今天在0点前启动挂机
        newbookTime = time.localtime(time.time() + 86400)
        programStartTime = datetime.datetime.now().date()

    # 接收用户传入的启动方式,这里用中转的方式保留用户第一次输入的启动方式,后续断线只需要更改这个变量即可
    newTime = newbookTime
    while True:
        startTime = time.time()  # 获取主线程开始时间
        # 刷新或者重连10次自动退出
        if num <= 11 and sessioncounts <= 11:
            try:
                bookSeat(url, newheader, seats_expand, openTime, newTime, directBook)
                break
            except requests.exceptions.RequestException:
                print("=============================错误信息===============================\n", traceback.format_exc())
                print(f'准备重新建立选座连接:第{num}次重连......')
                # 出了断线情况,如果时间超过了1个小时则自动读取最新的cookie,否则用老的cookie
                if time.time() - startTime > 3600:
                    print('加载新的cookie中...')
                    with open("newCookie.txt", 'r+', encoding='utf-8') as fp:
                        data = fp.read()
                        if data is not None:
                            newcookie = data.split(':')[-1]
                            newheader['Cookie'] = newcookie

                            # 判断当前断线 日期 ,与挂机启动的 日期 是否一致
                            nowTime = datetime.datetime.now().date()
                            # 如果断线日期与用户启动程序的日期一致,并且用户输入的就是想要明日自动选,就自动将bookTime改为 "tomorrowTime"的对应时间
                            if nowTime == programStartTime and bookTime == "tomorrowTime":
                                newTime = time.localtime(time.time() + 86400)
                            # 如果断线时间与用户启动程序的日期不一致(就是加了一天,即断线出现在第二天早上),并且用户输入的就是想要明日自动选,那就改成 "todayTime"的对应时间
                            if nowTime != programStartTime and bookTime == "tomorrowTime":
                                newTime = time.localtime(time.time())
                            # 如果断线时间与用户启动程序的日期一致(就是加了一天,即断线出现在第二天早上),并且用户输入的就是想要今日自动选,那就改成 "todayTime"的对应时间
                            if nowTime == programStartTime and bookTime == "todayTime":
                                newTime = time.localtime(time.time())

                            print('加载完成,已经设置最新的cookie')
                num += 1
                time.sleep(3)  # 休眠3秒再重连

            except ConnectionError as e:
                print("=============================错误信息===============================\n", traceback.format_exc())
                print(
                    f'准备第{sessioncounts}次重新刷新session(这里如果是第11次就不用管了,不会再刷了其实,懒得改就这样子)')
                # 出了断线情况,如果时间超过了1个小时则自动读取最新的cookie,否则用老的cookie
                if time.time() - startTime > 3600:
                    print('加载新的cookie中...')
                    with open("newCookie.txt", 'r+', encoding='utf-8') as fp:
                        data = fp.read()
                        if data is not None:
                            newcookie = data.split(':')[-1]
                            newheader['Cookie'] = newcookie

                            # 判断当前断线 日期 ,与挂机启动的 日期 是否一致
                            nowTime = datetime.datetime.now().date()
                            # 如果断线日期与用户启动程序的日期一致,并且用户输入的就是想要明日自动选,就自动将bookTime改为 "tomorrowTime"的对应时间
                            if nowTime == programStartTime and bookTime == "tomorrowTime":
                                newTime = time.localtime(time.time() + 86400)
                            # 如果断线时间与用户启动程序的日期不一致(就是加了一天,即断线出现在第二天早上),并且用户输入的就是想要明日自动选,那就改成 "todayTime"的对应时间
                            if nowTime != programStartTime and bookTime == "tomorrowTime":
                                newTime = time.localtime(time.time())
                            # 如果断线时间与用户启动程序的日期一致(就是加了一天,即断线出现在第二天早上),并且用户输入的就是想要今日自动选,那就改成 "todayTime"的对应时间
                            if nowTime == programStartTime and bookTime == "todayTime":
                                newTime = time.localtime(time.time())
                if str(e).find("u5c1d") or str(e).find("u5237"):
                    # 表示是因为开馆后座位因为未知原因显示"请重试刷新,尝试或者已被预订"之类的问题,这时候重连只需要直接进入抢座就行,省去前面的繁琐步骤
                    directBook = True
                    print('刷新成功!')
                print(
                    '=================================已经重刷了session,即将重新选座!==============================\n')
                # 重刷必须设置至少这么久的延迟,否则重刷不成功,切记不要再改小!
                time.sleep(0.75)
                sessioncounts += 1

        else:
            print(
                '"断线重连/重刷session" 已经尝试10次,不再  重连/重刷session,请检查网络(重刷问题可能是程序逻辑,反馈开发者)是否存在问题!!!!!!!! ')
            break


def main():
    """
    主程序入口
    :return:
    """
    try:
        # 返回值是元组,第一个元素是设备信息,第二个元素是版本号,第三个元素是过期时间
        active = activeCheck()
        # 1-激活校验
        if not active[0]:
            print('未激活,请激活后重试')
            return

        # 2-过期时间校验
        lastTime = active[1]

        if expire_date(lastTime):  # 设置过期时间
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
        configSet = getConfig(f"../config02/config.json")  # 导入配置
        print('配置初始化成功！')

        # 初始化外置座位列表,提前加载到列表,传参到核心程序
        expand_seats = []
        print('\n==========================准备启用外置座位配置===============================================')
        seats_expand = configSet.get('map_seats')
        for seat0 in seats_expand:
            libid = seats_expand[seat0]['libId']
            key = seats_expand[seat0]['seatKey']
            # 这个是在场馆里选座的请求参数
            # seat = {"operationName": "reserueSeat",
            #         "query": "mutation reserueSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserueSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}",
            #         "variables": {"seatKey": key, "libId": libid, "captchaCode": "", "captcha": ""}}

            # 这个是直接在主页选常用座位的接口,是最快地抢座方式,因为上面那个在开馆时候有问题我就不用了
            seat = {"operationName": "reserveSeat",
                    "query": "mutation reserveSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserveSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}",
                    "variables": {"seatKey": key, "libId": libid, "captchaCode": "", "captcha": ""}}

            # 将外置座位打包成json参数需要的值,添加到外置座位列表中
            expand_seats.append(seat)
            print(f"外置座位{seat0}信息:{seats_expand[seat0]}")
        print(f'外置座位添加成功！个数:{len(expand_seats)}\n')

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

        # 开始抢座
        oneTread(url=configSet.get('url'),
                 header=configSet.get('header'),
                 seats_expand=expand_seats,
                 openTime=configSet.get('openTime'),
                 bookTime=bookTime)

    except Exception:
        print("=============================错误信息===============================\n", traceback.format_exc())
        with open('errorlog.txt', 'a+', encoding='utf-8') as fp:
            fp.write(f"{datetime.datetime.now()}报错信息:\n" + traceback.format_exc() + '\n')

    finally:
        print('\n程序名字:SeatForEXE-version20230923')
        print("技术支持:B站:吟啸徐行alter,uid:64605340,出了bug请联系我,有空就解决")
        input('按任意键退出')


if __name__ == '__main__':
    main()

