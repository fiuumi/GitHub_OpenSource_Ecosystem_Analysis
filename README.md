github_crawler/
├── config/
│   ├── keywords.py                    # 60词关键词词典
│   └── targets.py                     # 12目标 + 分页生成（★改造1）
├── core/
│   ├── crawler.py                     # 引擎 + 多目标调度（★改造2/3）
│   ├── fetcher.py                     # HTTP请求
│   ├── parser.py                      # HTML解析
│   ├── url_manager.py                 # URL队列
│   ├── keyword_analyzer.py            # 关键词扫描
│   └── storage.py                     # 数据持久化
├── scripts/
│   ├── run_all.py                     # 批量爬取 + 自动分析（★改造3）
│   └── analysis/
│       ├── step1_data_integration.py  # 数据清洗（★改造2）
│       ├── step2_language_analysis.py # 语言热度
│       ├── step3_topic_wordcloud.py   # TF-IDF词云
│       ├── step4_portal_comparison.py # 门户对比
│       └── step5_cooccurrence_network.py # 共现网络


# 一键全流水线（爬取12目标 + 5个分析）
python scripts/run_all.py --analysis --delay 2.0

# 仅Trending + 分析
python scripts/run_all.py --analysis --trending

# 仅Topics + 分析  
python scripts/run_all.py --analysis --topics

# 快速测试（前3个目标 + 分析）
python scripts/run_all.py --analysis --limit 3 --delay 1.0

# 仅爬取（不分析）
python scripts/run_all.py --no-analysis
