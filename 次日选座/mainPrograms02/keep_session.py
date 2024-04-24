import datetime
import http.cookies
import requests
import json
import time
import http.cookiejar
import random

cookie_string = "Authorization=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1c2VySWQiOjExMDUyNjE4LCJzY2hJZCI6MTAwMDQsImV4cGlyZUF0IjoxNjk4NTE0NjQwfQ.f2JqsFjEM0hIcSyPUJpjeZZwKXSukqxopErdnV6Bs014ceIPgg_pwlLfwvUTxqOyB12Nl52UdBOzj6pBn_OnGwQNfv_8JuQ_MRghTpjLFcebDyZuZW-EAQOwncR4wA7tb4PDxePNHLpvCy5xwQF9NJMY2Nvy34-t5Kofy3OSMgyCaMfXyVR1cBuOKIzFQ5H4itl714yju-qqtO_hbmz45wooLZuIqkeHNSE61GJj3vDUdb0I8BzxVQDMo6sNr2JDi8e21s7MdEdYEZJuo_N9ULfFRJNzSanVipgLv_2cdPYZxE9AKszQygGn2d-kII1ZUGRML8Up9LI8Hf9P1B_YRA"
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
