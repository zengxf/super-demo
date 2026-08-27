
## 说明
**每个应用有独立的 key，以区分应用**


## 问题
**如果 curl 命令如果出错**，如：
- `{"code":"bad_request","message":"The browser (or proxy) sent a request that this server could not understand.","status":400}`

**可用 Bruno 或 Postman 测试**


## 参数
- **response_mode 可选 `streaming | blocking`**
- **应用的参数可通过 `运行` 页面，用 F12 查看**


## 测试会话类型的应用
- 投资专家： http://192.168.3.192/chat/7o0r9wramcdNi1XY


---
---


## 测试 - 查看版本
```bash
curl http://192.168.3.192/console/api/version?current_version=1.8.1
```


## 测试 - 应用 01 "SQL_生成器_test"
```bash
API_KEY=app-rPfvglhN4bwiZYyVOgBKZTnX-***
echo $API_KEY

curl -X POST \
-H "Authorization: Bearer ${API_KEY}" \
-H "Content-Type: application/json" \
-d '
{
  "inputs": {
    "A": "MySQL",
    "default_input": "查询用户表前10条数据"
  },
  "response_mode": "blocking",
  "user": "zxfeng"
}
' \
http://192.168.3.192/v1/completion-messages
```


## 测试 - 应用 02 "公司基本面_test"
```bash
API_KEY=app-ns5DLbZWIwzaNbqo01GQR6Mj-***
echo $API_KEY

curl -X POST \
-H "Authorization: Bearer ${API_KEY}" \
-H "Content-Type: application/json" \
-d '
{
  "inputs": {
    "stock_code": "000001",
    "date": "2026-02-04"
  },
  "query": "ok",
  "response_mode": "streaming",
  "user": "zxfeng"
}
' \
http://192.168.3.192/v1/chat-messages
```

- ***不支持 blocking 模式***
  - `{"code": "invalid_param", "message": "Agent Chat App does not support blocking mode", "status": 400}`


## 测试 - 应用 03 "聊天助手_test"
```bash
API_KEY=app-FGPkGYGvMkD5dkvCJaiajmxG-***
echo $API_KEY

curl -X POST \
-H "Authorization: Bearer ${API_KEY}" \
-H "Content-Type: application/json" \
-d '
{
  "inputs": {},
  "query": "What are the specs of the iPhone 17 Pro Max?",
  "response_mode": "blocking",
  "user": "zxfeng"
}
' \
http://192.168.3.192/v1/chat-messages
```


## 测试 - 应用 10 "提取CSV输出Json_test"
```bash
API_KEY=app-vkHys9VM80Pfs9Uxd4V1mbIm-***
echo $API_KEY

curl -X POST \
-H "Authorization: Bearer ${API_KEY}" \
-H "Content-Type: application/json" \
-d '
{
  "inputs": {},
  "query": "提取内容",
  "files": [{
    "type": "document",
    "transfer_method": "local_file",
    "upload_file_id": "e061c736-6eca-44c8-a046-dec5218ec2e5",
    "url": ""
  }],
  "response_mode": "blocking",
  "user": "zxfeng"
}
' \
http://192.168.3.192/v1/chat-messages
```

- `文件` 参数内容可通过 "**运行**" -> 上传文件 -> 输入 `提取内容` 后，进行请求 -> 查看参数