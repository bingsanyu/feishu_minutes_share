import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from share_minutes import ShareMinutes

# 企业自建应用
app_id = ''
app_serect = ''

# 被授权的用户ID，见飞书管理后台-组织架构-成员与部门-花名册-点击成员详情-基本信息-用户ID
receive_user_id = '' 

# 手动获取登录预授权码
# doc: https://open.feishu.cn/document/server-docs/authentication-management/login-state-management/obtain-code
code = ''


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        post_data = json.loads(post_data.decode('utf-8'))
        if 'challenge' in post_data and post_data['type'] == 'url_verification':
            response = {'challenge': post_data['challenge']}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif post_data['header']['event_type'] == 'vc.meeting.all_meeting_ended_v1':
            # 事件订阅: 企业会议结束v2.0 vc.meeting.all_meeting_ended_v1
            # doc: https://open.feishu.cn/document/server-docs/vc-v1/meeting/events/all_meeting_ended
            # api: 获取所有视频会议信息 vc:meeting.all_meeting:readonly
            meeting_id = post_data['event']['meeting']['id']
            try:
                share_minutes.run(meeting_id)
            except Exception as e:
                print(e)
        else:
            pass

class Server(HTTPServer):
    allow_reuse_address = True

def start_server():
    server = Server(('localhost', 61123), Handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

if __name__ == '__main__':
    share_minutes = ShareMinutes(app_id, app_serect, code, receive_user_id)
    share_minutes.get_app_access_token()
    share_minutes.get_user_access_token_and_refresh_token()
    print('初始化完成')
    start_server()
    while True:
        pass