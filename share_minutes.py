import os, time, json, datetime
import requests


class ShareMinutes:
    def __init__(self):
        self.app_id = os.environ.get('FEISHU_APP_ID')
        self.app_secret = os.environ.get('FEISHU_APP_SECRET')
        self.authorized_users_id_list = os.environ.get('FEISHU_AUTHORIZED_USERS_ID_LIST')
        self.auth_code = ''
        self.app_access_token = ''
        self.tenant_access_token = ''
        self.user_access_token = ''
        self.refresh_token = ''
        self.object_token = ''
        self.employee_dict = {}

    # 获取app_access_token
    # doc: https://open.feishu.cn/document/server-docs/authentication-management/access-token/app_access_token_internal
    def get_app_access_token(self):
        app_access_token_url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
        payload = json.dumps({
            "app_id": self.app_id,
            "app_secret": self.app_secret
        })
        response = requests.post(app_access_token_url, data=payload)
        if response.json()['code'] != 0:
            print('获取app_access_token失败，请检查app_id和app_secret！')
            return
        self.app_access_token = response.json()['app_access_token']

    # 获取tenant_access_token
    # doc: https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
    def get_tenant_access_token(self):
        get_tenant_access_token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = json.dumps({
            "app_id": self.app_id,
            "app_secret": self.app_secret
        })
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        response = requests.post(get_tenant_access_token_url, headers=headers, data=payload)
        if response.json()['code'] != 0:
            print('获取tenant_access_token失败，请检查app_id和app_secret！')
            return
        self.tenant_access_token = response.json()['tenant_access_token']

    # 获取refresh_token
    # doc: https://open.feishu.cn/document/server-docs/authentication-management/access-token/create-2
    def get_refresh_token(self):
        access_token_url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
        payload = json.dumps({
            "grant_type": 'authorization_code',
            "code": os.environ.get('CODE')
        })
        headers = {
            "Content-Type": "application/json",
            "Authorization" : f"Bearer {self.app_access_token}"
        }
        response = requests.post(access_token_url, headers=headers, data=payload)
        if response.json()['code'] != 0:
            return False
        self.refresh_token = response.json()['data']['refresh_token']
        return True

    # 刷新user_access_token
    # doc: https://open.feishu.cn/document/server-docs/authentication-management/access-token/create
    def get_user_access_token(self):
        refresh_token_url = "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token"
        payload = json.dumps({
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        })
        headers = {
            'Authorization': f'Bearer {self.app_access_token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        response = requests.request("POST", refresh_token_url, headers=headers, data=payload)
        if response.json()['code'] != 0:
            print('刷新user_access_token失败！')
            return False
        self.user_access_token = response.json()['data']['access_token']
        self.refresh_token = response.json()['data']['refresh_token']

    # 获取参会人列表
    # doc: https://open.feishu.cn/document/server-docs/vc-v1/meeting/get
    # api: 获取会议信息 vc:meeting:readonly
    def get_participants_id_list(self, meeting_id):
        meeting_detail_url = f"https://open.feishu.cn/open-apis/vc/v1/meetings/{meeting_id}?with_participants=true&user_id_type=user_id"
        headers = {
            'Authorization': f'Bearer {self.tenant_access_token}'
        }
        response = requests.get(meeting_detail_url, headers=headers).json()
        if response['code'] != 0:
            print("获取会议详情失败！")
            return None, None
            
        week_list = ["周一","周二","周三","周四","周五","周六","周日"]
        weekday = week_list[datetime.datetime.strptime(time.strftime("%Y-%m-%d", time.localtime(28800+int(response['data']['meeting']['start_time']))), '%Y-%m-%d').weekday()]

        participants_id_list = [participants['id'] for participants in response['data']['meeting']['participants']]
        start_time = time.strftime("%m-%d%H:%M", time.localtime(28800+int(response['data']['meeting']['start_time'])))
        end_time = time.strftime("%H:%M", time.localtime(28800+int(response['data']['meeting']['end_time'])))
        meeting_time = start_time[:5] + weekday + start_time[5:] + "至" + end_time

        return participants_id_list, meeting_time

    # 获取录制文件的object_token
    # doc: https://open.feishu.cn/document/server-docs/vc-v1/meeting-recording/get
    # api: 获取会议录制信息 vc:record:readonly
    def get_minute_id(self, meeting_id):
        meeting_recording_url = f"https://open.feishu.cn/open-apis/vc/v1/meetings/{meeting_id}/recording"
        headers = {
            'Authorization': f'Bearer {self.app_access_token}'
        }
        response = requests.get(meeting_recording_url, headers=headers)
        if 'data' not in response.json():
            return False
        self.object_token = response.json()['data']['recording']['url'][-24:]
        print(f'https://meetings.feishu.cn/minutes/{self.object_token}/')
        return True

    # 开启链接分享
    # doc: https://open.feishu.cn/document/server-docs/docs/permission/permission-public/patch-2
    # api: 查看、评论、编辑和管理文档 docs:doc
    def set_public(self):
        url = f"https://open.feishu.cn/open-apis/drive/v2/permissions/{self.object_token}/public?type=minutes"
        payload = json.dumps({
            "comment_entity": "anyone_can_view",
            "copy_entity": "anyone_can_view",
            "external_access_entity": "open",
            "link_share_entity": "tenant_readable",
            "manage_collaborator_entity": "collaborator_full_access",
            "security_entity": "anyone_can_view",
            "share_entity": "same_tenant"
        })
        headers = {
            'Authorization': f'Bearer {self.user_access_token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        response = requests.patch(url, headers=headers, data=payload)
        if response.json()['code'] == 0:
            print('开启链接分享成功！')
        else:
            print('开启链接分享失败')

    # 添加协作者
    # doc: https://open.feishu.cn/document/server-docs/vc-v1/meeting-recording/set_permission
    # api: 更新会议录制信息 vc:record
    # api: 获取用户userID contact:user.employee_id:readonly
    def set_permission(self, meeting_id):
        participants_id, meeting_time = self.get_participants_id_list(meeting_id)
        if not participants_id:
            return
        participants_id = set(participants_id)
        content = "{\"text\":\""+meeting_time+" 参会人:"
        for id in participants_id:
            if id in self.employee_dict.keys():
                content += f"<at user_id=\\\"{id}\\\">{self.employee_dict[id]}</at>"
            else:
                content += f"@飞书个人用户"
        content += "\\nhttps://meetings.feishu.cn/minutes/"+self.object_token+"\"}"

        
        set_permission_url = f"https://open.feishu.cn/open-apis/vc/v1/meetings/{meeting_id}/recording/set_permission?user_id_type=user_id"
        headers = {
            "Authorization": f"Bearer {self.user_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        all_users = self.authorized_users_id_list.split(',')
        for authorized_user_id in all_users:
            payload = json.dumps({
                "action_type": 0,
                "permission_objects": [
                    {
                        "id": authorized_user_id,
                        "permission": 1,
                        "type": 1
                    }
                ]
            })
            authorized_user_name = self.employee_dict[authorized_user_id]
            response = requests.patch(set_permission_url, headers=headers, data=payload)
            if response.json()['code'] == 0:
                    print(f'添加 {authorized_user_name} 为协作者成功！')
                    if self.send_message(authorized_user_id, content):
                        print(f'发送消息给 {authorized_user_name} 失败！')
                    else:
                        print(f'发送消息给 {authorized_user_name} 成功！')
            else:
                print(f'添加协作者失败！{response.json()}')

    # 获取员工花名册信息（最大值100，超过则需要分页获取）
    # doc: https://open.feishu.cn/document/server-docs/ehr-v1/list
    # api: 获取飞书人事（标准版）应用中的员工花名册信息 ehr:employee:readonly
    def get_employee_name(self):
        get_employee_name_url = "https://open.feishu.cn/open-apis/ehr/v1/employees?status=2&user_id_type=user_id&page_size=100"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}"
        }
        response = requests.get(get_employee_name_url, headers=headers).json()
        if response['code'] != 0:
            print("获取员工花名册信息失败！")
            return
        self.employee_dict = {employee['user_id']:employee['system_fields']['name'] for employee in response['data']['items']}

    # 发送消息通知
    # doc: https://open.feishu.cn/document/server-docs/im-v1/message/create
    # api: 获取与发送单聊、群组消息 im:message
    def send_message(self, receive_id, content):
        send_message_url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=user_id"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = json.dumps({
            "receive_id": receive_id,
            "msg_type": "text",
            "content": content
        })
        response = requests.post(send_message_url, headers=headers, data=payload)
        return response.json()['code']

    def run(self, meeting_id):
        print(time.strftime("\n%Y-%m-%d %H:%M:%S", time.localtime()))
        print(f'会议结束: {meeting_id}')

        self.get_user_access_token()
        self.get_tenant_access_token()
        self.get_employee_name()
        
        try:
            # 会议结束到回放生成需要一段时间
            time.sleep(3)
            for _ in range(200):
                if self.get_minute_id(meeting_id): # 此接口频率限制为1000次/分钟、50次/秒
                    break
                time.sleep(0.1)

            self.set_permission(meeting_id)
            self.set_public()

        except Exception as e:
            print(e)
