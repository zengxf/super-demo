#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财经新闻 RSS 抓取脚本"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import urllib.request
import xml.etree.ElementTree as ET
import html
import re
from datetime import datetime
from collections import defaultdict
import json
import ssl

# RSS 源配置
RSS_SOURCES = {
    "36氪": "https://www.36kr.com/feed",
    "虎嗅": "https://rss.huxiu.com/",
    "财新网": "https://plink.anyfeeder.com/weixin/caixinwang",
    "第一财经": "https://plink.anyfeeder.com/weixin/CBNweekly2008",
    "界面新闻·财经": "https://plink.anyfeeder.com/jiemian/finance",
    "经济观察网": "https://plink.anyfeeder.com/eeo",
    "21世纪经济报道": "https://plink.anyfeeder.com/weixin/jjbd21",
    "华尔街见闻": "https://plink.anyfeeder.com/weixin/wallstreetcn",
    "雪球·今日话题": "https://xueqiu.com/hots/topic/rss",
    "中国新闻网·财经": "https://www.chinanews.com.cn/rss/finance.xml",
    "纽约时报中文网": "http://cn.nytimes.com/rss/news.xml",
}

# 关键词分类 - 更精准的财经关键词
CATEGORIES = {
    "宏观经济": [
        "GDP", "CPI", "PPI", "降息", "降准", "加息", "货币", "财政", "外贸", 
        "进出口", "外资", "投资", "消费", "通胀", "通缩", "经济", "宏观",
        "央行", "美联储", "汇率", "人民币", "美元", "欧元", "关税", "贸易战",
        "复苏", "增长", "放缓", "下行", "企稳", "PMI", "LPR", "存款", "贷款",
        "逆回购", "SLF", "MLF", "社融", "M2", "财政政策", "货币政策", "利率",
        "国债", "地方债", "房地产", "房价", "限购", "限贷", "LPR"
    ],
    "股市行情": [
        "A股", "股市", "大盘", "指数", "上证", "深证", "创业板", "科创板",
        "北交所", "港股", "美股", "纳斯达克", "道琼斯", "标普", "涨幅", "跌幅",
        "涨停", "跌停", "IPO", "上市", "退市", "市值", "估值", "市盈率",
        "成交量", "北向资金", "南向资金", "主力", "散户", "持仓", "个股", "板块",
        "股", "证券", "收盘", "开盘", "交易", "恒指", "道指", "纳指"
    ],
    "金融政策": [
        "证监会", "银保监会", "金融监管", "监管", "政策", "法规", "IPO", "注册制", "并购",
        "重组", "再融资", "减持", "增持", "回购", "分红", "配股", "转债",
        "资管", "理财", "信托", "保险", "券商", "银行", "风控", "合规",
        "处罚", "立案", "调查", "问询", "函", "发审", "审核"
    ],
    "公司财报": [
        "财报", "年报", "季报", "业绩", "营收", "净利润", "利润", "盈利",
        "亏损", "增长", "下滑", "增幅", "降幅", "EPS", "ROE", "负债",
        "资产", "现金流", "收入", "成本", "费用", "利润表", "资产负债表",
        "业绩预告", "业绩快报", "扭亏", "首亏", "预增", "预减"
    ]
}

# 排除关键词（纯商业广告或无关社会新闻）
EXCLUDE_KEYWORDS = [
    "广告", "推广", "优惠", "促销", "抽奖", "福利", "免费", "秒杀",
    "整形", "美容", "减肥", "养生", "保健品", "药品", "医疗器械",
    "赌博", "色情", "虚假", "谣言", "鸡汤", "八卦", "明星", "娱乐"
]

def fetch_rss(url, source_name):
    """抓取 RSS 源"""
    articles = []
    try:
        # 创建不验证 SSL 证书的上下文
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
            content = response.read().decode('utf-8', errors='replace')
        
        # 尝试解析 XML
        root = ET.fromstring(content)
        
        # 处理 RSS 2.0
        if root.tag == 'rss':
            channel = root.find('channel')
            if channel is not None:
                items = channel.findall('item')
                for item in items[:30]:  # 每个源最多取30条
                    title = item.find('title')
                    link = item.find('link')
                    desc = item.find('description')
                    pub_date = item.find('pubDate')
                    
                    title_text = html.unescape(title.text) if title is not None and title.text else ""
                    link_text = link.text if link is not None and link.text else ""
                    desc_text = html.unescape(desc.text) if desc is not None and desc.text else ""
                    date_text = pub_date.text if pub_date is not None and pub_date.text else ""
                    
                    if title_text and link_text:
                        articles.append({
                            "title": title_text.strip(),
                            "link": link_text.strip(),
                            "desc": desc_text[:200] if desc_text else "",
                            "date": date_text,
                            "source": source_name
                        })
        
        # 处理 Atom
        elif root.tag == 'feed':
            entries = root.findall('entry')
            for entry in entries[:30]:
                title = entry.find('title')
                link = entry.find('link')
                summary = entry.find('summary')
                updated = entry.find('updated')
                
                title_text = html.unescape(title.text) if title is not None and title.text else ""
                link_text = link.get('href') if link is not None and link.get('href') else ""
                summary_text = html.unescape(summary.text) if summary is not None and summary.text else ""
                date_text = updated.text if updated is not None else ""
                
                if title_text and link_text:
                    articles.append({
                        "title": title_text.strip(),
                        "link": link_text.strip(),
                        "desc": summary_text[:200] if summary_text else "",
                        "date": date_text,
                        "source": source_name
                    })
                    
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
    
    return articles

def is_financial_related(title, desc):
    """判断内容是否与财经高度相关"""
    text = (title + " " + desc).lower()
    
    # 排除明显无关内容
    for kw in EXCLUDE_KEYWORDS:
        if kw in text:
            return False
    
    # 检查是否包含财经关键词
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in text:
                return True
    
    return False

def categorize_article(title, desc):
    """分类文章"""
    text = (title + " " + desc).lower()
    
    scores = defaultdict(int)
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in text:
                scores[category] += 1
    
    if not scores:
        return "财经要闻"  # 默认分类
    
    return max(scores, key=scores.get)

def main():
    """主函数"""
    print("正在抓取财经新闻...")
    
    all_articles = []
    
    # 抓取所有 RSS 源
    for source_name, url in RSS_SOURCES.items():
        print(f"抓取: {source_name}")
        articles = fetch_rss(url, source_name)
        all_articles.extend(articles)
    
    # 过滤和分类
    filtered_articles = []
    for article in all_articles:
        if is_financial_related(article["title"], article["desc"]):
            category = categorize_article(article["title"], article["desc"])
            article["category"] = category
            filtered_articles.append(article)
    
    # 按来源去重（保留最新）
    seen_titles = set()
    unique_articles = []
    for article in filtered_articles:
        # 简化标题进行比较
        simple_title = re.sub(r'[^\w\u4e00-\u9fff]', '', article["title"])[:30]
        if simple_title not in seen_titles:
            seen_titles.add(simple_title)
            unique_articles.append(article)
    
    # 分类统计
    categorized = defaultdict(list)
    for article in unique_articles:
        categorized[article["category"]].append(article)
    
    # 准备结果
    news_items = {
        "财经要闻": [],
        "重点公告": [],
        "机构观点": []
    }
    
    # 财经要闻 - 10条
    for article in categorized.get("宏观经济", [])[:5]:
        news_items["财经要闻"].append(article)
    for article in categorized.get("股市行情", [])[:5]:
        news_items["财经要闻"].append(article)
    
    # 重点公告 - 5条
    for article in categorized.get("公司财报", [])[:3]:
        news_items["重点公告"].append(article)
    for article in categorized.get("金融政策", [])[:2]:
        news_items["重点公告"].append(article)
    
    # 机构观点 - 5个
    opinion_sources = ["雪球·今日话题", "华尔街见闻", "36氪", "虎嗅", "第一财经"]
    opinion_articles = [a for a in unique_articles if a["source"] in opinion_sources][:5]
    for article in opinion_articles:
        news_items["机构观点"].append(article)
    
    # 补充数量
    if len(news_items["财经要闻"]) < 10:
        for article in unique_articles:
            if article not in news_items["财经要闻"] and article not in news_items["重点公告"] and article not in news_items["机构观点"]:
                news_items["财经要闻"].append(article)
                if len(news_items["财经要闻"]) >= 10:
                    break
    
    if len(news_items["重点公告"]) < 5:
        for article in unique_articles:
            if article not in news_items["财经要闻"] and article not in news_items["重点公告"] and article not in news_items["机构观点"]:
                news_items["重点公告"].append(article)
                if len(news_items["重点公告"]) >= 5:
                    break
    
    if len(news_items["机构观点"]) < 5:
        for article in unique_articles:
            if article not in news_items["财经要闻"] and article not in news_items["重点公告"] and article not in news_items["机构观点"]:
                news_items["机构观点"].append(article)
                if len(news_items["机构观点"]) >= 5:
                    break
    
    # 输出 Markdown 格式
    output = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output.append("# 📈 财经要闻速报")
    output.append(f"\n*更新时间: {timestamp}*")
    output.append(f"*\u6765\u6765\u6765\u6765\u6765\u6765\u6765\u6765\u6765\u6765\u6765\u6765\u6765\u6765\u6765 | 共抓取 {len(unique_articles)} 条*\n")
    
    # 财经要闻
    output.append("## 📰 财经要闻")
    output.append("")
    for i, article in enumerate(news_items["财经要闻"], 1):
        output.append(f"{i}. [{article['title']}]({article['link']})")
        output.append(f"   - *来源: {article['source']}*")
    output.append("")
    
    # 重点公告
    output.append("## 📋 重点公告")
    output.append("")
    for i, article in enumerate(news_items["重点公告"], 1):
        output.append(f"{i}. [{article['title']}]({article['link']})")
        output.append(f"   - *来源: {article['source']}*")
    output.append("")
    
    # 机构观点
    output.append("## 💡 机构观点")
    output.append("")
    for i, article in enumerate(news_items["机构观点"], 1):
        output.append(f"{i}. [{article['title']}]({article['link']})")
        output.append(f"   - *来源: {article['source']}*")
    
    output.append("\n---\n")
    output.append("*Powered by now_fin_skill | 财经新闻 RSS 聚合*")
    
    print("\n".join(output))
    return news_items

if __name__ == "__main__":
    main()
