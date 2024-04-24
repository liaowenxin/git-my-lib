import sys
import time

from Crypto.Cipher import AES
import base64
import datetime
import json
import random
import requests
import urllib3
import websocket
import wmi


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

def queue_together(queue_header,threadName=''):
    '''
    这个是可以带排队请求头的同步排队
    :param queue_header:
    :param threadName:
    :return:
    '''
    print("================================")
    print("--------------开始排队 - ---------------------")
    ws = websocket.WebSocket()
    # ws.connect("wss://wechat.**.com/ws?ns=prereserve/queue", header=headers)
    ws.connect("wss://wechat.v2.traceint.com/ws?ns=prereserve/queue", header=queue_header)
    if ws.connected:
        ws.send('{"ns":"prereserve/queue","msg":""}')
        rank = ws.recv()
        print(threadName+'连接成功!',datetime.datetime.now())
        print("rsp msg:{}".format(json.loads(rank)))
        n=1
        while True:
            ws.send('{"ns":"prereserve/queue","msg":""}')
            a = ws.recv()
            #msg里的原生数据是unicode码
            if a.find('u6392') != -1:  # '排'队成功返回的第一个字符(找不到返回-1)
                print("rsp msg:{}".format(json.loads(a)))
                break
            if a.find('u6210') != -1:  # 已经抢座'成'功的返回
                print("rsp msg:{}".format(json.loads(a)))
                break
            print(f"No.{n}排队中，rsp:{json.loads(a)}")
            n += 1
        # 关闭连接
        ws.close()
    print("排队结束。。。")
    print("================================")

def test_queue(queue_header,threadName=''):
    '''
    用于测试的排队
    :param threadName:
    :return:
    '''
    print("================================")
    print("--------------开始测试- ---------------------")
    ws = websocket.WebSocket()
    # ws.connect("wss://wechat.**.com/ws?ns=prereserve/queue", header=headers)
    ws.connect("wss://wechat.v2.traceint.com/ws?ns=prereserve/queue", header=queue_header)

    if ws.connected:
        print(threadName+'连接成功!',datetime.datetime.now())
        ws.send('{"ns":"prereserve/queue","msg":""}')
        rank = ws.recv()
        msg=str(json.loads(rank).get('msg'))
        if len(msg)==26:#测试成功的话返回的字符串长度为26,失败返回的是 1000
            print("rsp msg:{}".format(json.loads(rank)))
            print("测试成功!")
            print("================================")
            ws.close()
            return True
        else:
            print(rank)
            print("测试结果：您的cookie可能失效,请重新扫码解析链接")
    else:
        print('websocket未连接')

def oneTread(url,header,queue_header,queue_func='queue_together',count=1):
    '''
    排队和请求的启动函数
    :param url:
    :param header:
    :param count:
    :return:
    '''
    #默认同步排队
    if queue_func=='queue_together':
        count=1
        while True:
            if count<=20:
                try:
                    queue_together(queue_header)
                    break
                except Exception as e:
                    print(f'错误信息:\n {e}')
                    print(f'准备重新连接:第{count}次重连......')
                    count+=1
                    time.sleep(0.5)
            else:
                print('重连次数超过20,不再重连,请检查网络是否存在问题!!!!!!!!\n直接进入抢座!')
                break
        # 开始选座
        num = 1
        while True:
            if num <= 20:
                try:
                    bookSeat(url, header)
                    break
                except Exception as e:
                    print(f'错误信息:\n {e}')
                    print(f'准备重新建立选座连接:第{num}次重连......')
                    num += 1
                    time.sleep(0.5)
            else:
                print('重新建立选座请求超过20,不再重连,请检查网络是否存在问题!!!!!!!!\n直接进入抢座!')
                break


    #测试排队
    if queue_func=='test':
        # 开始选座
        num = 1
        while True:
            if num <= 20:
                try:
                    bookSeat(url, header)
                    break
                except Exception as e:
                    print(f'错误信息:\n {e}')
                    print(f'准备重新建立选座连接:第{num}次重连......')
                    num += 1
                    time.sleep(0.5)
            else:
                print('重新建立选座请求超过20,不再重连,请检查网络是否存在问题!!!!!!!!\n直接进入抢座!')
                break
    print('执行结束')

def bookSeat(url, header):
    # 开始选座
    print('--------------开始选座----------------------')
    startTime = time.time()
    response = requests.session()
    count=0
    while True:
        count += 1
        print(f'\n***********************第{count}轮选座请求开始****************************')
        # 各个接口请求参数
        info={"operationName":"prereserve","query":"query prereserve {\n userAuth {\n prereserve {\n prereserve {\n day\n lib_id\n seat_key\n seat_name\n is_used\n user_mobile\n id\n lib_name\n }\n }\n }\n}"}
        oftenseats = {"operationName":"index","query":"query index {\n userAuth {\n user {\n prereserveAuto: getSchConfig(extra: true, fields: \"prereserve.auto\")\n }\n currentUser {\n sch {\n isShowCommon\n }\n }\n prereserve {\n libs {\n is_open\n lib_floor\n lib_group_id\n lib_id\n lib_name\n num\n seats_total\n }\n }\n oftenseat {\n prereserveList {\n id\n info\n lib_id\n seat_key\n status\n }\n }\n }\n}"}

        # 查询预约信息
        responseInfo=response.post(url=url, headers=header, json=info,verify=False).json()
        if responseInfo['data']['userAuth']['prereserve']['prereserve'] != None:
            print(f'您貌似已经预定了座位,请在手机上查看')
            return
        print('您尚未预定座位')

        # 查询常用座位状态 0为空闲 1为被选 查询场馆是否还有剩余位置 num>=0 表示场馆还未满
        responseOftenSeats = response.post(url=url, headers=header, json=oftenseats, verify=False).json()
        oftenseatsList=responseOftenSeats['data']['userAuth']['oftenseat']['prereserveList']
        libs=responseOftenSeats['data']['userAuth']['prereserve']['libs']
        # 如果座位所在场馆未满,且座位未被选,则添加到列表中;如果说列表为空,则说明两个座位都没法选
        dataList = []
        for seat in oftenseatsList:
            if seat['status'] == 0:
                print(seat['info']+'是空闲状态')
                # 座位的请求发送需要在坐标后面加一个英文的 .  例如:12,23.
                key = seat['seat_key']+'.'
                libid = seat['lib_id']
                # 查询场馆是否满人
                for lib in libs:
                    # 场馆id符合and 场馆剩余位置数量不为0
                    if lib['lib_id'] ==libid  and lib['num'] != 0:
                        seat = {"operationName": "save",
                                "query": "mutation save($key: String!, $libid: Int!, $captchaCode: String, $captcha: String) {\n userAuth {\n prereserve {\n save(key: $key, libId: $libid, captcha: $captcha, captchaCode: $captchaCode)\n }\n }\n}",
                                "variables": {"key": key, "libid": libid, "captchaCode": "", "captcha": ""}}
                        dataList.append(seat)
                        print(lib['lib_name']+'场馆还未满')
                        break

                    # 场馆id符合 and 场馆剩余位置数量等于0
                    if lib['lib_id'] == libid and lib['num'] == 0:
                        print(lib['lib_name']+'场馆已满')
                        break
            else:
                print(seat['info']+'已经被占用状态')

        # 选座
        if len(dataList) > 0:  # 用于判断是否还有座位可选,因为每次抢被选座位都会清除一个座位
            for data in dataList:

                # 发送一个 开始预约 的请求
                libid = data['variables']['libid']
                libInfo = {"operationName": "libLayout",
                           "query": "query libLayout($libId: Int!) {\n userAuth {\n prereserve {\n libLayout(libId: $libId) {\n max_x\n max_y\n seats_booking\n seats_total\n seats_used\n seats {\n key\n name\n seat_status\n status\n type\n x\n y\n }\n }\n }\n }\n}",
                           "variables": {"libId": libid}}
                # 模拟开始预约按钮请求
                response.post(url=url, headers=header, json=libInfo, verify=False)

                # 先发送选座请求
                time.sleep(random.uniform(0.1, 0.2))
                r = response.post(url=url, headers=header, json=data, verify=False)
                r_json = r.json()

                # 再发送座位信息查询请求
                time.sleep(random.uniform(0.2, 0.4))
                r2 = response.post(url=url, headers=header, json=info, verify=False)  # 发起请求查询是否抢座成功
                r2_json = r2.json()

                # 判断请求是否通过
                if r_json['data']['userAuth']['prereserve']['save'] == True:  # 如果返回的是True
                    if r2_json['data']['userAuth']['prereserve']['prereserve'] != None:  # 查询选座状态，不是None就是成功了
                        print(f'\n====座位{data["variables"]["key"]}号通过请求和信息查询===\n'
                              f'座位{dataList.index(data) + 1}号抢座成功!\n'
                              f'请求的状态:{r.status_code}\n'
                              f'响应的内容:{r_json}\n'
                              f'抢座用时:{r.elapsed.total_seconds()}\n'
                              f'座位信息和时间:{datetime.datetime.now()}\n'
                              f'请求的状态:{r2.status_code}\n'
                              f'响应的内容:{r2_json}\n'
                              f'抢座用时:{r2.elapsed.total_seconds()}\n'
                              f'====座位{data["variables"]["key"]}号   通过  请求和信息查询===\n')
                        return

                # 请求没通过 打印错误信息
                print(f'\n====座位{data["variables"]["key"]}号 请求异常===\n'
                      f'座位{dataList.index(data) + 1}号 请求异常的信息!\n'
                              f'请求的状态:{r.status_code}\n'
                              f'响应的内容:{r_json}\n'
                              f'抢座用时:{r.elapsed.total_seconds()}\n'
                              f'座位信息和时间:{datetime.datetime.now()}\n'
                              f'请求的状态:{r2.status_code}\n'
                              f'响应的内容:{r2_json}\n'
                              f'抢座用时:{r2.elapsed.total_seconds()}\n'
                      f'====座位{data["variables"]["key"]}号 请求异常===\n')
                dataList.remove(data)  # 移除这个座位
                time.sleep(random.uniform(0.5, 0.9))

        # 超过30秒直接退出
        elif (time.time() - startTime) >= 30:
            print(f'\n抢座核心运行已超过{time.time() - startTime},无论抢不抢到都将自动停止!\n')
            return
        # 两个座位都选不上直接退出
        else:
            print('两个座位都没选上,程序即将退出')
            return

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
            print("ok Try to grab seat!")
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
        print("本程序所提供的服务仅供学习和参考使用,经过用户同意身份认证,使用爬虫采集数据\n如果过分使用导致目标服务器不可预料故障,所导致的后果开发者概不承担,自行承担责任!\n(不同意输入n,同意则输入y或者任意键)")
        In = input("是否继续使用?:")
        if In == "n":
            print("程序退出!")
            return
        
        elif In == "y":
            print(f"您已同意上述条款(输入内容{In}),程序继续执行!")
            
        else:
            print(f"您已同意上述条款(输入内容{In}-任意键),程序继续执行!")

        #不输出警告
        urllib3.disable_warnings()
        # 1、初始化配置类--------------cookie记得每天更新！！！
        print('配置初始化。。。')
        configSet=getConfig(f"../config/config.json")   #导入配置
        print('配置初始化成功！')

        #开始测试
        cookieTest=input('是否要检验cookie有效性:(y表示是,任意键直接进入倒计时):')
        if cookieTest == 'y' or cookieTest == 'Y':
            print('开始测试cookie有效性')
            Test = test_queue(configSet.get('queue_header'))
            if Test == True:  # 测试是否能成功排队,成功则表示cookie有效
                # 3、开始抢座
                start_grabSeat(configSet.get('openTime'))
                oneTread(url=configSet.get('url'),
                         header=configSet.get('header'),
                         queue_header=configSet.get('queue_header'),
                         queue_func='queue_together')
        else:
            start_grabSeat(configSet.get('openTime'))
            oneTread(url=configSet.get('url'),
                     header=configSet.get('header'),
                     queue_header=configSet.get('queue_header'),
                     queue_func='queue_together')#这里可以改成'test',用于直接测试选座功能(跳过排队,还要把倒计时功能注释掉!)
    finally:
        print('程序名字:threadForEXE-version20230909')
        print("技术支持:B站:吟啸徐行alter,uid:64605340,出了bug请联系我,有空就解决")
        input('按任意键退出')

if __name__ == '__main__':
    # 这个是选座的 带 激活校验 支持一个配置文件抢一个号
    main()











