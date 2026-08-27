# OpenClaw-测试


## 参考
- https://docs.openclaw.ai/start/getting-started
- https://docs.openclaw.ai/tools/web


## 安装
```bash
# 全局安装
npm install -g openclaw@latest

# 设置
openclaw onboard --install-daemon

# 启动
openclaw gateway --port 18789 --verbose
```

## 配置
- **文件夹**
```bash
C:\Users\my-pri\.openclaw
```

- 配置
```json
... // web
    "auth": {
      "mode": "token",
      "token": "xx6688----*****"
    },

... // 工具
  "tools": {
    "web": {
      "search": {
        "enabled": true,
        "provider": "brave",
        "apiKey": "brave-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      },
      "fetch": {
        "enabled": true
      }
    }
  }
```

### 改配置命令
```bash
openclaw configure --section web
```


## Web 页面
- http://127.0.0.1:18789/overview
- Overview 输入 token



## 添加下 Anspire skills
```bash
# 1
给我添加下 anspire skills

# 2
用来搜索，可以添加新的 skill，或添加其做为 tool

# 3
将 anspire-xx6688----***** 作为其API 密钥

# 4
将刚才的 key 改成 sk-xx6688----*****
改完后并测试下是否成功，并返回具体的配置文件

# 5
API 请求地址改成 https://plugin.anspire.cn/api/ntsearch/search


# Skills 地址
D:\Install\Web\node-v24.12.0\node_modules\openclaw\skills\anspire
D:\Install\Web\node-v24.12.0\node_modules\openclaw\skills\
sk-xx6688----*****
```

- 改 `skill.md` 文件
```bash
## Quick Start

# Basic search with API key (Authorization header required)
curl -H "Authorization: Bearer sk-xx6688----*****" \
  "https://plugin.anspire.cn/api/ntsearch/search?query=<query>"

# Search with parameters
curl -H "Authorization: Bearer sk-xx6688----*****" \
  "https://plugin.anspire.cn/api/ntsearch/search?query=<query>&limit=5&language=zh"

## API Parameters
| `query` | string | required | Search query |
```

- 测试
```bash
curl -H "Authorization: Bearer sk-xx6688----*****" \
  "https://plugin.anspire.cn/api/ntsearch/search?query=test&limit=5&language=zh"
```


## 使用 MiniMax
- 用 `openclaw onboard --install-daemon` 重置成 MiniMax 就行，然后参考下面的改配置文件
- ref: https://platform.minimaxi.com/docs/solutions/moltbot


## 测试
```bash
当前是用哪个模型

昨天白银大跌的原因，分析下，上网查询可用 anspire skill

当前白银多少钱一克
```


## 创建 now-fin Skill
- Web 会话里面输入
```md
创建一个财经新闻 skill，从下面 rss 中提取最新信息。

RSS 链接如下：
- 36氪 https://www.36kr.com/feed
- 虎嗅 https://rss.huxiu.com/
- 财新网 https://plink.anyfeeder.com/weixin/caixinwang
- 第一财经 https://plink.anyfeeder.com/weixin/CBNweekly2008
- 界面新闻·财经 https://plink.anyfeeder.com/jiemian/finance
- 经济观察网 https://plink.anyfeeder.com/eeo
- 21世纪经济报道 https://plink.anyfeeder.com/weixin/jjbd21
- 华尔街见闻 https://plink.anyfeeder.com/weixin/wallstreetcn
- 雪球·今日话题 https://xueqiu.com/hots/topic/rss
- 中国新闻网·财经 https://www.chinanews.com.cn/rss/finance.xml
- NYT-纽约时报中文网 http://cn.nytimes.com/rss/news.xml

要求是：
1. skill 名称为 now_fin_skill
2. 触发词 "now fin"
3. 筛选并提取关于宏观经济、股市行情、金融政策、公司财报等主题的文章标题及其对应链接，整理为**财经要闻**、**重点公告**、**机构观点** 模块。
4. 注意事项
   - 严格遵循系统提示中定义的日报输出格式（包括 Emoji 添加、标题头、by 信息等）。
   - 输出内容总量应为：**10 条财经要闻、5 条重点公告、5 个机构观点**。
   - 确保所有输出内容与财经高度相关，排除单纯的商业广告或无关的社会新闻。
```