import datetime
import http.cookies
import requests
import json
import time
import http.cookiejar
import random

cookie_string = "Authorization=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1c2VySWQiOjQxMDYxMTcwLCJzY2hJZCI6NzksImV4cGlyZUF0IjoxNjk4MDMxNTE0fQ.lvtnDosO6H_TswiyIrDIggK7KBFYu0Mm1-EbL5Djob9pdnAi2Gw0I-OCJdPZkeRlbRyCR1CYl9Q2vX2blV3890wpmEY7tChQ-xii2fyADAeRY0ov-K4OE7gc68__voYKjrAzE8K3HOmNkGNsDtZgOje5LXqMWX0XTL6QPutydZA43--t4BpQyI23P82pI0IRPi-vncec4lEfI-6sA36lVbbK3PhgKoslhF0YOpacYv3Q7KP9xWEa1M8jXRtn_xJL1cIUAGBNqY2ppCVFVHi9nr7SGNntiEltPauZekQhrZ6D6sa2IbsRTl3Th-GIz75G4LD6lVNXR0goZr1tUsS-yA; SERVERID=d3936289adfff6c3874a2579058ac651|1698024314|1698024314; SERVERID=e3fa93b0fb9e2e6d4f53273540d4e924|1698024314|1698024314"
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
