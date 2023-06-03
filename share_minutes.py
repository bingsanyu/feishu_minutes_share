import time
import datetime
import requests
import json
import logging


def beijing(sec, what):
    beijing_time = datetime.datetime.now() + datetime.timedelta(hours=8)
    return beijing_time.timetuple()
logging.Formatter.converter = beijing
logging.basicConfig(filename='usage.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


while True:
    try:
        # 获取app_access_token
        url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
        payload = json.dumps({
            "app_id": "", #
            "app_secret": "" #
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        app_access_token = response.json()['app_access_token']
        response.close()
        # 读取refresh_token
        with open('refresh_token.txt', 'r') as f:
            refresh_token = f.read()

        cookie = '' #
        bv_csrf_token = '' #
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'cookie': cookie,
            'referer': 'https://se6llxwh0q.feishu.cn/minutes/me',
            'content-type': 'application/x-www-form-urlencoded',
            'bv-csrf-token': bv_csrf_token,
        }
        get_rec_url = 'https://se6llxwh0q.feishu.cn/minutes/api/space/list?&size=100&space_name=2'
        resp = requests.get(url=get_rec_url, headers=headers)
        all_meetings= list(reversed(resp.json()['data']['list']))
        resp.close()

        # # 创建access_token
        # url = ' https://open.feishu.cn/open-apis/authen/v1/index?app_id=&redirect_uri=https%3A%2F%2Fhttpbin.org'
        # response = requests.request("GET", url)
        # print(response.url)
        # print(response.json())
        
        is_refresh = True
        # 授权录制文件
        for i in all_meetings:
            # 判断是否已经授权
            # 读取已经授权的会议id
            with open('exist_meetings.txt', 'r') as f:
                exist_meetings = f.read().split('\n')
            if i['meeting_id'] in exist_meetings:
                continue
            logging.info(i['meeting_id'])

            # 刷新access_token
            if is_refresh:
                is_refresh = False
                url = "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token"
                payload = json.dumps({
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                })
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {app_access_token}'
                }
                response = requests.request("POST", url, headers=headers, data=payload)
                logging.info(response.text)
                access_token = response.json()['data']['access_token']
                refresh_token = response.json()['data']['refresh_token']
                # 将refresh_token写入文件
                with open('refresh_token.txt', 'w') as f:
                    f.write(refresh_token)
                logging.info(refresh_token)
                response.close()


            # 开启链接分享以及添加协作者
            logging.info(i['object_token'])
            url = f"https://open.feishu.cn/open-apis/drive/v2/permissions/{i['object_token']}/public?type=minutes"
            payload = json.dumps({
                "comment_entity": "anyone_can_view",
                "copy_entity": "anyone_can_view",
                "external_access_entity": "open",
                "link_share_entity": "tenant_readable",
                "manage_collaborator_entity": "collaborator_can_view",
                "security_entity": "anyone_can_view",
                "share_entity": "same_tenant"
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            response = requests.request("PATCH", url, headers=headers, data=payload)
            logging.info(response.text)
            response.close()

            # 授权给一个人
            url = f"https://open.feishu.cn/open-apis/vc/v1/meetings/{i['meeting_id']}/recording/set_permission?user_id_type=user_id"
            payload = json.dumps({
                "action_type": 0,
                "permission_objects": [
                    {
                        "id": "", #
                        "permission": 1,
                        "type": 1
                    }
                ]
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            response = requests.request("PATCH", url, headers=headers, data=payload)
            logging.info(response.text)
            response.close()
            with open('exist_meetings.txt', 'a') as f:
                f.write(i['meeting_id'] + '\n')
    except Exception as ex:
        logging.error(ex)
        pass
    time.sleep(600)
