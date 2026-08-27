# Claude Code (CC) 使用


## 参考
- https://dash.aiweber.com/installation
- 邀请 https://dash.aiweber.com/invite/2G6WEO


## 安装
- **步骤 1: 安装 Git Bash (如果尚未安装)**
- **步骤 2: 安装 Node.js (如果尚未安装)**
  - 需要 Node.js 18+ 版本
  - `node --version`
- **步骤 3: 在「API密钥」界面配置一个 API KEY**
  - https://dash.aiweber.com/api-keys
- **步骤 4: 安装 CC 客户端**
  - `npm install -g @anthropic-ai/claude-code@2.1.15` (指定版本)
  - `npm install -g @anthropic-ai/claude-code` (安装或更新到最新版本)
  - `npm uninstall -g @anthropic-ai/claude-code`
- **步骤 5: 创建 settings.json 配置文件**
  - 前往 `C:\Users\[用户名]\.claude\` 目录，如果该目录不存在，请先在终端执行一次 `claude` 命令，目录会自动创建。
  - 在 `C:\Users\[用户名]\.claude\` 目录下创建 `settings.json` 文件，内容如下：
```js
{
    "env": {
        "ANTHROPIC_API_KEY": "你的API密钥",
        "ANTHROPIC_BASE_URL": "https://user-api-01.aiweber.com",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
    },
    "permissions": {
        "allow": [],
        "deny": []
    }
    , "apiKeyHelper": "echo '你的API密钥'"
}

// 有上面的 env.key，apiKeyHelper 可以不用设置
// , "apiKeyHelper": "echo '你的API密钥'"
```
- **步骤 6: 启动 CC 客户端**
  - `claude`


## 命令
- `/init` 初始化 CLAUDE.md
- `/status` 查看使用的模型状态


## 问题处理
```bash
# 1. 设置 proxy
# set HTTPS_PROXY=http://127.0.0.1:7890
set HTTP_PROXY=http://127.0.0.1:7890

# 2. 启动运行
claude

# 3. 登录验证
选择等 2 个登录验证，然后用 Google 账号认证

# 4. 回来继续 Ctrl + C 退出

# 5. 再启动
claude
```


## 配置
- **在 `~/.claude` 目录下**
- 改 **settings.json**

## 使用 AiWeber
- https://dash.aiweber.com/installation
```js
{
    "env": {
        "ANTHROPIC_API_KEY": "sk-ant-my-pri",
        "ANTHROPIC_BASE_URL": "https://user-api-01.aiweber.com",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
    },
    "permissions": {
        "allow": [],
        "deny": []
    }
}
```


## 使用 BigModel
- https://docs.bigmodel.cn/cn/guide/develop/claude#方式三%EF%BC%9A手动配置
```js
{
  "env": {
    "ANTHROPIC_API_KEY": "my-pri.Dbj4sY****",
    "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "ANTHROPIC_MODEL": "GLM-5.1",
    "ANTHROPIC_SMALL_FAST_MODEL": "GLM-5.1",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "GLM-5.1",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "GLM-5.1",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "GLM-5.1"
  },
  "permissions": {
    "allow": [],
    "deny": []
  }
}
```


## 使用 MiniMax
- https://platform.minimaxi.com/docs/coding-plan/claude-code#手动编辑配置文件
```js
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.minimaxi.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "sk-api-my-pri-3PqoE-my-pri-***",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1,
    "ANTHROPIC_MODEL": "MiniMax-M2.7",
    "ANTHROPIC_SMALL_FAST_MODEL": "MiniMax-M2.7",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "MiniMax-M2.7",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "MiniMax-M2.7",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "MiniMax-M275"
  },
  "permissions": {
    "allow": [],
    "deny": []
  }
}
```


## 使用 Skill
### 安装 skill-creator
```bash
# 1. 添加市场源
/plugin marketplace add anthropics/skills

# 2. 安装插件包
/plugin install example-skills@anthropic-agent-skills

# 查看所有的 skills
/skills
```

### 示例 1 - 下载视频 Skill
- https://zhuanlan.zhihu.com/p/1998522824734815001
```bash
# 1 搜
帮我搜一下 GitHub 上下载视频最屌的开源项目。

# 2 打包
https://github.com/yt-dlp/yt-dlp
把这个项目打包成 Skill，以后我只要给你链接，你就帮我下载视频。

# 3 测试
试试下载这个视频 https://www.youtube.com/watch?v=GqjvaBUk3Tc&t=9s
```

### 安装 financial-services-plugins
- https://zhuanlan.zhihu.com/p/2010421123465111104
```bash
# git bash 执行下面命令 （注：不要进入 claude）

# 1. 添加官方市场
claude plugin marketplace add anthropics/financial-services-plugins

# 2. 安装核心插件
claude plugin install financial-analysis@financial-services-plugins

# 3. 根据需要安装具体功能模块
claude plugin install investment-banking@financial-services-plugins
claude plugin install equity-research@financial-services-plugins
claude plugin install private-equity@financial-services-plugins

# 卸载插件
claude plugin uninstall financial-analysis@financial-services-plugins
claude plugin uninstall investment-banking@financial-services-plugins
claude plugin uninstall equity-research@financial-services-plugins
claude plugin uninstall private-equity@financial-services-plugins

# 查看已安装插件
claude plugin list
```
- 测试
```bash
# 进入 cc
claude

# 激活对应功能
/financial-analysis:dcf     # DCF 估值模型

# 以 A 股"蔚蓝锂芯"为例
5         # 使用输入的名称
蔚蓝锂芯  # 输入名称


# 其他
/financial-analysis:comps   # 可比公司分析
```