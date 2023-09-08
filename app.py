import os, json
import fc2
from flask import Flask, request


def async_proxy():
    client = fc2.Client(
        endpoint=os.environ.get('ALIYUN_FC_ENDPOINT'),
        accessKeyID=os.environ.get('ALIYUN_ACCESS_KEY_ID'),
        accessKeySecret=os.environ.get('ALIYUN_ACCESS_KEY_SECRET')
    )
    client.invoke_function(
        os.environ.get('ALIYUN_FC_ASYNC_TASK_SERVICE_NAME'),
        os.environ.get('ALIYUN_FC_ASYNC_TASK_FUNCTION_NAME'),
        headers={'x-fc-invocation-type': 'Async'},
        payload=json.dumps(request.get_data().decode('utf-8'))
    )


app = Flask(__name__)


@app.route("/webhook", methods=['POST'])
def feishu_webhook_event():
    payload = request.get_json()

    if payload.get('type', None) == 'url_verification':
        return {'challenge': payload['challenge']}
    print(payload)

    if payload.get('header') and payload.get('header').get('event_type') == 'vc.meeting.all_meeting_ended_v1':
        async_proxy()
    return '',200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)