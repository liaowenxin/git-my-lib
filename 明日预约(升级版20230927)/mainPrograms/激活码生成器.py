# AES-demo
import time

import base64
from Crypto.Cipher import AES

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


if __name__ == '__main__':
    # 原理,使用aes加密时间,激活程序根据解密出的时间去判断是否执行初始化数据操作
    # 加密的时间格式: 2023-12-23 13:00:00,这里我是在当前时间上加了120秒(2分钟)
    
    version = False # True 是正式版的意思,False是测试版
    
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()+120))
    print(f'激活码过期时间:{ts}\nversion = {version}')
    encrypt_oracle(f'{ts};version = {version}')

    # encrypt_oracle("2023-09-12 22:00:00")
    # decrypt_oralce("vTkZGW2ata761YZX6k2xNZBKs+lnwyN3c7YZXNISqDZdaM59CyqvjHgnM+De6iedVFHpM5b3LYUWQ8fsNmm1wV0USN3QlkxUvBHjAS37ei4sISuNg2N6ncidj+vqiUhiMGZflogUF7z2L5a0HUcU4g==")
    # a = "2023-09-22 10:04:49;version = False"
    # print(a.split(';')[-1])