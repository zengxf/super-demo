# 服务支持-SearXNG-安装



---
## 简介
- SearXNG 的核心身份是一个元搜索引擎（Metasearch Engine），它并不直接爬取网页，而是扮演一个“中转站”和“聚合者”的角色。


---
## 安装 (通过 Docker)
```bash
# 启动本地实例
docker run -d --name searxng -p 8080:8080 searxng/searxng

# 测试本地 API (需参考 "问题 1" 开启 JSON 格式)
curl 'http://localhost:8080/search?q=hello&format=json'
```

- **访问页面**
  - http://localhost:8080/
    - 可以**直接进行搜索**
- 第一次访问，可先设置**首选项**
  - http://localhost:8080/preferences
- **与官网搜索对比**
  - 搜索：`平安股价`
  - 官网：https://searxng.site/searxng/search   (`0.4 秒`)
  - 本地：http://localhost:8080/search          (`1.7 秒`)



---
## 问题
### 1. 403 Forbidden
```bash
# 测试
curl 'http://localhost:8080/search?q=searxng&format=json'
```

#### 输出
```xml
<!doctype html>
<html lang=en>
<title>403 Forbidden</title>
<h1>Forbidden</h1>
<p>You don't have the permission to access the requested resource. It is either read-protected or not readable by the server.</p>
```

#### 处理
```bash
docker exec -it searxng vi /etc/searxng/settings.yml
```

- 在配置文件中找到 `search:` 部分，**添加 `json` 到 `formats` 列表中**：
```yml
search:
  # ... 其他配置 ...
  formats:
    - html
    - json   # <--- 确保这一行存在
```

- **重启容器**
```bash
docker restart searxng
```


### 2. Dify 插件配置 invalid_param
- 添加配置时的请求
- http://localhost/console/api/workspaces/current/tool-provider/builtin/langgenius/searxng/searxng/add

#### 添加配置请求时的响应
```json
{
    "code": "invalid_param",
    "message": "req_id: d9f08561d9 PluginInvokeError: {\"args\":{},\"error_type\":\"ToolProviderCredentialValidationError\",\"message\":\"HTTPConnectionPool(host='localhost', port=8080): Max retries exceeded with url: \/?q=SearXNG\\u0026time_range=day\\u0026format=json\\u0026categories=general (Caused by NewConnectionError(\\\"HTTPConnection(host='localhost', port=8080): Failed to establish a new connection: [Errno 111] Connection refused\\\"))\"}",
    "status": 400
}
```

#### 处理
- 用主机 IP

```bash
C:\Users\xx> ipconfig

Windows IP 配置

以太网适配器 以太网:

   连接特定的 DNS 后缀 . . . . . . . :
   本地链接 IPv6 地址. . . . . . . . : fe80::33f5:309f:3d67:a76a%3
   IPv4 地址 . . . . . . . . . . . . : 192.168.3.181
   子网掩码  . . . . . . . . . . . . : 255.255.255.0
   默认网关. . . . . . . . . . . . . : 192.168.3.2
```

- 使用：`http://192.168.3.181:8080` 即可