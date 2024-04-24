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
import websocket
import wmi
import http.cookies
import http.cookiejar
from Crypto.Cipher import AES

# 捕捉极速模式下的json解码bug使用全局变量


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
        bd = bdinfo[0]+';'+bdinfo[1]+';'+bdinfo[2]+';'+bdinfo[3]

        # 解读本地初始配置的过期时间
        lastTime = bdinfo[-1]
        print(f"过期时间是:{lastTime}")
        # 获取当前设备信息
        di = getDeviceInfo()
        # 一致则返回True 和版本号
        return bd == di, lastTime
    except:
        print('验证码错误/文件出错,请检查是否正确激活,配置文件是否存在')


def start_grabSeat(openTime):
    """
    用于倒计时
    :param openTime: 场馆开放时间,一般要提前10秒
    :return: 无
    """
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
        # 考虑到建立websocket连接需要一定时间,提前6秒结束倒计时,然后先建立连接,再开始去排队轰炸
        if time.time() + 10 >= openTime:
            print("==================================提前6秒结束结束倒计时,即将建立ws连接====================================")
            print("倒计时结束,开始提前进行抢座(场馆开放才是真正抢座,现在是提前请求场馆信息和预约信息)!")
            grab_time = time.localtime(time.time())
            ts = time.strftime("%Y-%m-%d %H:%M:%S", grab_time)
            print('当前时间是： ' + ts)
            break


def queue_together(queue_header,openTime,threadName=''):
    """
    这个是可以带排队请求头的同步排队
    :param openTime: 开放时间
    :param queue_header:
    :param threadName:
    :return:
    """
    print("================================")
    print("--------------开始排队 - ---------------------")
    # 获取当前年月日 加上配置的时分秒，拼接成时间字符串
    ts = time.strftime("%Y-%m-%d", time.localtime(time.time()))
    openTime = ts + " " + openTime
    struct_openTime = openTime
    openTime = time.strptime(struct_openTime, "%Y-%m-%d %H:%M:%S")
    openTime = time.mktime(openTime)

    ws = websocket.WebSocket()
    # ws.connect("wss://wechat.**.com/ws?ns=prereserve/queue", header=headers)
    ws.connect("wss://wechat.v2.traceint.com/ws?ns=prereserve/queue", header=queue_header)
    if ws.connected:
        ws.send('{"ns":"prereserve/queue","msg":""}')
        rank = ws.recv()
        print(threadName+'连接成功!',datetime.datetime.now())
        print("rsp msg:{}".format(json.loads(rank)))

        print("建立连接后,等待到最后2秒开始启动,现在正在等待中......")
        while True:
            if time.time() > openTime - 2:
                print("等待完毕.开始ws请求")
                break


        # 先用来计数排队轰炸次数
        n = 1


        while True:
            # 当前时间比开放时间小,大概在这个时间范围内(准点前0.005秒,这个秒后面隔两次请求就是),可以进入明日预约
            if time.time() <= openTime-0.004:
                # 这里是请求轰炸,先排队再说,不管别的
                ws.send('{"ns":"prereserve/queue","msg":""}')
                print(f"No.{n}排队轰炸中......")
                n += 1
                continue

            print(f"轰炸结束时间:{datetime.datetime.now()}")
            print(f"\n===============排队轰炸结束,进入排队结果检测(为了高速舍弃了排名,后面如果出现了data并不是真实的排名)==============\n")
            break

        # 检测时重置n,下面的循环用来检测到开放点后是否排上了队
        n = 1
        # 用于使得循环中的data判断只执行一次就终止
        run = False
        # 捕获的第一次data不为0时候data的值,即排名
        rank = None
        while True:
            ws.send('{"ns":"prereserve/queue","msg":""}')
            a = ws.recv()

            jrsp = json.loads(a)

            # 获取第一次data不为0时候的数据,即排名
            # 这里多一次key判断,因为请求太快会出现keyError找不到data
            if "data" in jrsp:
                if jrsp["data"] != 0 and run == False:
                    run = True
                    rank = jrsp["data"]
                    print(f"当前时间的时间戳是:{time.time()}\n标准时间:{datetime.datetime.now()}")
                    
            if "code" in jrsp:
                if jrsp["code"] == 1000:
                    print("获取用户信息失败,即将重刷session")
                    raise ConnectionError("选座请求异常!")

            # msg里的原生数据是unicode码
            if a.find('u6392') != -1:  # '排'队成功返回的第一个字符(找不到返回-1)
                print("rsp msg:{}".format(jrsp))
                break
            if a.find('u6210') != -1:  # 已经抢座'成'功的返回
                print("rsp msg:{}".format(jrsp))
                break

            print(f"No.{n}检测座位中，rsp:{jrsp}")
            n += 1
        # 关闭连接
        ws.close()
        print(f"排队结束,你的排名可能是:{rank},(如果第一次检测座位出现 不在预约时间 的字样,那么排名准确;如果没有,也具有较大参考价值,不会相差很多)")
    print("==============排队结束,开始选座==================")


def bookSeat(url, header,seats_expands,openTime, bookTime, directBook):
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

    # 如果不是因为重刷session执行这个函数,就表示是正常的挂机或者断线,那么就要执行下面的这个分支
    if not directBook:
        print('\n==================================开始挂机=========================================')
        # 用于将挂机方式的时间转化成时间戳
        ts = time.strftime("%Y-%m-%d", bookTime)
        openTime0 = ts+" "+openTime
        struct_openTime = openTime0
        openTime1 = time.strptime(struct_openTime, "%Y-%m-%d %H:%M:%S")
        openTime2 = time.mktime(openTime1)

        # 保持cookie活性,检测当前当前挂机剩余时间,如果开放时间减去剩余时间小于180秒(3分钟),则结束挂机,将进入倒计时
        # 初始化新的cookie
        nowCookie = None
        while True:
            print(f'剩余时间:{(openTime2 - time.time())//60}分钟')
            # 取整
            intoCountTimes = (openTime2 - time.time())//1
            # 最后五分钟进入倒计时
            if intoCountTimes < 300.0:
                print(f'==============离开放还剩{intoCountTimes//60}分钟左右,挂机结束!开始进入倒计时=====================')
                with open('intoCountTimeLogs.txt', 'w+', encoding='utf-8') as fp:
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
                print("Error场馆请求时出了bug,由于返回数据有异常！！！: %s" % err)
                # 打印导致解码错误的源文本,
                print("返回数据异常的内容.text:" + res.text)
                # 将错误写入日志中
                with open('errorlog.txt', 'a+', encoding='utf-8') as fp:
                    fp.write(
                        f"{datetime.datetime.now()}报错信息:\n" + traceback.format_exc() + '\n' + '返回数据异常的内容:' + res.text + '\n')
                raise ConnectionError("选座请求异常!")

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
                print("cookie已变,当前为:")
                # 重置初始cookie,用于判断下次是否为新的
                cookie_string = nowCookie
                print(nowCookie)
                with open('newCookie.txt', 'w', encoding='utf-8') as fp:
                    #  这里的 "更新的cookie为:" 这一段不要改,特别是 : 号,我用来断线的时候分割出cookie用的
                    fp.write(f"{datetime.datetime.now()}更新的cookie为:"+nowCookie)
                    print('已保存本次的新的cookie')
            # 随即间隔时间打印当前cookie
            print("当前时间:", datetime.datetime.now())
            # 一分钟到三分钟随机更新一次会话
            sleep = random.uniform(60, 180)
            print(f"本次随机间隔时间为{sleep//1}秒左右\n")
            time.sleep(sleep)

    # ==============================================进入倒计时=====================================
        # 进入倒计时,但是提前十秒放开去查询场馆是否开放
        start_grabSeat(openTime)
        pass

    # =========================倒计时结束,开始排队=====================================================
    queue_header = {
        "Host": "wechat.v2.traceint.com",
        "Connection": "Upgrade",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090621) XWEB/8391 Flue",
        "Upgrade": "websocket",
        "Origin": "https://web.traceint.com",
        "Sec-WebSocket-Version": "13",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh",
        "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
        "Cookie": cookie_string
    }
    queue_together(queue_header,openTime)

# ========================如果座位所在场馆未满,且座位未被选,则添加到列表中;如果说列表为空,则说明两个座位都没法选=========================   #
    # 抢座真正开始时间
    startTime = time.time()

    print("\n====================================开始请求常用座位==========================================")
    # 查询是否预约的接口
    info = {"operationName":"prereserve","query":"query prereserve {\n userAuth {\n prereserve {\n prereserve {\n day\n lib_id\n seat_key\n seat_name\n is_used\n user_mobile\n id\n lib_name\n }\n }\n }\n}"}
    # 进入明日预约后查询  常用座位  以及  所有场馆  状态的接口
    oftenseats = {"operationName":"index","query":"query index {\n userAuth {\n user {\n prereserveAuto: getSchConfig(extra: true, fields: \"prereserve.auto\")\n }\n currentUser {\n sch {\n isShowCommon\n }\n }\n prereserve {\n libs {\n is_open\n lib_floor\n lib_group_id\n lib_id\n lib_name\n num\n seats_total\n }\n }\n oftenseat {\n prereserveList {\n id\n info\n lib_id\n seat_key\n status\n }\n }\n }\n}"}

    # 如果座位所在场馆未满,且座位未被选,则添加到列表中;如果说列表为空,则说明两个座位都没法选
    ofseat = None

    # 默认False,只有在第一次directBook为False时候会被设置成True,跳过繁琐的常用场馆状态请求
    skip = False

    # 第一次运行到这里使用极速模式抢一号位置
    if not directBook:
        print("这是第一次请求,即将判断是否开启极速模式!(如果后面没有显示开启了极速就是没开)")
        # TODO 针对一些会卡顿的学校,如果拍完队出现卡顿超过1.3秒,就直接归类到自动重刷
        firstRequest = response.post(url=url, json=oftenseats, verify=False, timeout=1.3)
        responseOftenSeats = firstRequest.json()
        firstSeat = responseOftenSeats['data']['userAuth']['oftenseat']['prereserveList'][0]
        if firstSeat['status'] == 0:
            print(firstSeat['info']+'是空闲状态,首次选座请求将使用极速模式对常用一号座位进行选座!!!')
            key = firstSeat['seat_key']
            libid = firstSeat['lib_id']
            seat = {"operationName": "save",
                    "query": "mutation save($key: String!, $libid: Int!, $captchaCode: String, $captcha: String) {\n userAuth {\n prereserve {\n save(key: $key, libId: $libid, captcha: $captcha, captchaCode: $captchaCode)\n }\n }\n}",
                    "variables": {"key": key + '.', "libid": libid, "captchaCode": "", "captcha": ""}}
            ofseat = seat
            skip = True

    # 重刷或者一号位已被选则正常进行一二号位置状态请求
    if skip == False:
        # 第二步:查询常用座位状态( 0为空闲 1为被选 查询场馆是否还有剩余位置 num>0 表示场馆还未满)
        # TODO 针对一些会卡顿的学校,如果拍完队出现卡顿超过1.3秒,就直接归类到自动重刷
        responseOftenSeats = response.post(url=url, json=oftenseats, verify=False, timeout=1.3).json()
        oftenseatsList = responseOftenSeats['data']['userAuth']['oftenseat']['prereserveList']
        libs = responseOftenSeats['data']['userAuth']['prereserve']['libs']

        for seat in oftenseatsList:
            # 表示已经查到了一个能用的座位了,那就直接退出执行下一步选常用
            if ofseat is not None:
                break
            # 先去查询常用的状态
            if seat['status'] == 0:
                print(seat['info']+'是空闲状态')
                key = seat['seat_key']
                libid = seat['lib_id']
                # 查询场馆是否满人 TODO 这里改成先去找到场馆的下标查,不要用循环,但是没开明日预约之前怎么知道场馆数据的下标呢???
                for lib in libs:
                    # 场馆id符合and 场馆剩余位置数量不为0
                    if lib['lib_id'] == libid and lib['num'] != 0:
                        # TODO 记得看这个是不是常用的选坐接口
                        seat = {"operationName": "save",
                                "query": "mutation save($key: String!, $libid: Int!, $captchaCode: String, $captcha: String) {\n userAuth {\n prereserve {\n save(key: $key, libId: $libid, captcha: $captcha, captchaCode: $captchaCode)\n }\n }\n}",
                                "variables": {"key": key+'.', "libid": libid, "captchaCode": "", "captcha": ""}}
                        ofseat = seat
                        print(lib['lib_name']+'场馆还未满')
                        break

                    # 场馆id符合 and 场馆剩余位置数量等于0
                    if lib['lib_id'] == libid and lib['num'] == 0:
                        print(lib['lib_name']+'场馆已满')
                        break
            else:
                print(seat['info']+'已经被占用状态')

# ===================================常用座位选座=============================================
    # 如果有常用可以用
    if ofseat is not None:
        #  发送一个 开始预约 的请求=========这两步非常关键,会影响能否正常抢到常用
        libid = ofseat['variables']['libid']
        libInfo = {"operationName": "libLayout",
                   "query": "query libLayout($libId: Int!) {\n userAuth {\n prereserve {\n libLayout(libId: $libId) {\n max_x\n max_y\n seats_booking\n seats_total\n seats_used\n seats {\n key\n name\n seat_status\n status\n type\n x\n y\n }\n }\n }\n }\n}",
                   "variables": {"libId": libid}}
        # 模拟开始预约按钮请求,设置超时时间
        response.post(url=url, json=libInfo, verify=False,timeout=1.3)

        r = response.post(url=url, json=ofseat, verify=False,timeout=1.3)
        r_json = r.json()

        # 再发送座位信息查询请求
        r2 = response.post(url=url, json=info, verify=False)  # 发起请求查询是否抢座成功
        r2_json = r2.json()

        # 判断请求是否通过
        if r_json['data']['userAuth']['prereserve']['save']:  # 如果返回的是True
            if r2_json['data']['userAuth']['prereserve']['prereserve'] is not None:  # 查询选座状态，不是None就是成功了
                print(f'\n====座位{ofseat["variables"]["key"]}号通过请求和信息查询===\n'
                      f'抢座成功!\n'
                      f'请求的状态:{r.status_code}\n'
                      f'响应的内容:{r_json}\n'
                      f'座位信息和时间:{datetime.datetime.now()}\n'
                      f'请求的状态:{r2.status_code}\n'
                      f'响应的内容:{r2_json}\n'
                      f'====座位{ofseat["variables"]["key"]}号   通过  请求和信息查询===\n')
                print(f"本次抢座从场馆开放到选上常用座位用时{time.time()-startTime}s")
                return

        # 否则就打印错误信息
        print(f'\n====座位{ofseat["variables"]["key"]}号 请求异常===\n'
              f' 请求异常的信息!\n'
              f'请求的状态:{r.status_code}\n'
              f'响应的内容:{r_json}\n'
              f'抢座用时:{r.elapsed.total_seconds()}\n'
              f'请求的状态:{r2.status_code}\n'
              f'响应的内容:{r2_json}\n'
              f'座位信息和时间:{datetime.datetime.now()}\n'
              f'====座位{ofseat["variables"]["key"]}号 请求异常===\n')
        print('抛出异常并重新刷新session')
        raise ConnectionError("选座请求异常!")

    # =================================如果说两个常用都被选了,就使用外置座位=====================================
    print("# =================================两个常用都被选了,启用外置座位=====================================")
    if len(seats_expands) == 0:
        print("没有外置座位!")

    if len(seats_expands) > 0 and ofseat is None:
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
                libid = data['variables']['libid']
                libInfo = {"operationName": "libLayout",
                           "query": "query libLayout($libId: Int!) {\n userAuth {\n prereserve {\n libLayout(libId: $libId) {\n max_x\n max_y\n seats_booking\n seats_total\n seats_used\n seats {\n key\n name\n seat_status\n status\n type\n x\n y\n }\n }\n }\n }\n}",
                           "variables": {"libId": libid}}
                # 模拟 “选择场馆” 按钮请求,获取场馆座位信息
                lib = response.post(url=url, json=libInfo, verify=False).json()

                # 获取场馆信息，判断是否已满
                seatsInfo = lib['data']['userAuth']['prereserve']['libLayout']

                # 如果这个场馆没满则获取该场馆所有座位
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
                    if key == data['variables']['key']:
                        # print(seatName,seatStatus,status,Type,key)
                        if status == False and Type == 1 and seatName is not None:
                            dataFree = {"operationName": "save",
                                        "query": "mutation save($key: String!, $libid: Int!, $captchaCode: String, $captcha: String) {\n userAuth {\n prereserve {\n save(key: $key, libId: $libid, captcha: $captcha, captchaCode: $captchaCode)\n }\n }\n}",
                                        "variables": {"key": key + '.', "libid": libid, "captchaCode": "",
                                                      "captcha": ""}}
                            # 设置座位状态为可访问，用于跳出馆室循环
                            free = True
                            print(f'当前空闲座位:{seatName},状态:{seatStatus},是否被选{status}')
                            break
                        else:
                            print(f'外置座位{seatName}被选')
                            amount -= 1
        pass

        # 当free = True的时候就会走到这里
        # 只有能用的空闲座位才可以这个地方执行,先发送选座请求
        # 判断data 参数是否非空,座位是否空闲
        if free == True and dataFree is not None:
            r = response.post(url=url, json=dataFree, verify=False)
            r_json = r.json()

            # 再发送座位信息查询请求
            r2 = response.post(url=url, json=info, verify=False)  # 发起请求查询是否抢座成功
            r2_json = r2.json()

            # 判断请求是否通过
            if r_json['data']['userAuth']['prereserve']['save']:  # 如果返回的是True
                if r2_json['data']['userAuth']['prereserve']['prereserve'] is not None:  # 查询选座状态，不是None就是成功了
                    print(f'\n====外置座位{dataFree["variables"]["key"]}号通过请求===\n'
                          f'外置抢座成功!\n'
                          f'请求的状态:{r.status_code}\n'
                          f'响应的内容:{r_json}\n'
                          f'信息查询内容{r2_json}\n'
                          f'抢座用时:{r.elapsed.total_seconds()}\n'
                          f'座位信息和时间:{datetime.datetime.now()}\n'
                          f'====外置座位{dataFree["variables"]["key"]}号通过请求===\n')
                    print(f"本次抢座从场馆开放到选上外置座位用时{time.time() - startTime}s")
                    return

            print(f'外置座位{dataFree["variables"]["key"]}号请求的状态:{r.status_code}\n'
                  f'响应的内容:{r_json}\n'
                  f'抢座用时:{r.elapsed.total_seconds()}\n'
                  f'信息查询内容{r2_json}\n'
                  f'座位信息和时间:{datetime.datetime.now()}\n'
                  f'座位{dataFree["variables"]["key"]}号')
                  
            print('抛出异常并重新刷新session')
            raise ConnectionError("选座请求异常!")

# =================================两个常用都选不上,就轰炸两个常用座位对应的场馆=================================
    print('\n==============所有自定义座位都没选上,进入常用馆室轰炸模式(有空闲就选)!==================')
    # 遍历常用座位所在的场馆,获取场馆信息
    num = 1  # 计数器，用于计算是第几次请求
    # 从常用的两个场馆去轰炸
    responseOftenSeats = response.post(url=url, json=oftenseats, verify=False).json()
    oftenseatsList = responseOftenSeats['data']['userAuth']['oftenseat']['prereserveList']

    for i in [0, 1]:
        # 从常用中获取场馆id,info
        libid = oftenseatsList[i]["lib_id"]
        freeSeats = None
        libName = oftenseatsList[i]["info"].split(' ')[0]
        print("\n场馆id:", libid, ",场馆名字:", libName)

        # 获取场馆信息的请求参数
        libInfo = {"operationName": "libLayout",
         "query": "query libLayout($libId: Int!) {\n userAuth {\n prereserve {\n libLayout(libId: $libId) {\n max_x\n max_y\n seats_booking\n seats_total\n seats_used\n seats {\n key\n name\n seat_status\n status\n type\n x\n y\n }\n }\n }\n }\n}",
         "variables": {"libId": libid}}

        freeInfo = {"operationName":"index","query":"query index {\n userAuth {\n user {\n prereserveAuto: getSchConfig(extra: true, fields: \"prereserve.auto\")\n }\n currentUser {\n sch {\n isShowCommon\n }\n }\n prereserve {\n libs {\n is_open\n lib_floor\n lib_group_id\n lib_id\n lib_name\n num\n seats_total\n }\n }\n oftenseat {\n prereserveList {\n id\n info\n lib_id\n seat_key\n status\n }\n }\n }\n}"}

        # 查询这个场馆的剩余座位信息
        freeLibInfo = response.post(url=url, json=freeInfo, verify=False).json()
        restOfLibs = freeLibInfo['data']['userAuth']['prereserve']['libs']
        for restLib in restOfLibs:
            if restLib['lib_id'] == libid and restLib['num'] != 0:
                print(f"{libName}场馆未满")
                freeSeats = restLib['num']
                print(f"{libName}场馆的剩余座位有:{freeSeats} 个")
                break

        # 如果这馆室没位置了,跳过这个馆室
        if freeSeats is None:
            print(f"{libName}场馆已满")
            continue


        # 模拟 选择场馆 按钮请求
        lib = response.post(url=url, json=libInfo, verify=False).json()
        seatsInfo = lib['data']['userAuth']['prereserve']['libLayout']

        # 获取场馆座位列表
        seatsList = seatsInfo['seats']

        # 遍历场馆座位
        for seat in seatsList:
            # 获取该场馆的每个座位对应的信息
            seatName = seat['name']
            status = seat['status']  # False表示未被选, True表示被选
            Type = seat['type']  # type=1 是表示座位正常的,其他都是不正常

            # 如果座位没问题,就发送请求
            if status == False and Type == 1 and seatName is not None:
                # 常用座位的key
                key = seat['key']

                data = {"operationName": "save",
                            "query": "mutation save($key: String!, $libid: Int!, $captchaCode: String, $captcha: String) {\n userAuth {\n prereserve {\n save(key: $key, libId: $libid, captcha: $captcha, captchaCode: $captchaCode)\n }\n }\n}",
                            "variables": {"key": key + '.', "libid": libid, "captchaCode": "","captcha": ""}}

                # 先发送选座请求
                print(f'场馆{libName}发送第{num}次请求')
                r = response.post(url=url, json=data, verify=False)
                r_json = r.json()

                # 再发送座位信息查询请求
                r2 = response.post(url=url, json=info, verify=False)  # 发起请求查询是否抢座成功
                r2_json = r2.json()

                # 判断请求是否通过
                if r_json['data']['userAuth']['prereserve']['save']:  # 如果返回的是True
                    if r2_json['data']['userAuth']['prereserve']['prereserve'] is not None:  # 查询选座状态，不是None就是成功了
                        print(f'\n===={libName}座位{seatName}号通过请求和信息查询===\n'
                              f'抢座成功!\n'
                              f'请求的状态:{r.status_code}\n'
                              f'响应的内容:{r_json}\n'
                              f'座位信息和时间:{datetime.datetime.now()}\n'
                              f'请求的状态:{r2.status_code}\n'
                              f'响应的内容:{r2_json}\n'
                              f'===={libName}座位{seatName}号   通过  请求和信息查询===\n')
                        print(f"本次抢座从场馆开放到选上轰炸座位用时{time.time() - startTime}s")
                        return

                # 其他错误  打印错误信息
                print(f'\n===={libName}座位{seatName}号 请求异常===\n'
                      f'{libName}座位{seatName}号 请求异常的信息!\n'
                      f'请求的状态:{r.status_code}\n'
                      f'响应的内容:{r_json}\n'
                      f'抢座用时:{r.elapsed.total_seconds()}\n'
                      f'座位信息和时间:{datetime.datetime.now()}\n'
                      f'===={libName}座位{seatName}号 请求异常===\n')
                print('抛出异常并重新刷新session')
                # 本轮选座请求的总次数加 1
                num += 1
                raise ConnectionError("选座请求异常!")


def oneTread(url, header, seats_expand,openTime,bookTime):
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
    newbookTime = None   # 第一次的时间跟用户设置的一样
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

            # 当常用座位设置了超时时间,常用选座卡顿则进行重刷
            except requests.exceptions.ReadTimeout:
                print("=============================卡顿超过1.3秒,即将将自动重刷页面===============================\n")
                print(f'因为请求超时(选座卡顿),准备不加延迟的重新刷新请求')
                # 出了断线情况,如果时间超过了1个小时则自动读取最新的cookie,否则用老的cookie
                if time.time() - startTime > 3600:
                    print('加载新的cookie中...')
                    with open("newCookie.txt", 'r+',encoding='utf-8') as fp:
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
                # 因为是超时导致的重刷,所以为了尽快回去选座,直接跳过排队和倒计时,加快再次发送选座请求的时间
                directBook = True
                print('超时请求重刷新成功!')
                print('=================================已经重刷了超时请求,即将重新选座!==============================\n')
                # sessioncounts += 1


            # 如果原因是JSONDecodeError,则记录响应的数据
            except requests.exceptions.JSONDecodeError:
                print("=============================JSONDecodeError的错误信息===============================\n")
                print("！！！此bug的暂时无解，不过我处理了会自己继续往下执行,出现了不要慌，慌也没用哒！！！")
                with open('errorlog.txt', 'a+', encoding='utf-8') as fp:
                    fp.write(f"{datetime.datetime.now()}报错信息:\n" + traceback.format_exc() + '\n')

                print(f'准备重新建立选座连接:第{num}次重连......')
                # 出了断线情况,如果时间超过了1个小时则自动读取最新的cookie,否则用老的cookie
                if time.time() - startTime > 3600:
                    print('加载新的cookie中...')
                    with open("newCookie.txt", 'r+',encoding='utf-8') as fp:
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
                time.sleep(0.75)  # 休眠1秒再重连

            # 这一块负责处理大部分场景的错误
            except (requests.exceptions.RequestException, websocket._exceptions.WebSocketConnectionClosedException, ConnectionResetError, KeyError,TimeoutError):
                print("=============================即将保存错误信息===============================\n")
                print("导致断线的原因可能有requests的原因(网络状况不好),也可能是webscokets的原因(包括一台电脑挂多个不同的号以及一个号挂多个相同的程序)\n请尽量避免以上三种情况!!!")
                with open('errorlog.txt', 'a+', encoding='utf-8') as fp:
                    fp.write(f"{datetime.datetime.now()}报错信息:\n" + traceback.format_exc() + '\n')

                print(f'准备重新建立选座连接:第{num}次重连......')
                # 出了断线情况,如果时间超过了1个小时则自动读取最新的cookie,否则用老的cookie
                if time.time() - startTime > 3600:
                    print('加载新的cookie中...')
                    with open("newCookie.txt", 'r+',encoding='utf-8') as fp:
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

                            print('加载完成,已经设置最新的cookie,并且保存了错误信息在errorlog.txt中')
                num += 1
                time.sleep(1)  # 休眠1秒再重连
                
            # 自定义抛出连接错误,用于刷新session,极速模式没抢到也走这里
            except ConnectionError as e:
                print("=============================我自定义的错误,用于重刷异常响应===============================\n")
                with open('errorlog.txt', 'a+', encoding='utf-8') as fp:
                    fp.write(f"{datetime.datetime.now()}报错信息:\n" + traceback.format_exc() + '\n')

                print(f'准备第{sessioncounts}次重新刷新session(这里如果是第11次就不用管了,不会再刷了其实,懒得改就这样子)')
                # 出了断线情况,如果时间超过了1个小时则自动读取最新的cookie,否则用老的cookie
                if time.time() - startTime > 3600:
                    print('加载新的cookie中...')
                    with open("newCookie.txt", 'r+',encoding='utf-8') as fp:
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
                print('=================================已经重刷了session,即将重新选座!==============================\n')
                # 重刷必须设置至少这么久的延迟,否则重刷不成功,切记不要再改小!
                time.sleep(0.75)
                sessioncounts += 1

        else:
            print('"断线重连/重刷session" 已经尝试10次,不再  重连/重刷session,请检查网络(重刷问题可能是程序逻辑,反馈开发者)是否存在问题!!!!!!!! ')
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
        configSet = getConfig(f"../config/config.json")   # 导入配置
        print('配置初始化成功！')

        # 初始化外置座位列表,提前加载到列表,传参到核心程序
        expand_seats = []
        print('\n==========================准备启用外置座位配置===============================================')
        seats_expand = configSet.get('map_seats')
        for seat0 in seats_expand:
            libid = seats_expand[seat0]['libId']
            key = seats_expand[seat0]['seatKey']
            # 这个是在场馆里选座的请求参数
            seat = {"operationName": "save",
                    "query": "mutation save($key: String!, $libid: Int!, $captchaCode: String, $captcha: String) {\n userAuth {\n prereserve {\n save(key: $key, libId: $libid, captcha: $captcha, captchaCode: $captchaCode)\n }\n }\n}",
                    "variables": {"key": key, "libid": libid, "captchaCode": "", "captcha": ""}}

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
        print("=============================错误信息(未处理,将会结束运行,请自动选座位)===============================\n", traceback.format_exc())
        with open('errorlog.txt', 'a+', encoding='utf-8') as fp:
            fp.write(f"{datetime.datetime.now()}报错信息:\n" + traceback.format_exc()+'\n')

    finally:
        print('\n程序名字:SeatForEXE-version20230923')
        print("技术支持:B站:吟啸徐行alter,uid:64605340,出了bug请联系我,有空就解决")
        input('按任意键退出')


if __name__ == '__main__':
    '''
    2023年10月15日,更新极速选座,第一次请求可以直接选座,只查询座位状态查询,出现的风险由重刷承担抵消
    更新为'先排队,到点再处理排队响应是否包含排名模式',提高排队请求速度
    
    2023年11月11号，无法处理JSONDecodeError，我已经放弃了，反正重刷session就能解决，不根治了
    遭遇新问题，排队时候座位检测次数过多导致redispool满了，或许应该在出现排名后限速请求
    
    2023年11月13号,针对常用座位请求卡顿的情况,设置了请求超时时间,超时后自动重刷,不再缓慢等待,浪费排队名次
    '''
    main()














