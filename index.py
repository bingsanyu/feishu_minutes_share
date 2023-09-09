import os, json
import oss2
from share_minutes import ShareMinutes


def handler(event, context):
    response = json.loads(event)

    share_minutes = ShareMinutes()

    auth = oss2.Auth(os.environ.get('ALIYUN_ACCESS_KEY_ID'), os.environ.get('ALIYUN_ACCESS_KEY_SECRET'))
    bucket = oss2.Bucket(auth, os.environ.get('ALIYUN_OSS_ENDPOINT'), os.environ.get('ALIYUN_OSS_BUCKET_NAME'))

    if response.get('payload') == "need_refresh":
        share_minutes.get_app_access_token()
        if not share_minutes.get_refresh_token():
            if not bucket.object_exists('feishu_refresh_key.txt'):
                print('code失效且没有已保存的refresh。请更新code！')
                return
            share_minutes.refresh_token = bucket.get_object('feishu_refresh_key.txt').read().decode('utf-8')
            share_minutes.get_user_access_token()
        bucket.put_object('feishu_refresh_key.txt', share_minutes.refresh_token)

    elif response.get('header') and response.get('header').get('event_type') == 'vc.meeting.all_meeting_ended_v1':
        meeting_id = response['event']['meeting']['id']
        share_minutes.refresh_token = bucket.get_object('feishu_refresh_key.txt').read().decode('utf-8')
        share_minutes.run(meeting_id)
        bucket.put_object('feishu_refresh_key.txt', share_minutes.refresh_token)

    return
