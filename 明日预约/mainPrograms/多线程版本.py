import sys
import time

import datetime
import random
import json
import requests
import threading
import urllib3
import websocket


class myThread(threading.Thread):
    """
        定义线程对象
    """

    def __init__(self, name, url, queue_header, header, data1, data2, data3, cookietest, opentime, queue_func):
        threading.Thread.__init__(self)
        self.data1 = data1
        self.data2 = data2
        self.data3 = data3
        self.url = url
        self.header = header
        self.name = name
        self.queue_header = queue_header
        self.cookietest = cookietest
        self.opentime = opentime
        self.queue_func = queue_func

    def run(self):
        print(f"\n开始: {self.name}\n")
        crawl(self.name, self.url, self.queue_header, self.header, self.data1, self.data2, self.data3, self.cookietest,
              self.opentime, self.queue_func)
        print(f"\n结束: {self.name}\n")


def test_queue(queue_header, threadname=''):
    '''
    用于测试的排队
    :param threadname:
    :return:
    '''
    ws = websocket.WebSocket()
    # ws.connect("wss://wechat.**.com/ws?ns=prereserve/queue", header=headers)
    ws.connect("wss://wechat.v2.traceint.com/ws?ns=prereserve/queue", header=queue_header)
    if ws.connected:
        ws.send('{"ns":"prereserve/queue","msg":""}')
        rank = ws.recv()
        msg = str(json.loads(rank).get('msg'))
        if len(msg) == 26:  # 测试成功的话返回的字符串长度为26,失败返回的是 1000
            print(f"{threadname}测试成功!,rsp msg:{json.loads(rank)}\n")
            ws.close()
            return True
        else:
            print(f"{threadname}测试结果：{rank}\n当前配置文件的cookie可能失效,请重新扫码解析链接\n")


def pass_queue(queue_header, threadname=''):
    '''
    用于正式
    :param queue_header:
    :param threadname:
    :return:
    '''
    print(f"{threadname}开始排队\n")
    ws = websocket.WebSocket()
    # ws.connect("wss://wechat.**.com/ws?ns=prereserve/queue", header=headers)
    ws.connect("wss://wechat.v2.traceint.com/ws?ns=prereserve/queue", header=queue_header)
    if ws.connected:
        while True:
            ws.send('{"ns":"prereserve/queue","msg":""}')
            rank = ws.recv()
            if rank.find('u4e0d') == -1:#表示找不到'不'字,即在预约时间内
                print(f'{threadname}连接成功!,当前时间是:{datetime.datetime.now()}\n'
                      f'{threadname}排队中，排队进去的名次(data):{json.loads(rank)}')
                break
                
        while True:
            ws.send('{"ns":"prereserve/queue","msg":""}')
            rsp = ws.recv()
            # msg里的原生数据是unicode码
            if rsp.find('u6392') != -1:  # '排'队成功返回的第一个字符(找不到返回-1)
                print(f"{threadname}排队结束,rsp msg:{json.loads(rsp)}")
                break
            if rsp.find('u6210') != -1:  # 已经抢座'成'功的返回
                print(f"{threadname}排队结束,rsp msg:{json.loads(rsp)}")
                break
        # 关闭连接
        ws.close()


def crawl(threadname, url, queue_header, header, data1, data2, data3, cookietest, opentime, queue_func):
    '''
        是排队和请求的程序，给每个线程执行这个程序
    :param threadname:
    :param url:
    :param queue_header:
    :param header:
    :param data1:
    :param data2:
    :param data3:
    :param cookietest:
    :param opentime:
    :param queue_func:
    :return:
    '''
    try:
        # 这个是测试的
        if queue_func == 'test':
            # 每个线程直接发送占座请求
            bookSeat(threadname, url=url, header=header, data1=data1, data2=data2, data3=data3)

        # 这个是正式的
        if queue_func == pass_queue:
            # 判断是否需要测试cookie有效性
            if cookietest == 'y' or cookietest == 'Y':
                print(f'\n{threadname}开始测试cookie有效性')
                test = test_queue(queue_header, threadname)
                if test:  # 测试是否能成功排队,成功则表示cookie有效
                    start_grabSeat(opentime, threadname)
                    pass_queue(threadname=threadname, queue_header=queue_header)
                    # 每个线程发送占座请求
                    bookSeat(threadname, url=url, header=header, data1=data1, data2=data2, data3=data3)
                    return

            # 不进行测试,直接进入倒计时
            start_grabSeat(opentime, threadname)
            pass_queue(threadname=threadname, queue_header=queue_header)
            # 每个线程发送占座请求
            bookSeat(threadname, url=url, header=header, data1=data1, data2=data2, data3=data3)

    except Exception as e:
        print(f"{threadname}的错误信息: {e}")


def bookSeat(threadname, url, header, data1, data2, data3):
    # 开始选座
    print(f'\n{threadname}开始选座')
    dataList = [data1, data2]
    response = requests.session()
    startTime=time.time()
    while True:
        if len(dataList) > 0:  # 用于判断是否还有座位可选,因为每次抢被选座位都会清除一个座位
            for data in dataList:

                # 先发送抢座请求
                time.sleep(random.uniform(0.7, 0.9)) # --------这个延迟差不多是最合适的,抢座位
                r = response.post(url=url, headers=header, json=data, verify=False)
                r_json = r.json()
                # 再发送座位信息查询请求
                r2 = response.post(url=url, headers=header, json=data3, verify=False)  # 发起请求查询是否抢座成功
                r2_json = r2.json()
                if r_json['data']['userAuth']['prereserve']['save'] == True:  # 如果返回的是True
                    if r2_json['data']['userAuth']['prereserve']['prereserve'] != None:  # 查询选座状态，不是None就是成功了或者被选了
                        endTime=time.time()
                        print(f'\n===={threadname}的座位{data["variables"]["key"]}号通过请求和信息查询===\n'
                              f'{threadname}座位{dataList.index(data) + 1}号抢座成功!\n'
                              f'请求的状态:{r.status_code}\n'
                              f'响应的内容:{r_json}\n'
                              f'抢座用时:{r.elapsed.total_seconds()}\n'
                              f'座位信息和时间:{datetime.datetime.now()}\n'
                              f'请求的状态:{r2.status_code}\n'
                              f'响应的内容:{r2_json}\n'
                              f'抢座用时:{r2.elapsed.total_seconds()}\n'
                              f'===={threadname}座位{dataList.index(data) + 1}号    通过  请求和信息查询===\n')
                        print(f"{threadname}运行耗时：{endTime - startTime} s")
                        return  # 抢到了直接退出

                    # 是true但是没有请求到数据,重新执行循环
                    time.sleep(random.uniform(0.5, 0.9))
                    continue

                elif r.text.find('u88ab') != -1 or r.text.find('u5237') != -1:  # '被'字or'刷'字 返回,表示被抢了
                    print(f'\n===={threadname}的座位{data["variables"]["key"]}号  已经被选了 ===\n'
                          f'座位{dataList.index(data) + 1}号抢座失败!\n'
                          f'请求的状态:{r.status_code}\n'
                          f'响应的内容:{r_json}\n'
                          f'抢座用时:{r.elapsed.total_seconds()}\n'
                          f'座位信息和时间:{datetime.datetime.now()}\n'
                          f'===={threadname}的座位{data["variables"]["key"]}号 已经被选了===\n')
                    dataList.remove(data)  # 移除这个座位
                    time.sleep(random.uniform(0.5, 0.9))
                    continue

                elif r.text.find('u6ee1') != -1:  # '满'字返回,表示 场馆满了,直接退出
                    print(f'\n===={threadname}的座位{data["variables"]["key"]}号的 场馆满了 ===\n'
                          f'座位{dataList.index(data) + 1}号 的场馆满了!\n'
                          f'请求的状态:{r.status_code}\n'
                          f'响应的内容:{r_json}\n'
                          f'抢座用时:{r.elapsed.total_seconds()}\n'
                          f'座位信息和时间:{datetime.datetime.now()}\n'
                          f'===={threadname}的座位{data["variables"]["key"]}号的 场馆满了===\n')
                    dataList.remove(data)
                    time.sleep(random.uniform(0.5, 0.9))
                    continue

                elif (time.time()-startTime) >= 30:
                    print(f'{threadname} 的抢座核心运行已超过{time.time()-startTime},无论抢不抢到都将自动停止!')
                    return
        else:
            print(f'{threadname}的两个座位都被抢了!')
            break



def startThreads(queue_func, cookietest='', count=1):
    '''
        创建线程池，默认创建1个
    :param queue_func:
    :param cookietest:
    :param count:
    :return:
    '''
    # 创建线程池
    threads = []
    # 创建n个新线程
    for i in range(1, count + 1):
        # 初始化配置类
        configSet = getConfig(f"../config/config{i}.json")

        # 初始化新线程名字
        thread = myThread(name="Thread" + str(i) + '号',
                          url=configSet.get('url'),
                          header=configSet.get('header'),
                          queue_header=configSet.get('queue_header'),
                          data1=configSet.get('data1'),
                          data2=configSet.get('data2'),
                          data3=configSet.get('data3'),
                          cookietest=cookietest,
                          opentime=configSet.get('openTime'),
                          queue_func=queue_func)
        # 开启新线程
        thread.start()
        # 添加新线程到线程列表
        threads.append(thread)

    # 等待所有线程完成
    for thread in threads:
        thread.join()


def start_grabSeat(openTime, threadname):
    '''
    程序倒计时
    :param opentime:
    :return:
    '''
    struct_openTime = openTime
    openTime = time.strptime(struct_openTime, "%Y-%m-%d %H:%M:%S")
    openTime = time.mktime(openTime)
    print(
        f'{threadname}进入倒计时\n当前时间:{datetime.datetime.now()},\n剩余时间:{openTime - time.time()}s\n系统默认倒计时中......\n')
    while True:
        # print(f'剩余时间:{opentime-time.time()}s')
        if time.time() >= openTime:
            print("------------------------------")
            print("ok Try to grab seat!")
            break


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


def main():
    try:
        # 关闭程序执行警告
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # 设置线程数量
        count = eval(input('请输入线程数( 线程数<=配置文件数量):'))

        cookietest = input('是否要检验cookie有效性:(y表示是,任意键直接进入倒计时):')
        # 多线程,count默认为1个线程,  ! important     线程数<=配置文件数量
        startThreads(queue_func=pass_queue, cookietest=cookietest, count=count)

        # 不排队直接请求座位,用于测试请求座位的功能
        # startThreads(queue_func='test',cookietest=cookietest,count=count)

    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("exc_type:", exc_type)
        print("exc_value:", exc_value)
        print("exc_traceback:", exc_traceback)

    finally:
        print('程序名字:多线程版本\n技术支持:B站:吟啸徐行alter,uid:64605340,出了问题请联系我,有空就解决')
        input('按任意键退出')

if __name__ == '__main__':
    main()
