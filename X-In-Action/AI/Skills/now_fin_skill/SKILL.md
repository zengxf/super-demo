---
name: now_fin_skill
description: 财经新闻速报。从多个权威财经 RSS 源抓取最新资讯，提取宏观经济、股市行情、金融政策、公司财报等主题内容，整理为财经要闻、重点公告、机构观点三个模块。触发词："now fin"、"财经新闻"、"今日财经"。
---

# 财经新闻速报 (now_fin_skill)

## 触发方式

- 触发词：`now fin`
- 也支持："财经新闻"、"今日财经"、"财经要闻"

## 使用方法

运行 `./fetch_news.py` 脚本抓取并分析财经新闻：

```bash
cd ~/.openclaw/skills/now_fin_skill
python fetch_news.py
```

脚本会自动：
1. 从 11 个 RSS 源抓取最新文章
2. 过滤与财经高度相关的内容（排除广告、社会新闻）
3. 按宏观经济、股市行情、金融政策、公司财报分类
4. 输出结构化的财经要闻、重点公告、机构观点

## RSS 源列表

| 源 | 网址 |
|---|---|
| 36氪 | https://www.36kr.com/feed |
| 虎嗅 | https://rss.huxiu.com/ |
| 财新网 | https://plink.anyfeeder.com/weixin/caixinwang |
| 第一财经 | https://plink.anyfeeder.com/weixin/CBNweekly2008 |
| 界面新闻·财经 | https://plink.anyfeeder.com/jiemian/finance |
| 经济观察网 | https://plink.anyfeeder.com/eeo |
| 21世纪经济报道 | https://plink.anyfeeder.com/weixin/jjbd21 |
| 华尔街见闻 | https://plink.anyfeeder.com/weixin/wallstreetcn |
| 雪球·今日话题 | https://xueqiu.com/hots/topic/rss |
| 中国新闻网·财经 | https://www.chinanews.com.cn/rss/finance.xml |
| 纽约时报中文网 | http://cn.nytimes.com/rss/news.xml |

## 输出格式

执行脚本后，输出 JSON 格式结果，包含：

- **财经要闻**：10 条（宏观经济 + 股市行情）
- **重点公告**：5 条（公司财报 + 金融政策）
- **机构观点**：5 个（雪球、华尔街见闻等观点性内容）

## 示例输出

```json
{
  "抓取时间": "2026-03-19 17:10:00",
  "财经要闻": [
    {"title": "央行降息25个基点", "link": "https://...", "source": "华尔街见闻"},
    {"title": "A股三大指数收涨", "link": "https://...", "source": "第一财经"}
  ],
  "重点公告": [
    {"title": "阿里巴巴发布2026财年Q3财报", "link": "https://...", "source": "财新网"},
    {"title": "证监会发布IPO新规", "link": "https://...", "source": "证券时报"}
  ],
  "机构观点": [
    {"title": "中信证券：看好A股中长期表现", "link": "https://...", "source": "雪球·今日话题"}
  ]
}
```

## 注意事项

1. 脚本会自动过滤纯广告、无关社会新闻
2. 基于关键词匹配进行分类，可能存在少量误分类
3. 建议在交易日前一天或当天早上使用，获取最新市场动态
4. 如需调整分类逻辑，可修改脚本中的 `CATEGORIES` 关键词配置
