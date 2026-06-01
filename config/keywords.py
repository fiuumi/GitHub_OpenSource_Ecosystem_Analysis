"""
GitHub Crawler - Unified Keyword Dictionary (60 words, 6 dimensions)

This module defines the keyword taxonomy used for technology topic analysis.
All keywords are used to scan repository descriptions and count occurrences,
enabling downstream analysis of programming language heat, tech domain 
distribution, and keyword co-occurrence networks.

Source: GitHub Open Source Ecosystem Evolution Analysis Design Document
Section 4.1 - Unified Keyword Dictionary
"""

from typing import List, Dict

# === Dimension 1: Programming Languages (15 words) ===
LANGUAGE_KEYWORDS: List[str] = [
    "Python", "Go", "Rust", "TypeScript", "JavaScript", "Java",
    "C++", "C", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "Dart"
]

# === Dimension 2: Cloud Native & Containers (10 words) ===
CLOUD_NATIVE_KEYWORDS: List[str] = [
    "Kubernetes", "Docker", "container", "microservice", "serverless",
    "DevOps", "Istio", "Helm", "Terraform", "service-mesh"
]

# === Dimension 3: Big Data Stack (10 words) ===
BIGDATA_KEYWORDS: List[str] = [
    "Hadoop", "Spark", "Flink", "Kafka", "data-warehouse", "data-lake",
    "ETL", "streaming", "MapReduce", "Elasticsearch"
]

# === Dimension 4: Artificial Intelligence (10 words) ===
AI_KEYWORDS: List[str] = [
    "machine-learning", "deep-learning", "neural-network", "NLP",
    "computer-vision", "LLM", "GPT", "transformer", "OpenAI", "agent"
]

# === Dimension 5: Blockchain & Web3 (8 words) ===
BLOCKCHAIN_KEYWORDS: List[str] = [
    "blockchain", "Ethereum", "Web3", "smart-contract", "DeFi",
    "cryptocurrency", "Solidity", "NFT"
]

# === Dimension 6: Databases & Storage (7 words) ===
DATABASE_KEYWORDS: List[str] = [
    "database", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "NoSQL"
]

# === Combined Master List (60 words) ===
ALL_KEYWORDS: List[str] = (
    LANGUAGE_KEYWORDS +
    CLOUD_NATIVE_KEYWORDS +
    BIGDATA_KEYWORDS +
    AI_KEYWORDS +
    BLOCKCHAIN_KEYWORDS +
    DATABASE_KEYWORDS
)

# === Dimension Mapping for Categorized Analysis ===
KEYWORD_CATEGORIES: Dict[str, List[str]] = {
    "Language": LANGUAGE_KEYWORDS,
    "CloudNative": CLOUD_NATIVE_KEYWORDS,
    "BigData": BIGDATA_KEYWORDS,
    "AI": AI_KEYWORDS,
    "Blockchain": BLOCKCHAIN_KEYWORDS,
    "Database": DATABASE_KEYWORDS,
}

# === Network Analysis Keywords (subset for co-occurrence network) ===
NETWORK_KEYWORDS: List[str] = [
    "Python", "Go", "Rust", "TypeScript", "Java", "C++",
    "Kubernetes", "Docker", "microservice", "serverless",
    "Hadoop", "Spark", "Flink", "Kafka",
    "machine-learning", "deep-learning", "LLM", "GPT", "NLP",
    "blockchain", "Web3", "smart-contract", "DeFi",
    "PostgreSQL", "MongoDB", "Redis"
]

# === Technology Domain Classification ===
TECH_DOMAINS: Dict[str, List[str]] = {
    'CloudNative': CLOUD_NATIVE_KEYWORDS,
    'BigData': BIGDATA_KEYWORDS,
    'AI': AI_KEYWORDS,
    'Blockchain': BLOCKCHAIN_KEYWORDS,
    'Database': DATABASE_KEYWORDS,
}


def get_keyword_category(keyword: str) -> str:
    """Return the category name for a given keyword."""
    for category, keywords in KEYWORD_CATEGORIES.items():
        if keyword in keywords:
            return category
    return "Unknown"


def get_all_keywords_lowercase() -> List[str]:
    """Return all keywords in lowercase for case-insensitive matching."""
    return [kw.lower() for kw in ALL_KEYWORDS]


# === Validation ===
if __name__ == '__main__':
    print(f"Total keywords: {len(ALL_KEYWORDS)}")
    print(f"  Languages:    {len(LANGUAGE_KEYWORDS)}")
    print(f"  Cloud Native: {len(CLOUD_NATIVE_KEYWORDS)}")
    print(f"  Big Data:     {len(BIGDATA_KEYWORDS)}")
    print(f"  AI:           {len(AI_KEYWORDS)}")
    print(f"  Blockchain:   {len(BLOCKCHAIN_KEYWORDS)}")
    print(f"  Database:     {len(DATABASE_KEYWORDS)}")
    print(f"\nAll keywords: {ALL_KEYWORDS}")
