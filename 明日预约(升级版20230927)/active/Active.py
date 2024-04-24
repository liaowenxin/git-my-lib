from Crypto.Cipher import AES

import wmi
import base64
import time
import datetime

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
    return encrypted_text
    # print(encrypted_text)


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

def expire_date(dead):
    '''
    激活码过期时间
    :param openTime:
    :return:
    '''
    expire_Time = dead
    expireTime = time.strptime(expire_Time, "%Y-%m-%d %H:%M:%S")
    deadTime = time.mktime(expireTime)
    if time.time() >= deadTime:
        print("激活码已失效,请联系开发者!")
        print("技术支持:B站:吟啸徐行alter,uid:64605340,出了问题请联系我,有空就解决")
        return
    return True

def activeCheck():
    with open('initConfig.txt', 'r+', encoding='utf-8') as fp:
        initConfig=fp.read()
    #解密初始化中的设备信息
    bd = decrypt_oralce(initConfig)
    #获取当前设备信息
    di = getDeviceInfo()
    # print(bd==di)
    #一致则返回True
    return bd == di

def main():
    with open('initConfig.txt', 'r+', encoding='utf-8') as fp:
        initConfig = fp.read()
    #如果初始化文件是空的,就输入激活码
    if len(initConfig)==0:
        activeCode=input('请输入激活码:')
        #将base64激活码解码为字符串时间
        E_activeCode=decrypt_oralce(activeCode)
        #判断激活码是否过期,时间在前面,版本在后面,以英文分号分割
        if expire_date(E_activeCode.split(';')[0]):
            #加密设备信息, 加密的时候带上版本号
            lastTime = None
            # 试用版 只能用7天
            if E_activeCode.split(';')[-1]== "version = False":
                # 604800 = 3天
                ts = time.strftime("%Y-%m-%d", time.localtime(time.time() + 259200))
                lastTime = ts + " " + "23:59:50"
                print(lastTime)

            # 正式版 用到年底
            if E_activeCode.split(';')[-1] == "version = True":
                ts = f"{str(datetime.datetime.today().year)}-12-31"
                lastTime = ts + " " + "23:59:50"
                print(lastTime)

            # 存入设备信息和过期时间
            deviceInfo=encrypt_oracle(getDeviceInfo()+";"+lastTime)
            #写入文档
            with open('initConfig.txt', 'w', encoding='utf-8') as fp:
                fp.write(deviceInfo)
            print('激活成功!')

    print('执行结束')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        print('激活失败,请使用正确的激活码')
    finally:
        # print('')
        input('按任意键退出')

