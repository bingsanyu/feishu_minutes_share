import requests
import json
import time

class ShareMinutes:
    def __init__(self, app_id, app_secret, code, receive_user_id):
        self.app_id = app_id
        self.app_secret = app_secret
        self.code = code
        self.receive_user_id = receive_user_id
        self.app_access_token = ''
        self.user_access_token = ''
        self.refresh_token = ''
        self.object_token = ''

    # 获取app_access_token
    # https://open.feishu.cn/document/server-docs/authentication-management/access-token/app_access_token_internal
    def get_app_access_token(self):
        app_access_token_url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
        payload = json.dumps({
            "app_id": self.app_id,
            "app_secret": self.app_secret
        })
        response = requests.post(app_access_token_url, data=payload)
        self.app_access_token = response.json()['app_access_token']
        response.close()

    # 获取user_access_token和refresh_token
    # https://open.feishu.cn/document/server-docs/authentication-management/access-token/create-2
    def get_user_access_token_and_refresh_token(self):
        access_token_url = "https://open.feishu.cn/open-apis/authen/v1/access_token"
        payload = json.dumps({
            "grant_type": 'authorization_code',
            "code": self.code
        })
        headers = {
            'Content-Type': 'application/json',
            'Authorization' : f'Bearer {self.app_access_token}'
        }
        response = requests.post(access_token_url, headers=headers, data=payload)
        # 如果返回值不为0，表示code已过期，需要重新获取
        if response.json()['code'] != 0:
            print('code已过期，请手动重新获取！')
            exit()
        self.user_access_token = response.json()['data']['access_token']
        self.refresh_token = response.json()['data']['refresh_token']
        response.close()

    # 获取录制文件的object_token
    # doc: https://open.feishu.cn/document/server-docs/vc-v1/meeting-recording/get
    # api: 获取会议录制信息 vc:record:readonly
    def get_minute_id(self, meeting_id):
        meeting_recording_url = f"https://open.feishu.cn/open-apis/vc/v1/meetings/{meeting_id}/recording"
        headers = {
            'Authorization': f'Bearer {self.app_access_token}'
        }
        response = requests.get(meeting_recording_url, headers=headers)
        # 如果没有录制文件，返回的json中没有data字段
        if 'data' not in response.json():
            print('录制文件还未生成，等待1s后重试……')
            return False
        self.object_token = response.json()['data']['recording']['url'][-24:]
        print(f'https://meetings.feishu.cn/minutes/{self.object_token}/')
        return True

    # 刷新user_access_token
    # doc: https://open.feishu.cn/document/server-docs/authentication-management/access-token/create
    def refresh_user_access_token(self):
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
        self.user_access_token = response.json()['data']['access_token']
        self.refresh_token = response.json()['data']['refresh_token']
        response.close()
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
            "manage_collaborator_entity": "collaborator_can_view",
            "security_entity": "anyone_can_view",
            "share_entity": "same_tenant"
        })
        headers = {
            'Authorization': f'Bearer {self.user_access_token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        response = requests.patch(url, headers=headers, data=payload)
        response.close()
        if response.json()['code'] == 0:
            print('开启链接分享成功！')
            return True

    # 添加协作者
    # doc: https://open.feishu.cn/document/server-docs/vc-v1/meeting-recording/set_permission
    # api: 更新会议录制信息 vc:record
    # api: 获取用户userID contact:user.employee_id:readonly
    def set_permission(self, meeting_id):
        set_permission_url = f"https://open.feishu.cn/open-apis/vc/v1/meetings/{meeting_id}/recording/set_permission?user_id_type=user_id"
        payload = json.dumps({
            "action_type": 0,
            "permission_objects": [
                {
                    "id": self.receive_user_id,
                    "permission": 1,
                    "type": 1
                }
            ]
        })
        headers = {
            'Authorization': f'Bearer {self.user_access_token}'
        }
        response = requests.patch(set_permission_url, headers=headers, data=payload)
        response.close()
        if response.json()['code'] == 0:
            # doc: https://open.feishu.cn/document/server-docs/contact-v3/user/get
            # api: 以应用身份读取通讯录 contact:contact:readonly_as_app
            get_user_info_url = f"https://open.feishu.cn/open-apis/contact/v3/users/{self.receive_user_id}?user_id_type=user_id"
            response = requests.get(get_user_info_url, headers=headers)
            user_name = response.json()['data']['user']['name']
            response.close()
            print(f'添加 {user_name} 为协作者成功！')
            return True

    # 获取tenant_access_token
    # doc: https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
    def get_tenant_access_token(self):
        get_tenant_access_token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = json.dumps({
            "app_id": self.app_id,
            "app_secret": self.app_secret
        })
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        response = requests.post(get_tenant_access_token_url, headers=headers, data=payload)
        tenant_access_token = response.json()['tenant_access_token']
        return tenant_access_token

    # 发送消息通知
    # doc: https://open.feishu.cn/document/server-docs/im-v1/message/create
    # api: 获取与发送单聊、群组消息 im:message
    def send_message(self):
        tenant_access_token = self.get_tenant_access_token()
        minutes_url = f"https://meetings.feishu.cn/minutes/{self.object_token}"
        send_message_url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=user_id"
        payload = json.dumps({
            "receive_id": self.receive_user_id,
            "msg_type": "text",
            "content": json.dumps({"text":f"{minutes_url}"})
        })
        headers = {
            'Authorization': f'Bearer {tenant_access_token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
        response = requests.post(send_message_url, headers=headers, data=payload)
        response.close()
        if response.json()['code'] == 0:
            print('发送消息通知成功！')
            return True

    def run(self, meeting_id):
        print(time.strftime("\n%Y-%m-%d %H:%M:%S", time.localtime()))
        print(f'会议结束: {meeting_id}')
        while True:
            time.sleep(7)
            if self.get_minute_id(meeting_id) and self.refresh_user_access_token() and self.set_permission(meeting_id) and self.set_public() and self.send_message():
                break
            time.sleep(1)