# Coze-单机本地部署
- ref: https://github.com/coze-dev/coze-studio/blob/main/README.zh_CN.md


## 部署
### 1. 下载
- https://github.com/coze-dev/coze-studio/releases
- 下载最新的 `Source code (zip)`
- 解压为 `Coze`
- 复制 `.env.example` 为 `.env`


### 2.启动
```bash
# 导航到 Coze 目录
cd Coze

# 启动容器
docker compose up -d

# 验证 & 重启
docker compose ps
docker compose down
docker compose up -d
```


## 访问 Coze
- http://127.0.0.1:8888/
- 第 1 次，注册账号，访问 http://127.0.0.1:8888/sign **输入用户名、密码点击注册按钮**。

### 管理端
- http://127.0.0.1:8888/admin
- **配置模型**：访问 http://127.0.0.1:8888/admin/#model-management 新增模型。


## 总结
- ***目前 `V0.5.1` 版的工作流，还不是很完善，模型配置完，测试不成功***。