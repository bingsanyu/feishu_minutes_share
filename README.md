# 创建应用
1. 在[飞书开发者平台](https://open.feishu.cn/app/)创建一个企业自建应用。
2. 点击`应用功能-添加应用能力`，添加`网页应用`和`机器人`。
3. 点击`开发配置-事件订阅`，在`请求地址配置`中输入自己的公网ip或者内网穿透工具提供的公网ip。同时，将`Encrypt Key`和`Verification Token`设为空值（不进行加密，如果你想进行加密则需要修改代码以实现解密功能。）
4. 点击`开发配置-权限管理-API权限`，开启下面的权限。
    - contact:contact:readonly_as_app
    - contact:user.employee_id:readonly
    - docs:doc
    - im:message
    - vc:meeting.all_meeting:readonly
    - vc:record
    - vc:record:readonly
5. 点击`开发配置-事件订阅-已添加事件`，添加下面的事件。
    - vc.meeting.all_meeting_ended_v1
6. 点击`开发配置-安全设置-重定向URL`，添加下面的URL。
    - https://httpbin.org/
    - 其他网址也可以
5. 发布版本并由企业管理员进行审核。

# 配置main.py参数
1. 在你所创建应用的管理页面，点击`基础信息-凭证与基础信息`，复制`应用凭证`中的`App ID`和`App Secret`，粘贴到代码相应位置。
2. 在[飞书管理后台](https://feishu.cn/admin/contacts/departmentanduser/people-standard-plugin/people-manage/roster)点击想要授权的用户，复制其`用户 ID`参数，粘贴到代码相应位置。
3. 将 `https://open.feishu.cn/open-apis/authen/v1/user_auth_page_beta?app_id={app_id}&redirect_uri={redirect_uri}&state=` 中的`{app_id}`替换为你所建应用的`App ID`，将`{redirect_uri}`替换为你设置的`重定向URL`。打开修改后的链接，出现飞书授权登录页面，点击`授权`，等待网页重定向。复制重定向后的url（如`https://httpbin.org/?code=e35q1eb5a1444905924fc9f3dff4e909&state=`）中的code值，粘贴到代码相应位置。（此code只能使用一次，每次运行代码都需要重新获取）。

# 运行
运行`main.py`。
