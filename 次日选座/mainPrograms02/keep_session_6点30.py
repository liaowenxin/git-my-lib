import datetime
import http.cookies
import requests
import json
import time
import http.cookiejar
import random

cookie_string = "Authorization=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1c2VySWQiOjI1MjY5NzkxLCJzY2hJZCI6MjAxNzUsImV4cGlyZUF0IjoxNjk3NTY0OTI3fQ.GPTTMg_MiFkmDg7qM_A6j9AMiTSnFf4_DXdVFBm7jlIVbsfmEtHOZt_kja9cLbirUVJaY50ncNZiOft9_gJzMXSQa39jtyukwvtQ7pLIwypJAbw75QSkjr2jCAIdMBZexhBTTR0C3ShQOSq5J_GkDXZcdQRvjk6yQdCx36rDREOLI1H8yjOh6HC9YJqNwyL_obGx7sdoapwmSvmjGce8Jt9cclDLh5LZaets33CtFPKMwO9-b2KVjp4YeQakP0cxRyzbvywFiPVZ_B5kpgRKc3pvlx7CzGIIksZqhTUi0fPMukP93aj_8rKOZamDgVcgBXruj6MzQVMZ9qj1W6CRWQ"
session = requests.Session()
cookie = http.cookies.SimpleCookie()
cookie.load(cookie_string)
for key, morsel in cookie.items():
    session.cookies.set(key, morsel)

while True:
    if session.cookies.keys().count("Authorization") > 1:
        session.cookies.set("Authorization", domain="", value=None)
    res = session.post("http://wechat.v2.traceint.com/index.php/graphql/", json={
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
    print("响应信息:",result)

    # print(session.cookies.items(),'\n')

    dict = {}
    for key, morsel in session.cookies.items():
        dict[key] = morsel
        break

    # print(dict)
    strCookie = "Authorization"+"="+dict["Authorization"]
    if strCookie == cookie_string:
        print("cookie未变:")
        print(strCookie)
    if strCookie != cookie_string:
        print("cookie已变,当前为:")
        print(strCookie)

    print("\n当前时间:",datetime.datetime.now(), "\n")
    # 一分钟到五分钟随机更新一次会话
    timeS = random.uniform(180, 300)
    time.sleep(timeS)
    print(f"请求间隔时间为:{timeS//60}分钟")
