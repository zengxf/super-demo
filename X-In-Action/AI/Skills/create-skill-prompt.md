
## 今日财经 Skill
```js
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