import json
import requests
import urllib3

cookie = "Authorization=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1c2VySWQiOjQwMjA0ODI1LCJzY2hJZCI6MjAwNTgsImV4cGlyZUF0IjoxNjk1NzgxMDA4fQ.VEirewfSpsdQIF7fDmER03EvSRzm1nxwxugf3sPJ_skuTE-0waqe01Ts29gZ4k1SESwtle8SYP7K4FY9LOiCaZ-UnDnuZSsi3TdjDwMHrM8vHSOehSVIu1LAqQaYQmb863VlC5UkodwZTAjVpC1U1IDSO-kY74lTIKaWsuiTjGyRwwMJRCs5msu7RqokJVfGz1NWFF6n-DtR3Q-GM2Ynvvsmj0iPAQDkVyey4H2aBH6MalWyqFso4LMBi8iK_E36APLrVvjCUxjEI7q7_S4wx3YFKPBq9_pEHiirL_n6cx3Sx5-TAa_Fh7P3_4QcNYe7QRI2bj8yTCM8VGqaTbjKfQ; SERVERID=82967fec9605fac9a28c437e2a3ef1a4|1695773808|1695773808; SERVERID=82967fec9605fac9a28c437e2a3ef1a4|1695773808|1695773808"
header= {
    "Host": "wechat.v2.traceint.com",
    "Connection": "keep-alive",
    "Content-Length": "194",
    "App-Version": "2.0.14",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x6309021a) XWEB/8237 Flue",
    "Content-Type": "application/json",
    "Accept": "',*/*'",
    "Origin": "https://web.traceint.com",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://web.traceint.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh",
    "Cookie" : cookie
}

url = 'https://wechat.v2.traceint.com/index.php/graphql/ '
        
def main():
    # 不输出警告
    urllib3.disable_warnings()
    #获取被害者的馆室和常用座位
    # home = {"operationName":"index","query":"query index($pos: String!, $param: [hash]) {\n userAuth {\n oftenseat {\n list {\n id\n info\n lib_id\n seat_key\n status\n }\n }\n message {\n new(from: \"system\") {\n has\n from_user\n title\n num\n }\n indexMsg {\n message_id\n title\n content\n isread\n isused\n from_user\n create_time\n }\n }\n reserve {\n reserve {\n token\n status\n user_id\n user_nick\n sch_name\n lib_id\n lib_name\n lib_floor\n seat_key\n seat_name\n date\n exp_date\n exp_date_str\n validate_date\n hold_date\n diff\n diff_str\n mark_source\n isRecordUser\n isChooseSeat\n isRecord\n mistakeNum\n openTime\n threshold\n daynum\n mistakeNum\n closeTime\n timerange\n forbidQrValid\n renewTimeNext\n forbidRenewTime\n forbidWechatCancle\n }\n getSToken\n }\n currentUser {\n user_id\n user_nick\n user_mobile\n user_sex\n user_sch_id\n user_sch\n user_last_login\n user_avatar(size: MIDDLE)\n user_adate\n user_student_no\n user_student_name\n area_name\n user_deny {\n deny_deadline\n }\n sch {\n sch_id\n sch_name\n activityUrl\n isShowCommon\n isBusy\n }\n }\n }\n ad(pos: $pos, param: $param) {\n name\n pic\n url\n }\n}","variables":{"pos":"App-首页"}}
    liblist = {"operationName":"list","query":"query list {\n userAuth {\n reserve {\n libs(libType: -1) {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n libGroups {\n id\n group_name\n }\n reserve {\n isRecordUser\n }\n }\n record {\n libs {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_color_name\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n }\n rule {\n signRule\n }\n }\n}"}
    
    response = requests.session()
    response.headers = header

    # 常用座位1所在的馆室id 获取
    # responseOftenSeats = response.post(url=url,json=home, verify=False).json()
    # responseOftenSeatsInfo=responseOftenSeats['data']['userAuth']['oftenseat']['list'][0]

    # oftenlibid = responseOftenSeatsInfo['lib_id']
    # oftenlibinfo = responseOftenSeatsInfo['info']
    # print(oftenlibinfo+"----"+str(oftenlibid))

    # 所有馆室的列表
    print("获取场馆名字信息中...")
    responseLib = response.post(url=url,json=liblist, verify=False).json()
    libs = responseLib['data']['userAuth']['reserve']['libs']
    print(libs,"\n")
    for lib in libs:
        print("馆室名字:"+lib["lib_name"])
        
main()