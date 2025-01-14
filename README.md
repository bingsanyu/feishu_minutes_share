基于阿里云函数计算和飞书自建应用实现会议结束后自动推送妙记消息给指定用户并授予其权限。

![image](https://github.com/bingsanyu/feishu_minutes_share/assets/66949416/d6cd62c3-4688-4b6f-bf14-fb3e719ae198)

> *[飞书回调限制](https://open.feishu.cn/document/ukTMukTMukTM/uYDNxYjL2QTM24iN0EjN/event-subscription-configure-/encrypt-key-encryption-configuration-case#9cd4c9b1)要求"应用收到HTTP POST请求后，需要在3秒内以HTTP200状态码响应该请求"。*

> *但是，从 会议结束的事件发出 到 妙记生成 需要10秒左右的时间。因此，飞书的回调接口实现应该尽量少做事，收到回调后马上返回，同时再异步调用真正的业务。*

> *参考：https://github.com/wujianguo/feishu-chatgpt-access*

> 为什么不直接使用单个函数异步调用？答：阿里云函数计算的单个函数在有http触发器时不能创建其他触发器，而我们需要一个定时触发器来不断刷新token。

## 1. 配置 飞书企业自建应用

1. 在[飞书开放平台](https://open.feishu.cn/app/)新建一个企业自建应用。
2. 点击`应用功能-添加应用能力`，添加`网页应用`和`机器人`。
3. 点击`开发配置-权限管理-API权限`，开启下面的权限。
    - contact:contact:readonly_as_app
    - contact:user.employee_id:readonly
    - docs:doc
    - ehr:employee:readonly
    - im:message
    - vc:meeting.all_meeting:readonly
    - vc:meeting:readonly
    - vc:record
    - vc:record:readonly
4. 点击`开发配置-事件订阅-已添加事件`，添加下面的事件。
    - vc.meeting.all_meeting_ended_v1
5. 点击`开发配置-安全设置-重定向URL`，添加任意一个URL。例如：
    - https://open.feishu.cn/api-explorer/loading
6. 发布版本并由企业管理员进行审核。

## 2. 配置 阿里云-函数计算FC

### 2.1 创建异步事件函数

1. 创建函数
2. 使用内置运行时创建
3. 函数名称：async_http
4. 请求处理程序类型：处理事件请求
5. 运行环境：Python 3.10
6. 使用示例代码
7. 创建完成后，复制本仓库中 ```index.py``` 中的代码来覆盖默认的  ```index.py```。
8. 新建代码文件 ```share_minutes.py```，将本仓库中 ```share_minutes.py``` 中的代码复制进去。
9. 点击部署代码
10. 点击触发器管理，添加一个触发器，触发类型为`事件总线EventBridge`，事件模式内容为
    ```
    {
        "source": [
            {
                "anything-but": {
                    "prefix": "acs."
                }
            }
        ]
    }
    ```
11. 再添加一个定时触发器，触发间隔 `90分钟`，触发消息为 `need_refresh`。
12. 点击函数配置，添加环境变量
    - ALIYUN_ACCESS_KEY_ID: 阿里云的 accessKeyId
    - ALIYUN_ACCESS_KEY_SECRET: 阿里云的 accessKeySecret
    - ALIYUN_OSS_BUCKET_NAME: 阿里云OSS对象存储的bucket名
    - ALIYUN_OSS_ENDPOINT: 阿里云OSS对象存储的endpoint
    - CODE: 将链接`https://open.feishu.cn/open-apis/authen/v1/user_auth_page_beta?app_id={app_id}&redirect_uri={redirect_uri}` 中的`{app_id}`替换为你所建应用的`App ID`，`{redirect_uri}`替换为你设置的`重定向URL`。打开修改后的链接，出现飞书授权登录页面，点击`授权`，等待网页重定向。复制重定向后url（例如`https://open.feishu.cn/api-explorer/loading/?code=e35q1eb5a1444905924fc9f3dff4e909&state=`）中的code值。
    - FEISHU_APP_ID: 飞书自建应用的app_id
    - FEISHU_APP_SECRET: 飞书自建应用的app_secret
    - FEISHU_AUTHORIZED_USERS_ID_LIST: 要接收会议推送的用户ID，可在飞书管理后台的成员详情中找到。使用英文逗号分隔（例如 `12qw34as,09oikjnb` ）

### 2.2 创建http函数

1. 创建函数
2. 使用自定义运行时创建
3. 函数名称：feishu_access
4. 请求处理程序类型：处理http请求
5. 运行环境：Python 3.10
6. 使用示例代码
7. 创建完成后，点击函数代码，查看函数代码，复制本仓库中 ```app.py``` 中的代码来覆盖默认的  ```app.py```。
8. 点击部署代码
9. 点击函数配置，添加环境变量
   - ALIYUN_ACCESS_KEY_ID: 阿里云的 accessKeyId
   - ALIYUN_ACCESS_KEY_SECRET: 阿里云的 accessKeySecret
   - ALIYUN_FC_ASYNC_TASK_SERVICE_NAME: async_http 函数所在的服务名
   - ALIYUN_FC_ASYNC_TASK_FUNCTION_NAME: async_http 函数的名字，即为 async_http
   - ALIYUN_FC_ENDPOINT: 如 12345.cn-hangzhou.fc.aliyuncs.com，参考 https://help.aliyun.com/document_detail/52984.html
10. 将飞书自建应用中事件订阅里的请求地址变更为此http函数触发器管理里的地址。
