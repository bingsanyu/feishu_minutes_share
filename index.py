import json
from share_minutes import ShareMinutes


def handler(event, context):
    if type(json.loads(event)) == type({}):
        return
    req = json.loads(json.loads(event))
    meeting_id = req['event']['meeting']['id']
    share_minutes = ShareMinutes()
    share_minutes.run(meeting_id)