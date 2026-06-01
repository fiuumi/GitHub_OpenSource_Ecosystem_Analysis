# GitHub开源软件技术生态演化趋势的大数据分析

## ——基于 GitHub Trending & Topics 多源数据采集与挖掘设计方案

---

## 1. 项目背景与选题依据

### 1.1 选题背景

GitHub是全球最大的开源软件托管平台，截至2025年拥有超过1亿开发者、4亿仓库，日均新增仓库超20万个。GitHub Trending和GitHub Topics是两个核心内容发现入口：Trending反映短期内社区最关注的项目（**时效性热度**），Topics则按技术主题聚合长期积累的高质量仓库（**主题性深度**）。这两个入口的数据结合起来，可以构建一幅完整的开源技术生态图景——既看到当下的热点风向，也理解各技术领域的长期积累。

本课题利用网络爬虫对GitHub Trending（多语言趋势榜）和GitHub Topics（五大技术主题页）进行系统性采集，运用大数据分析技术揭示全球开源生态的编程语言分布、技术主题演化、Trending与Topics的内容差异，以及各技术栈之间的内在关联。

### 1.2 选题意义

| 维度 | 意义描述 |
|------|----------|
| **学术价值** | 完整实践"云计算与大数据"课程的采集-清洗-分析-可视化全流程 |
| **技术实践** | 验证网络爬虫在英文技术站点的采集能力，练习英文NLP、TF-IDF、网络分析 |
| **趋势洞察** | 通过Trending（短期热度）与Topics（长期深度）的双视角，揭示技术生态的全景 |
| **领域关联** | 分析云原生、大数据、AI等核心领域的语言偏好和技术交叉 |

### 1.3 与本课程关联

- **云计算层面**：Trending/Topics中Kubernetes、Docker、Serverless等云原生项目的分析直接对应云计算主题
- **大数据层面**：采集Hadoop、Spark、Flink等大数据开源项目，实践数据分析全流程
- **技术融合**：分析对象涵盖云计算和大数据的核心技术栈，爬虫本身即是大数据采集层的实践

---

## 2. 爬虫工具适配性评估

### 2.1 目标网站技术验证

| 目标页面 | URL | 验证结果 | 静态化程度 |
|----------|-----|----------|------------|
| Trending总榜 | `github.com/trending` | 纯静态HTML，仓库卡片完整渲染 | ★★★★★ |
| Trending Python | `github.com/trending/python` | 静态HTML，含描述/star数/语言 | ★★★★★ |
| Trending Go | `github.com/trending/go` | 静态HTML，结构同上 | ★★★★★ |
| Trending Rust | `github.com/trending/rust` | 静态HTML | ★★★★★ |
| Trending TypeScript | `github.com/trending/typescript` | 静态HTML | ★★★★★ |
| Trending Java | `github.com/trending/java` | 静态HTML | ★★★★★ |
| Trending C++ | `github.com/trending/c++` | 静态HTML（URL编码为`c%2B%2B`） | ★★★★★ |
| Topics AI | `github.com/topics/artificial-intelligence` | 静态HTML，含主题标签 | ★★★★★ |
| Topics Blockchain | `github.com/topics/blockchain` | 静态HTML | ★★★★★ |
| Topics Cloud | `github.com/topics/cloud-computing` | 静态HTML，3258个仓库 | ★★★★★ |
| Topics Big Data | `github.com/topics/big-data` | 静态HTML，5643个仓库 | ★★★★★ |
| Topics ML | `github.com/topics/machine-learning` | 静态HTML | ★★★★★ |

### 2.2 爬虫能力匹配

| 能力需求 | 爬虫支持 | 匹配说明 |
|----------|----------|----------|
| 静态HTTP请求 | ✅ urllib | GitHub全站SSR |
| HTML文本提取 | ✅ HTMLParser | 提取仓库描述、标题 |
| 链接提取 | ✅ `<a href>`解析 | 提取仓库详情链接、主题标签 |
| 关键词频率统计 | ✅ 内置keywords字典 | 统计语言/技术关键词命中次数 |
| 资源计数 | ✅ link/image/script/style_count | 分析页面结构特征 |
| robots.txt | ✅ 自动检测 | GitHub允许爬取公开页面 |
| JS渲染/登录 | ❌ 不支持 | 不需要 |

### 2.3 数据字段映射

| 爬虫输出字段 | GitHub场景含义 | 分析用途 |
|-------------|---------------|----------|
| `title` | 仓库名（`owner/repo · GitHub`） | 仓库识别 |
| `description` | 仓库一句话描述 | **核心：技术主题NLP分析** |
| `word_count` | 页面文本总词数 | 描述丰富度评估 |
| `link_count` | 页面内链接数 | 页面导航密度/生态关联 |
| `image_count` | 图片数量 | README可视化程度 |
| `script_count` | JS文件数 | 页面交互复杂度 |
| `style_count` | CSS文件数 | 页面工程化程度 |
| `keywords` | 关键词命中次数 | **核心：技术热度统计** |
| `url` | 页面URL | 分类标记（Trending/Topics） |

---

## 3. 数据源设计

### 3.1 数据源概览

| 编号 | 数据源 | 入口URL | 内容 | 预期数据量 |
|:----:|--------|---------|------|:----------:|
| 1 | Trending总榜 | `github.com/trending` | 全语言热门仓库 | ~25条 |
| 2 | Trending Python | `github.com/trending/python` | Python热门项目 | ~25条 |
| 3 | Trending Go | `github.com/trending/go` | Go热门项目 | ~25条 |
| 4 | Trending Rust | `github.com/trending/rust` | Rust热门项目 | ~25条 |
| 5 | Trending TypeScript | `github.com/trending/typescript` | TS热门项目 | ~25条 |
| 6 | Trending Java | `github.com/trending/java` | Java热门项目 | ~25条 |
| 7 | Trending C++ | `github.com/trending/c%2B%2B` | C++热门项目 | ~25条 |
| 8 | Topics AI | `github.com/topics/artificial-intelligence` | AI主题聚合 | ~30条 |
| 9 | Topics Blockchain | `github.com/topics/blockchain` | 区块链主题 | ~30条 |
| 10 | Topics Cloud | `github.com/topics/cloud-computing` | 云计算主题 | ~30条 |
| 11 | Topics Big Data | `github.com/topics/big-data` | 大数据主题 | ~30条 |
| 12 | Topics ML | `github.com/topics/machine-learning` | 机器学习主题 | ~30条 |

**总计：约330条仓库数据**

### 3.2 两大入口的本质差异

| 维度 | GitHub Trending | GitHub Topics |
|------|-----------------|---------------|
| **时间维度** | 短期热度（今日/本周/本月） | 长期积累（历史全部） |
| **排序逻辑** | 近期star增速 | 总star数/更新频率 |
| **内容类型** | 新兴项目、潮流工具 | 成熟框架、经典教材 |
| **语言分布** | 新兴语言（Go/Rust/TS）占比高 | 传统语言（Python/Java）占比高 |
| **描述特征** | 简洁有力，突出卖点 | 详细完整，技术规范 |
| **分析价值** | 反映**当下技术风向** | 反映**领域技术沉淀** |

> 双入口对比是本方案的核心创新点：Trending回答"现在什么最火"，Topics回答"什么技术最扎实"。

---

## 4. 大数据采集方案

### 4.1 统一关键词词典（60词，6大维度）

```python
# === 维度1：编程语言（15词）===
LANGUAGE_KEYWORDS = [
    "Python", "Go", "Rust", "TypeScript", "JavaScript", "Java",
    "C++", "C", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "Dart"
]

# === 维度2：云原生与容器（10词）===
CLOUD_NATIVE_KEYWORDS = [
    "Kubernetes", "Docker", "container", "microservice", "serverless",
    "DevOps", "Istio", "Helm", "Terraform", "service-mesh"
]

# === 维度3：大数据技术栈（10词）===
BIGDATA_KEYWORDS = [
    "Hadoop", "Spark", "Flink", "Kafka", "data-warehouse", "data-lake",
    "ETL", "streaming", "MapReduce", "Elasticsearch"
]

# === 维度4：人工智能（10词）===
AI_KEYWORDS = [
    "machine-learning", "deep-learning", "neural-network", "NLP",
    "computer-vision", "LLM", "GPT", "transformer", "OpenAI", "agent"
]

# === 维度5：区块链与Web3（8词）===
BLOCKCHAIN_KEYWORDS = [
    "blockchain", "Ethereum", "Web3", "smart-contract", "DeFi",
    "cryptocurrency", "Solidity", "NFT"
]

# === 维度6：数据库与存储（7词）===
DATABASE_KEYWORDS = [
    "database", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "NoSQL"
]

ALL_KEYWORDS = (
    LANGUAGE_KEYWORDS + CLOUD_NATIVE_KEYWORDS + BIGDATA_KEYWORDS +
    AI_KEYWORDS + BLOCKCHAIN_KEYWORDS + DATABASE_KEYWORDS
)
```

### 4.2 采集命令（12个任务）

#### Trending系列（7个任务）

```bash
# 任务1：Trending总榜（全语言）
python crawler.py \
  "https://github.com/trending" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_trending_all

# 任务2：Trending Python
python crawler.py \
  "https://github.com/trending/python" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_trending_python

# 任务3：Trending Go
python crawler.py \
  "https://github.com/trending/go" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_trending_go

# 任务4：Trending Rust
python crawler.py \
  "https://github.com/trending/rust" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_trending_rust

# 任务5：Trending TypeScript
python crawler.py \
  "https://github.com/trending/typescript" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_trending_ts

# 任务6：Trending Java
python crawler.py \
  "https://github.com/trending/java" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_trending_java

# 任务7：Trending C++
python crawler.py \
  "https://github.com/trending/c%2B%2B" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_trending_cpp
```

#### Topics系列（5个任务）

```bash
# 任务8：Topics - Artificial Intelligence
python crawler.py \
  "https://github.com/topics/artificial-intelligence" \
  --max-pages 35 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_topics_ai

# 任务9：Topics - Blockchain
python crawler.py \
  "https://github.com/topics/blockchain" \
  --max-pages 35 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_topics_blockchain

# 任务10：Topics - Cloud Computing
python crawler.py \
  "https://github.com/topics/cloud-computing" \
  --max-pages 35 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_topics_cloud

# 任务11：Topics - Big Data
python crawler.py \
  "https://github.com/topics/big-data" \
  --max-pages 35 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_topics_bigdata

# 任务12：Topics - Machine Learning
python crawler.py \
  "https://github.com/topics/machine-learning" \
  --max-pages 35 --max-depth 1 --delay 2.0 \
  --output-dir ./output/gh_topics_ml
```

### 4.3 批量采集脚本

```bash
#!/bin/bash
# run_all_crawlers.sh
# 一键执行12个采集任务

OUTPUT_BASE="./output"
mkdir -p "$OUTPUT_BASE"

# ===== Trending系列 =====
echo "===== [1/7] Trending: All Languages ====="
python crawler.py "https://github.com/trending" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_trending_all"

echo "===== [2/7] Trending: Python ====="
python crawler.py "https://github.com/trending/python" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_trending_python"

echo "===== [3/7] Trending: Go ====="
python crawler.py "https://github.com/trending/go" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_trending_go"

echo "===== [4/7] Trending: Rust ====="
python crawler.py "https://github.com/trending/rust" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_trending_rust"

echo "===== [5/7] Trending: TypeScript ====="
python crawler.py "https://github.com/trending/typescript" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_trending_ts"

echo "===== [6/7] Trending: Java ====="
python crawler.py "https://github.com/trending/java" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_trending_java"

echo "===== [7/7] Trending: C++ ====="
python crawler.py "https://github.com/trending/c%2B%2B" \
  --max-pages 30 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_trending_cpp"

# ===== Topics系列 =====
echo "===== [8/12] Topics: AI ====="
python crawler.py "https://github.com/topics/artificial-intelligence" \
  --max-pages 35 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_topics_ai"

echo "===== [9/12] Topics: Blockchain ====="
python crawler.py "https://github.com/topics/blockchain" \
  --max-pages 35 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_topics_blockchain"

echo "===== [10/12] Topics: Cloud Computing ====="
python crawler.py "https://github.com/topics/cloud-computing" \
  --max-pages 35 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_topics_cloud"

echo "===== [11/12] Topics: Big Data ====="
python crawler.py "https://github.com/topics/big-data" \
  --max-pages 35 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_topics_bigdata"

echo "===== [12/12] Topics: Machine Learning ====="
python crawler.py "https://github.com/topics/machine-learning" \
  --max-pages 35 --max-depth 1 --delay 2.0 \
  --output-dir "$OUTPUT_BASE/gh_topics_ml"

echo ""
echo "=========================================="
echo "  全部12个采集任务已完成！"
echo "  数据目录: $OUTPUT_BASE/"
echo "=========================================="
```

---

## 5. 大数据分析方案（五大维度）

### 5.1 维度一：编程语言热度全景分析

**目标**：统计15种编程语言在Trending和Topics中的出现频次，分析语言热度分布与入口差异。

**分析指标**：
- 全局热度TOP15排行
- Trending vs Topics 语言热度对比（Trending反映新兴语言优势，Topics反映传统语言积累）
- 各语言页（如Trending Python）的关键词自引用率

**预期图表**：
- 水平柱状图：语言热度TOP15
- 分组柱状图：Trending vs Topics 语言热度对比

### 5.2 维度二：技术主题TF-IDF与词云分析

**目标**：对仓库描述进行英文NLP分析，提取高权重特征词，生成主题词云。

**分析流程**：
1. 预处理：小写转换 → 正则清洗 → 停用词过滤 → 词干提取（NLTK PorterStemmer）
2. TF-IDF：计算unigram和bigram的TF-IDF权重
3. 词云：按平台（Trending/Topics）分别生成
4. 对比：双平台TOP20关键词对比

**预期图表**：
- WordCloud词云图（Trending / Topics 各一张）
- 水平柱状图：双平台TF-IDF TOP20对比

### 5.3 维度三：Trending vs Topics 内容生态对比

**目标**：对比短期热度入口（Trending）与长期深度入口（Topics）在内容特征上的系统性差异。

**分析指标**：

| 指标 | 计算方式 | 解读 |
|------|----------|------|
| 平均描述长度 | `mean(word_count)` | Topics项目描述更详尽 |
| 平均链接密度 | `mean(link_count)` | Topics生态关联更丰富 |
| 平均图片数 | `mean(image_count)` | README可视化程度 |
| 平均脚本数 | `mean(script_count)` | 页面交互复杂度 |
| 平均样式数 | `mean(style_count)` | 页面工程化程度 |
| 技术标签密度 | 每页的Topics标签链接数 | Topics项目更主动地标记技术领域 |

**预期图表**：
- 雷达图：多维特征对比
- 箱线图：各指标分布差异

### 5.4 维度四：技术领域 × 编程语言 交叉分析

**目标**：分析各技术领域（AI/云原生/大数据/区块链）中编程语言的分布偏好，揭示"什么领域用什么语言"。

**分析矩阵**：

| 领域 \ 语言 | Python | Go | Rust | TS | Java | C++ |
|:----------:|:------:|:--:|:----:|:--:|:----:|:---:|
| AI | ★★★ | ★ | ★ | ★ | ★ | ★★ |
| Cloud Native | ★★ | ★★★ | ★ | ★ | ★ | ★ |
| Big Data | ★★★ | ★ | ★ | ★ | ★★★ | ★ |
| Blockchain | ★ | ★★ | ★★★ | ★★ | ★ | ★ |

**预期图表**：
- 热力图：领域 × 语言 关键词命中矩阵
- 堆叠柱状图：各领域语言构成比例

### 5.5 维度五：技术关键词共现网络分析

**目标**：构建技术关键词之间的共现关系网络，发现技术栈的内在关联结构。

**分析方法**：
1. 遍历每条数据的keywords字典，提取同时出现的关键词对
2. 统计共现频率，过滤低频边（阈值≥2）
3. 使用NetworkX构建无向加权图
4. 计算度中心性和介数中心性
5. 识别连通分量（技术社区簇）

**预期图表**：
- 网络关系图（节点大小=度中心性，边粗细=共现权重，颜色=社区簇）
- 中心性排名表

---

## 6. 完整分析代码（5个脚本）

### 6.1 技术栈

| 层级 | 工具 | 用途 |
|------|------|------|
| 数据处理 | Pandas | 数据读取、清洗、聚合 |
| 英文NLP | NLTK | 分词、词干提取、停用词 |
| 文本分析 | Scikit-learn | TF-IDF计算 |
| 可视化 | Matplotlib + Seaborn | 静态图表 |
| 词云 | WordCloud | 主题词云 |
| 网络分析 | NetworkX | 共现网络构建与分析 |

### 6.2 脚本1：数据整合与清洗

```python
"""
step1_data_integration.py
整合12个数据源的JSON文件，清洗后输出统一DataFrame
"""

import json
import pandas as pd
import os

# 数据源元信息
DATA_SOURCES = {
    # Trending系列
    'gh_trending_all': {'portal': 'Trending', 'sub': 'all', 'type': 'trending'},
    'gh_trending_python': {'portal': 'Trending', 'sub': 'Python', 'type': 'trending'},
    'gh_trending_go': {'portal': 'Trending', 'sub': 'Go', 'type': 'trending'},
    'gh_trending_rust': {'portal': 'Trending', 'sub': 'Rust', 'type': 'trending'},
    'gh_trending_ts': {'portal': 'Trending', 'sub': 'TypeScript', 'type': 'trending'},
    'gh_trending_java': {'portal': 'Trending', 'sub': 'Java', 'type': 'trending'},
    'gh_trending_cpp': {'portal': 'Trending', 'sub': 'C++', 'type': 'trending'},
    # Topics系列
    'gh_topics_ai': {'portal': 'Topics', 'sub': 'AI', 'type': 'topics'},
    'gh_topics_blockchain': {'portal': 'Topics', 'sub': 'Blockchain', 'type': 'topics'},
    'gh_topics_cloud': {'portal': 'Topics', 'sub': 'Cloud', 'type': 'topics'},
    'gh_topics_bigdata': {'portal': 'Topics', 'sub': 'BigData', 'type': 'topics'},
    'gh_topics_ml': {'portal': 'Topics', 'sub': 'ML', 'type': 'topics'},
}


def load_source(source_name, meta):
    """加载单个数据源的JSON"""
    path = os.path.join('output', source_name, 'crawl_report.json')
    if not os.path.exists(path):
        print(f"[WARN] 文件不存在: {path}")
        return pd.DataFrame()

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    if df.empty:
        return df

    # 添加元信息
    for key, val in meta.items():
        df[key] = val
    df['source_name'] = source_name

    # 从title提取repo名
    df['repo_name'] = df['title'].str.split('·').str[0].str.strip()
    df['owner'] = df['repo_name'].str.split('/').str[0]
    df['repo'] = df['repo_name'].str.split('/').str[1]

    return df


def integrate_and_clean():
    """整合所有数据并清洗"""
    dfs = []
    for name, meta in DATA_SOURCES.items():
        df = load_source(name, meta)
        if not df.empty:
            dfs.append(df)
            print(f"[OK] {name}: {len(df)} 条")

    if not dfs:
        raise ValueError("未找到任何数据")

    all_df = pd.concat(dfs, ignore_index=True)
    print(f"\n整合完成: {len(all_df)} 条")

    # === 清洗 ===
    before = len(all_df)

    # 1. URL去重
    all_df = all_df.drop_duplicates(subset=['url'], keep='first')

    # 2. 过滤无意义页面
    all_df = all_df[~all_df['title'].str.contains('Sign in|Page not found', case=False, na=False)]
    all_df = all_df[all_df['word_count'] > 10]

    # 3. 提取有效关键词（>0的）
    def get_active_kws(kw_dict):
        if not isinstance(kw_dict, dict):
            return {}
        return {k: v for k, v in kw_dict.items() if v > 0}

    all_df['active_keywords'] = all_df['keywords'].apply(get_active_kws)

    after = len(all_df)
    print(f"清洗: {before} → {after} 条 (过滤 {before - after})")
    print(f"\n入口分布:\n{all_df['portal'].value_counts()}")
    print(f"\n子类分布:\n{all_df['sub'].value_counts()}")

    # 保存
    os.makedirs('output/analysis', exist_ok=True)
    all_df.to_pickle('output/analysis/cleaned_data.pkl')
    all_df.to_csv('output/analysis/cleaned_data.csv', index=False, encoding='utf-8-sig')
    print("\n[SAVE] 已保存 cleaned_data.pkl / .csv")
    return all_df


if __name__ == '__main__':
    integrate_and_clean()
```

### 6.3 脚本2：编程语言热度分析

```python
"""
step2_language_analysis.py
分析15种编程语言在Trending和Topics中的热度分布
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

LANGUAGES = [
    "Python", "Go", "Rust", "TypeScript", "JavaScript", "Java",
    "C++", "C", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "Dart"
]


def analyze_language_heat(df):
    """统计各语言在各入口的关键词命中次数"""
    records = []
    for _, row in df.iterrows():
        kw = row.get('keywords', {})
        if not isinstance(kw, dict):
            continue
        for lang in LANGUAGES:
            count = kw.get(lang, 0)
            if count > 0:
                records.append({
                    'language': lang,
                    'portal': row.get('portal', 'Unknown'),
                    'sub': row.get('sub', 'Unknown'),
                    'count': count,
                    'url': row['url']
                })
    return pd.DataFrame(records)


def plot_results(lang_df, global_top):
    """绘制两张核心图表"""
    fig, axes = plt.subplots(2, 1, figsize=(14, 16))

    # === 图1：全局TOP15 ===
    top15 = global_top.head(15)
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(top15)))
    ax1 = axes[0]
    bars = ax1.barh(range(len(top15)), top15.values, color=colors, edgecolor='white', linewidth=0.5)
    ax1.set_yticks(range(len(top15)))
    ax1.set_yticklabels(top15.index, fontsize=12)
    ax1.invert_yaxis()
    ax1.set_xlabel('Total Keyword Hits', fontsize=12)
    ax1.set_title('Top 15 Programming Languages on GitHub\n(Trending + Topics Combined)',
                  fontsize=14, fontweight='bold')
    for i, v in enumerate(top15.values):
        ax1.text(v + 0.3, i, str(int(v)), va='center', fontsize=10)

    # === 图2：Trending vs Topics 对比 ===
    ax2 = axes[1]
    pivot = lang_df.groupby(['language', 'portal'])['count'].sum().unstack(fill_value=0)
    # 确保两列都存在
    for col in ['Trending', 'Topics']:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot['total'] = pivot.sum(axis=1)
    top10 = pivot.sort_values('total', ascending=False).head(10).drop(columns=['total'])

    x = np.arange(len(top10))
    w = 0.35
    ax2.bar(x - w/2, top10['Trending'], w, label='Trending', color='#2dba4e', edgecolor='white')
    ax2.bar(x + w/2, top10['Topics'], w, label='Topics', color='#0969da', edgecolor='white')
    ax2.set_xticks(x)
    ax2.set_xticklabels(top10.index, rotation=45, ha='right', fontsize=11)
    ax2.set_ylabel('Keyword Hits', fontsize=12)
    ax2.set_title('Trending vs Topics: Language Heat Comparison',
                  fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)

    plt.tight_layout()
    plt.savefig('output/analysis/language_heat.png', dpi=300, bbox_inches='tight')
    print("[SAVE] output/analysis/language_heat.png")
    plt.close()


def generate_report(global_top, lang_df):
    """生成文本报告"""
    with open('output/analysis/language_report.txt', 'w', encoding='utf-8') as f:
        f.write("=" * 55 + "\n")
        f.write("     Programming Language Heat Analysis\n")
        f.write("=" * 55 + "\n\n")

        f.write("[Global Top 15]\n")
        for i, (lang, cnt) in enumerate(global_top.head(15).items(), 1):
            f.write(f"  {i:2d}. {lang:<15s} {cnt:>4.0f} hits\n")

        f.write("\n[Trending vs Topics]\n")
        pivot = lang_df.groupby(['language', 'portal'])['count'].sum().unstack(fill_value=0)
        for col in ['Trending', 'Topics']:
            if col not in pivot.columns:
                pivot[col] = 0
        pivot['total'] = pivot.sum(axis=1)
        for lang, row in pivot.sort_values('total', ascending=False).head(10).iterrows():
            tr = row.get('Trending', 0)
            tp = row.get('Topics', 0)
            ratio = tr / (tr + tp) * 100 if (tr + tp) > 0 else 0
            f.write(f"  {lang:<15s} Trending:{tr:>3.0f}  Topics:{tp:>3.0f}  "
                   f"Trending%:{ratio:>5.1f}%\n")

    print("[SAVE] output/analysis/language_report.txt")


if __name__ == '__main__':
    df = pd.read_pickle('output/analysis/cleaned_data.pkl')
    lang_df = analyze_language_heat(df)

    if not lang_df.empty:
        global_top = lang_df.groupby('language')['count'].sum().sort_values(ascending=False)
        plot_results(lang_df, global_top)
        generate_report(global_top, lang_df)
        print("[DONE] Language analysis complete")
    else:
        print("[ERROR] No language data found")
```

### 6.4 脚本3：TF-IDF与词云分析

```python
"""
step3_topic_wordcloud.py
对仓库描述进行TF-IDF分析和词云生成
"""

import pandas as pd
import matplotlib.pyplot as plt
import re
import os
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer

# 英文停用词（扩展技术版）
STOPWORDS = set([
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
    'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'been', 'have', 'has',
    'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'can',
    'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
    'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their',
    'github', 'com', 'http', 'https', 'www', 'io', 'org', 'net', 'co',
    'open', 'source', 'free', 'software', 'project', 'tool', 'library', 'framework',
    'app', 'application', 'based', 'using', 'built', 'made', 'simple', 'easy', 'fast',
    'lightweight', 'powerful', 'modern', 'new', 'support', 'supports', 'supported',
    'api', 'cli', 'ui', 'gui', 'version', 'amp', 'lt', 'gt', 'quot', 'nbsp',
    'all', 'any', 'each', 'every', 'some', 'more', 'most', 'other', 'such', 'only',
    'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also', 'back', 'still',
    'well', 'even', 'much', 'many', 'up', 'out', 'down', 'off', 'over', 'under',
    'not', 'no', 'yes', 'get', 'use', 'used', 'one', 'two', 'three', 'first',
    'like', 'way', 'make', 'see', 'know', 'take', 'come', 'go', 'think', 'say',
    'help', 'build', 'create', 'add', 'set', 'run', 'write', 'read', 'need', 'want'
])


def preprocess(text):
    """预处理英文描述"""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s\-/]', ' ', text)
    words = text.split()
    words = [w for w in words if len(w) > 2 and w not in STOPWORDS and not w.isdigit()]
    return ' '.join(words)


def generate_wordcloud(df, portal_name, path):
    """生成词云"""
    subset = df[df['portal'] == portal_name]
    texts = subset['description'].apply(preprocess)
    all_text = ' '.join(texts)
    if not all_text.strip():
        print(f"[WARN] {portal_name} empty text")
        return

    wc = WordCloud(
        width=1600, height=900, background_color='white',
        max_words=200, colormap='tab10', relative_scaling=0.5,
        min_font_size=10, max_font_size=150
    ).generate(all_text)

    plt.figure(figsize=(16, 9))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.title(f'GitHub {portal_name} - Technology Topic Cloud',
              fontsize=18, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches='tight')
    print(f"[SAVE] {path}")
    plt.close()


def compute_tfidf(df, portal_name, top_n=25):
    """计算TF-IDF"""
    subset = df[df['portal'] == portal_name]
    texts = subset['description'].apply(preprocess)
    texts = texts[texts.str.len() > 0]
    if len(texts) < 5:
        return pd.DataFrame()

    vec = TfidfVectorizer(max_features=500, ngram_range=(1, 2), min_df=2, max_df=0.8)
    matrix = vec.fit_transform(texts)
    names = vec.get_feature_names_out()
    scores = matrix.mean(axis=0).A1
    words = list(zip(names, scores))
    words.sort(key=lambda x: x[1], reverse=True)
    return pd.DataFrame(words[:top_n], columns=['keyword', 'tfidf_score'])


def plot_tfidf_compare(trending_tfidf, topics_tfidf):
    """对比两入口的TF-IDF关键词"""
    fig, axes = plt.subplots(1, 2, figsize=(18, 10))

    for ax, df, name, color in zip(
        axes, [trending_tfidf, topics_tfidf],
        ['Trending', 'Topics'], ['#2dba4e', '#0969da']
    ):
        if df.empty:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            continue
        top = df.head(20)
        ax.barh(range(len(top)), top['tfidf_score'], color=color, edgecolor='white')
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(top['keyword'], fontsize=10)
        ax.invert_yaxis()
        ax.set_title(f'{name} - Top 20 TF-IDF Keywords', fontsize=13, fontweight='bold')
        ax.set_xlabel('TF-IDF Score')

    plt.tight_layout()
    plt.savefig('output/analysis/tfidf_comparison.png', dpi=300, bbox_inches='tight')
    print("[SAVE] output/analysis/tfidf_comparison.png")
    plt.close()


if __name__ == '__main__':
    df = pd.read_pickle('output/analysis/cleaned_data.pkl')
    os.makedirs('output/analysis', exist_ok=True)

    # 词云
    generate_wordcloud(df, 'Trending', 'output/analysis/wordcloud_trending.png')
    generate_wordcloud(df, 'Topics', 'output/analysis/wordcloud_topics.png')

    # TF-IDF
    t_tfidf = compute_tfidf(df, 'Trending')
    p_tfidf = compute_tfidf(df, 'Topics')

    if not t_tfidf.empty:
        t_tfidf.to_csv('output/analysis/tfidf_trending.csv', index=False)
    if not p_tfidf.empty:
        p_tfidf.to_csv('output/analysis/tfidf_topics.csv', index=False)

    plot_tfidf_compare(t_tfidf, p_tfidf)
    print("[DONE] TF-IDF and wordcloud complete")
```

### 6.5 脚本4：Trending vs Topics 对比分析

```python
"""
step4_portal_comparison.py
对比Trending与Topics的内容生态差异 + 领域×语言交叉分析
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 技术领域关键词分类
TECH_DOMAINS = {
    'CloudNative': ["Kubernetes", "Docker", "container", "microservice", "serverless",
                     "DevOps", "Istio", "Terraform", "service-mesh"],
    'BigData':     ["Hadoop", "Spark", "Flink", "Kafka", "data-warehouse", "data-lake",
                     "ETL", "streaming", "MapReduce", "Elasticsearch"],
    'AI':          ["machine-learning", "deep-learning", "neural-network", "NLP",
                     "computer-vision", "LLM", "GPT", "transformer", "OpenAI", "agent"],
    'Blockchain':  ["blockchain", "Ethereum", "Web3", "smart-contract", "DeFi",
                     "cryptocurrency", "Solidity", "NFT"],
    'Database':    ["database", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "NoSQL"],
}

LANGUAGES = ["Python", "Go", "Rust", "TypeScript", "Java", "C++", "C"]


def structure_comparison(df):
    """页面结构特征对比"""
    metrics = df.groupby('portal').agg({
        'word_count': ['mean', 'median'],
        'link_count': ['mean', 'median'],
        'image_count': ['mean', 'median'],
        'script_count': ['mean', 'median'],
        'style_count': ['mean', 'median']
    }).round(2)
    metrics.columns = ['_'.join(c) for c in metrics.columns]
    return metrics


def plot_radar(df):
    """绘制多维雷达图"""
    portals = df['portal'].unique()
    metrics = structure_comparison(df)

    cats = ['Avg Words', 'Avg Links', 'Avg Images', 'Avg Scripts', 'Avg Styles']
    raw = {
        'Avg Words': metrics['word_count_mean'].values,
        'Avg Links': metrics['link_count_mean'].values,
        'Avg Images': metrics['image_count_mean'].values,
        'Avg Scripts': metrics['script_count_mean'].values,
        'Avg Styles': metrics['style_count_mean'].values
    }

    # Min-Max归一化
    norm = {}
    for c in cats:
        v = raw[c]
        mi, ma = v.min(), v.max()
        norm[c] = (v - mi) / (ma - mi) if ma > mi else np.zeros_like(v)

    N = len(cats)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    colors = ['#2dba4e', '#0969da']
    for i, p in enumerate(portals):
        vals = [norm[c][i] for c in cats] + [norm[cats[0]][i]]
        ax.plot(angles, vals, 'o-', linewidth=2.5, label=p, color=colors[i])
        ax.fill(angles, vals, alpha=0.15, color=colors[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontsize=11)
    ax.set_ylim(0, 1)
    ax.set_title('Trending vs Topics: Content Feature Comparison',
                 fontsize=14, fontweight='bold', pad=30)
    ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1), fontsize=11)
    plt.tight_layout()
    plt.savefig('output/analysis/portal_radar.png', dpi=300, bbox_inches='tight')
    print("[SAVE] output/analysis/portal_radar.png")
    plt.close()


def domain_language_matrix(df):
    """领域 × 语言 交叉分析"""
    results = []
    for _, row in df.iterrows():
        kw = row.get('keywords', {})
        if not isinstance(kw, dict):
            continue
        for domain, d_kws in TECH_DOMAINS.items():
            d_hit = any(kw.get(k, 0) > 0 for k in d_kws)
            if d_hit:
                for lang in LANGUAGES:
                    if kw.get(lang, 0) > 0:
                        results.append({
                            'domain': domain,
                            'language': lang,
                            'portal': row.get('portal', 'Unknown')
                        })
    return pd.DataFrame(results)


def plot_domain_heatmap(dl_df):
    """绘制领域×语言热力图"""
    if dl_df.empty:
        return
    pivot = dl_df.groupby(['domain', 'language']).size().unstack(fill_value=0)
    # 确保所有语言列存在
    for lang in LANGUAGES:
        if lang not in pivot.columns:
            pivot[lang] = 0
    pivot = pivot[LANGUAGES]  # 固定列顺序

    plt.figure(figsize=(12, 7))
    sns.heatmap(pivot, annot=True, fmt='d', cmap='YlOrRd',
                linewidths=0.5, cbar_kws={'label': 'Co-occurrence Count'})
    plt.title('Technology Domain × Programming Language Cross Analysis',
              fontsize=14, fontweight='bold')
    plt.ylabel('Technology Domain', fontsize=12)
    plt.xlabel('Programming Language', fontsize=12)
    plt.tight_layout()
    plt.savefig('output/analysis/domain_language_heatmap.png', dpi=300, bbox_inches='tight')
    print("[SAVE] output/analysis/domain_language_heatmap.png")
    plt.close()


def plot_box_comparison(df):
    """箱线图对比"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    for ax, metric, title in zip(axes.flat,
                                  ['word_count', 'link_count', 'image_count', 'script_count'],
                                  ['Description Length', 'Link Count', 'Image Count', 'Script Count']):
        data = [df[df['portal'] == p][metric].dropna().values for p in df['portal'].unique()]
        labels = df['portal'].unique()
        bp = ax.boxplot(data, labels=labels, patch_artist=True)
        for patch, color in zip(bp['boxes'], ['#2dba4e', '#0969da']):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_ylabel('Count')
    plt.suptitle('Trending vs Topics: Distribution Comparison', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('output/analysis/portal_boxplot.png', dpi=300, bbox_inches='tight')
    print("[SAVE] output/analysis/portal_boxplot.png")
    plt.close()


if __name__ == '__main__':
    df = pd.read_pickle('output/analysis/cleaned_data.pkl')

    # 结构对比
    metrics = structure_comparison(df)
    print("\n[Structure Metrics]")
    print(metrics)
    metrics.to_csv('output/analysis/structure_metrics.csv')

    # 雷达图 + 箱线图
    plot_radar(df)
    plot_box_comparison(df)

    # 领域×语言交叉
    dl_df = domain_language_matrix(df)
    if not dl_df.empty:
        plot_domain_heatmap(dl_df)
        dl_df.to_csv('output/analysis/domain_language_matrix.csv', index=False)

    print("[DONE] Portal comparison complete")
```

### 6.6 脚本5：共现网络分析

```python
"""
step5_cooccurrence_network.py
技术关键词共现网络构建与社区发现
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
from itertools import combinations
import numpy as np

# 核心关键词（用于网络节点）
NETWORK_KEYWORDS = [
    "Python", "Go", "Rust", "TypeScript", "Java", "C++",
    "Kubernetes", "Docker", "microservice", "serverless",
    "Hadoop", "Spark", "Flink", "Kafka",
    "machine-learning", "deep-learning", "LLM", "GPT", "NLP",
    "blockchain", "Web3", "smart-contract", "DeFi",
    "PostgreSQL", "MongoDB", "Redis"
]


def build_network(df, min_co=2):
    """构建共现网络"""
    co = Counter()
    for _, row in df.iterrows():
        kw = row.get('keywords', {})
        if not isinstance(kw, dict):
            continue
        present = [k for k in NETWORK_KEYWORDS if kw.get(k, 0) > 0]
        for a, b in combinations(sorted(present), 2):
            co[(a, b)] += 1

    G = nx.Graph()
    for (a, b), w in co.items():
        if w >= min_co:
            G.add_edge(a, b, weight=w)
    G.remove_nodes_from(list(nx.isolates(G)))
    return G, co


def analyze_network(G):
    """网络拓扑分析"""
    if len(G.nodes) == 0:
        return {}
    m = {
        'nodes': G.number_of_nodes(),
        'edges': G.number_of_edges(),
        'density': nx.density(G),
        'avg_clustering': nx.average_clustering(G),
        'components': nx.number_connected_components(G),
    }
    deg = nx.degree_centrality(G)
    m['top_degree'] = sorted(deg.items(), key=lambda x: x[1], reverse=True)[:15]
    bet = nx.betweenness_centrality(G)
    m['top_betweenness'] = sorted(bet.items(), key=lambda x: x[1], reverse=True)[:10]
    return m


def plot_network(G, path):
    """绘制网络图"""
    if len(G.nodes) == 0:
        return
    plt.figure(figsize=(18, 14))
    pos = nx.spring_layout(G, k=3.5, iterations=100, seed=42)

    degrees = dict(G.degree())
    node_sizes = [degrees[n] * 350 + 250 for n in G.nodes()]
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    ew_max = max(edge_weights) if edge_weights else 1
    edge_widths = [w / ew_max * 4 + 0.5 for w in edge_weights]

    # 社区着色（连通分量）
    comps = list(nx.connected_components(G))
    cmap = plt.cm.Set3(np.linspace(0, 1, max(len(comps), 1)))
    nc_map = {}
    for i, comp in enumerate(comps):
        for n in comp:
            nc_map[n] = cmap[i % len(cmap)]
    node_colors = [nc_map[n] for n in G.nodes()]

    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors,
                           alpha=0.88, edgecolors='white', linewidths=1.5)
    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.35, edge_color='gray')
    nx.draw_networkx_labels(G, pos, font_size=11, font_weight='bold')

    plt.title('GitHub Open Source Technology Co-occurrence Network',
              fontsize=16, fontweight='bold', pad=20)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches='tight')
    print(f"[SAVE] {path}")
    plt.close()


def write_report(metrics, path):
    """网络分析报告"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write("=" * 55 + "\n")
        f.write("   Technology Co-occurrence Network Report\n")
        f.write("=" * 55 + "\n\n")
        f.write(f"[Basic Metrics]\n")
        f.write(f"  Nodes:       {metrics.get('nodes', 0)}\n")
        f.write(f"  Edges:       {metrics.get('edges', 0)}\n")
        f.write(f"  Density:     {metrics.get('density', 0):.4f}\n")
        f.write(f"  Clustering:  {metrics.get('avg_clustering', 0):.4f}\n")
        f.write(f"  Components:  {metrics.get('components', 0)}\n\n")
        f.write("[Degree Centrality Top 15]\n")
        for i, (n, c) in enumerate(metrics.get('top_degree', []), 1):
            f.write(f"  {i:2d}. {n:<25s} {c:.4f}\n")
        f.write("\n[Betweenness Centrality Top 10]\n")
        for i, (n, c) in enumerate(metrics.get('top_betweenness', []), 1):
            f.write(f"  {i:2d}. {n:<25s} {c:.4f}\n")
    print(f"[SAVE] {path}")


if __name__ == '__main__':
    df = pd.read_pickle('output/analysis/cleaned_data.pkl')

    G, co = build_network(df, min_co=2)
    print(f"[INFO] Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    metrics = analyze_network(G)

    # 保存共现边数据
    pd.DataFrame([{'kw1': a, 'kw2': b, 'weight': w} for (a, b), w in co.most_common(100)]) \
      .to_csv('output/analysis/cooccurrence_edges.csv', index=False)

    plot_network(G, 'output/analysis/cooccurrence_network.png')
    write_report(metrics, 'output/analysis/network_report.txt')

    # 分别绘制Trending和Topics子网络
    for portal in ['Trending', 'Topics']:
        sub = df[df['portal'] == portal]
        if len(sub) > 5:
            G_sub, _ = build_network(sub, min_co=1)
            if G_sub.number_of_nodes() > 0:
                plot_network(G_sub, f'output/analysis/network_{portal.lower()}.png')

    print("[DONE] Network analysis complete")
```

### 6.7 一键运行脚本

```bash
#!/bin/bash
# run_analysis.sh

echo "============================================"
echo "  GitHub Open Source Ecosystem Analysis"
echo "============================================"

python step1_data_integration.py
python step2_language_analysis.py
python step3_topic_wordcloud.py
python step4_portal_comparison.py
python step5_cooccurrence_network.py

echo ""
echo "============================================"
echo "  All analysis complete!"
echo "  Results: output/analysis/"
echo "============================================"
```

---

## 7. 预期成果清单

| 成果项 | 文件名 | 说明 |
|--------|--------|------|
| 清洗数据集 | `cleaned_data.pkl/.csv` | 12个数据源整合后的结构化数据 |
| 语言热度排行 | `language_heat.png` | 全局TOP15 + Trending vs Topics对比 |
| 语言分析报告 | `language_report.txt` | 详细数据与百分比 |
| Trending词云 | `wordcloud_trending.png` | 短期热度技术主题 |
| Topics词云 | `wordcloud_topics.png` | 长期沉淀技术主题 |
| TF-IDF对比 | `tfidf_comparison.png` | 双入口TOP20关键词对比 |
| 多维雷达图 | `portal_radar.png` | Trending vs Topics 5维特征对比 |
| 箱线图对比 | `portal_boxplot.png` | 4项指标分布差异 |
| 领域×语言热力图 | `domain_language_heatmap.png` | 技术领域与编程语言交叉矩阵 |
| 共现全网络 | `cooccurrence_network.png` | 全平台技术关键词关联网络 |
| Trending子网络 | `network_trending.png` | Trending入口关键词网络 |
| Topics子网络 | `network_topics.png` | Topics入口关键词网络 |
| 网络分析报告 | `network_report.txt` | 拓扑指标与中心性排名 |

---

## 8. 项目交付结构

```
project/
├── crawler.py                      # 提供的爬虫入口
├── html_parser.py                  # 提供的HTML解析器
├── webcrawler.py                   # 提供的核心爬虫
├── run_all_crawlers.sh             # 12个采集任务批量脚本
├── analysis/
│   ├── step1_data_integration.py      # 数据整合与清洗
│   ├── step2_language_analysis.py     # 编程语言热度
│   ├── step3_topic_wordcloud.py       # TF-IDF与词云
│   ├── step4_portal_comparison.py     # Trending vs Topics + 交叉分析
│   ├── step5_cooccurrence_network.py  # 共现网络
│   └── run_analysis.sh                # 一键分析脚本
├── output/
│   ├── gh_trending_all/            # 12个数据源原始采集结果
│   ├── gh_trending_python/
│   ├── ...（共12个目录）
│   └── analysis/                   # 分析成果目录
│       ├── cleaned_data.csv
│       ├── language_heat.png
│       ├── wordcloud_trending.png
│       ├── wordcloud_topics.png
│       ├── tfidf_comparison.png
│       ├── portal_radar.png
│       ├── domain_language_heatmap.png
│       ├── cooccurrence_network.png
│       └── ...
└── report.md                       # 最终分析报告
```

---

## 9. 实施计划

| 阶段 | 时间 | 任务 | 产出 |
|------|------|------|------|
| **第1周** | Day 1-2 | 环境搭建、参数调试 | 确认12个页面可正常爬取 |
| | Day 3-5 | 执行12个采集任务 | ~330条仓库原始数据 |
| **第2周** | Day 1 | 数据清洗与整合 | 统一数据集 |
| | Day 2-3 | 语言热度 + TF-IDF词云 | 排行图、词云、TF-IDF对比 |
| | Day 4-5 | Trending vs Topics对比 + 交叉分析 | 雷达图、热力图、箱线图 |
| **第3周** | Day 1-2 | 共现网络分析 | 网络图、中心性报告 |
| | Day 3-4 | 撰写报告 | 完整Markdown报告 |
| | Day 5 | 答辩准备 | PPT + 演示 |

---

## 10. 核心创新点

1. **Trending vs Topics 双视角分析**：不是简单统计热门项目，而是对比"短期热度入口"与"长期深度入口"的内容生态差异，回答"现在什么最火"和"什么技术最扎实"两个问题
2. **技术领域 × 编程语言交叉矩阵**：揭示各技术领域（云原生/大数据/AI/区块链）的编程语言偏好，回答"什么领域用什么语言"
3. **技术关键词共现网络**：用NetworkX构建技术栈之间的关联网络，发现隐藏的集群结构（如Docker-Kubernetes-DevOps云原生集群）
4. **全英文NLP分析链路**：从分词、停用词过滤、词干提取到TF-IDF的完整英文文本挖掘流程
5. **课程深度契合**：分析对象直接涵盖Docker、Kubernetes、Hadoop、Spark、TensorFlow等云计算与大数据核心开源技术

---
