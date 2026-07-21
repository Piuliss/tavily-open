# tavily-open

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

中文文档 | [English](README.md)

> 🔍 开源的智能搜索与网页爬取工具 - Tavily 的开源替代方案

## 📖 项目简介

**tavily-open** 是一个功能强大的开源搜索和网页爬取工具，基于 SearXNG 构建。它通过两种主要方式提供灵活的网页内容提取功能：使用强大的 `Crawl4AI` 库进行深度爬取，以及可选地集成 `Jina Reader` 以实现快速、由 AI 驱动的内容获取。这种双引擎方法允许用户在全面爬取和高速内容提取之间进行选择。该工具完全开源、可定制，并支持分布式缓存。

### ✨ 核心特性

- 🔎 **智能搜索** - 通过 SearXNG 元搜索引擎获取高质量搜索结果
- 🕷️ **双爬取引擎** - 可选择使用 `Crawl4AI` 进行深度、支持 JavaScript 渲染的爬取，或使用 `Jina Reader` 进行快速、经 AI 优化的内容提取。
- 🚀 **分布式缓存** - 基于 Redis 的分布式缓存，减少重复爬取，提升性能
- 🎯 **RESTful API** - 简洁易用的 API 接口，支持 Swagger 文档
- ⚙️ **高度可定制** - 灵活配置搜索引擎、爬虫参数和缓存策略
- 🔄 **并发处理** - 多线程并行爬取，提高吞吐量
- 🐳 **Docker 支持** - 一键部署，包含所有依赖
- 🧪 **完整测试** - 全面的测试套件和代码质量工具

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          客户端应用                                   │
│                     (Web App / CLI / SDK)                            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ HTTP POST /search
                                 │ { query, limit, engines }
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        tavily-open API 服务                          │
│                      (FastAPI + Uvicorn)                             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
         ┌──────────────────┐      ┌──────────────────┐
         │  SearXNG 搜索    │      │   Redis 缓存      │
         │   元搜索引擎      │      │   分布式存储      │
         └────────┬─────────┘      └────────┬─────────┘
                  │                         │
                  │ 返回 URL 列表            │ 缓存命中检查
                  │ + 元数据                 │
                  ▼                         │
         ┌──────────────────┐               │
         │  URL 去重与       │◄─────────────┘
         │  缓存查询         │
         └────────┬─────────┘
                  │
                  │ 需要处理的 URL
                  │
      ┌───────────▼───────────┐
      │    提取引擎           │
      │ (通过 .env 选择)      │
      └───────────┬───────────┘
      ┌───────────┴───────────┐
      │                       │
┌─────▼───────┐           ┌─────▼─────┐
│ Jina Reader │           │ Crawl4AI  │
│ (Profile:   │           │  (默认)    │
│   reader)   │           │           │
└─────┬───────┘           └─────┬─────┘
      │                       │
      └───────────┬───────────┘
                  │
         ┌────────▼─────────┐
         │  内容过滤与处理   │
         │  (清洗 + 格式化)  │
         └────────┬─────────┘
                  │
                  │ 存储到缓存
                  ▼
         ┌──────────────────┐
         │  返回结果 + 统计  │
         │  (JSON Response)  │
         └──────────────────┘
```

### 🔄 工作流程详解

1. **接收请求** - 客户端发送搜索查询及参数（关键词、结果数量、搜索引擎配置）。
2. **缓存检查** - 系统首先检查 Redis 缓存中是否存在已爬取的内容（如启用缓存）。
3. **搜索阶段** - 将查询发送到 SearXNG，获取相关 URL 列表和元数据。
4. **URL 去重** - 对搜索结果进行去重，并查询缓存命中情况。
5. **内容提取** - 对于未缓存的 URL，系统会使用两种配置引擎中的一种。具体选择由 `.env` 文件中的 `READER_ENABLED` 设置和激活的 Docker Compose profile 决定。
    - **Crawl4AI (默认)**: 提供支持 JavaScript 渲染的深度爬取。这是默认方法。
    - **Jina Reader (可选)**: 当设置 `READER_ENABLED=true` 并激活 `reader` profile 时，系统会使用 Jina Reader 服务进行快速、由 AI 驱动的内容提取。
6. **内容处理** - 对提取的原始内容进行清洗、格式化和质量过滤。
7. **缓存存储** - 将成功获取的内容存储到 Redis，并设置过期时间。
8. **返回结果** - 返回处理后的内容及统计信息（缓存命中数、新爬取数、失败数）。

### 🧩 核心组件

| 组件 | 说明 | 技术栈 |
|------|------|--------|
| **API 服务器** | RESTful API 接口 | FastAPI + Uvicorn |
| **搜索引擎** | 隐私友好的元搜索 | SearXNG |
| **爬虫引擎** | 智能内容提取 | Crawl4AI + Playwright / Jina Reader |
| **缓存层** | 分布式缓存存储 | Redis |
| **并发处理** | 多线程爬取 | ThreadPoolExecutor |

## 🚀 快速开始

### 📋 前置要求

- Python 3.8+
- SearXNG 实例（本地或远程）
- Playwright 浏览器（安装脚本自动处理）
- Redis（可选，用于缓存 - Docker 部署自动包含）
- Jina Reader（可选，用于替代爬虫）

### 🐳 Docker 部署（推荐）

最简单的方式是使用 Docker Compose 一键部署所有服务：

```bash
# 1. 克隆仓库
git clone https://github.com/Owoui/SearXNG-Crawl4AI.git
cd SearXNG-Crawl4AI

# 2. 配置环境变量
cp .env.example .env
# 根据需要编辑 .env 文件

# 3. 启动基础服务（应用 + Redis）
docker-compose up -d

# 或启动包含 SearXNG 的完整服务
docker-compose --profile searxng up -d

# 4. 查看日志
docker-compose logs -f

# 5. 停止服务
docker-compose down
```

#### 📦 Docker Compose Profiles

本项目支持通过 profiles 选择性启动服务：

| Profile | 包含服务 | 使用场景 |
|---------|---------|---------|
| **默认（无 profile）** | App + Redis | 开发环境，使用外部 SearXNG |
| **searxng** | App + Redis + SearXNG | 完整本地环境 |
| **reader** | App + Redis + Reader + Reader 版 API | 在 `http://localhost:8001` 使用 Reader 提取 |
| **full** | 所有服务 | 生产环境或完整测试 |

**启动示例：**

```bash
# 仅启动基础服务（App + Redis）
docker-compose up -d

# 启动包含 SearXNG 的服务
docker-compose --profile searxng up -d

# 启动包含 Reader 服务的服务
docker-compose --profile reader up -d

# 启动所有服务
docker-compose --profile full up -d
```

**服务访问地址：**
- **主应用 API**: `http://localhost:8000`
- **Reader 版 API**: `http://localhost:8001` (使用 reader profile 时)
- **SearXNG 界面**: `http://localhost:8080` (使用 searxng profile 时)
- **Reader 服务**: `http://localhost:3001` (使用 reader profile 时)
- **Redis**: `localhost:6379`

详细的 Docker Profiles 使用说明请参考：[`DOCKER_PROFILES.md`](DOCKER_PROFILES.md)

### 💻 手动安装

#### 1. 克隆仓库

```bash
git clone https://github.com/Owoui/SearXNG-Crawl4AI.git
cd SearXNG-Crawl4AI
```

#### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
# 生产环境
pip install -e .

# 开发环境（包含测试和代码质量工具）
pip install -e ".[dev]"
```

#### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置 SearXNG、Redis 等参数
```

#### 5. 启动服务

```bash
# 使用命令行工具
opencrawl

# 或直接使用 Python
python -m opencrawl.main
```

服务默认运行在 `http://0.0.0.0:3000`

> **注意：** 包名保持为 `searcrawl` 以确保向后兼容性，但项目现已更名为 **tavily-open**。

## 📚 使用指南

### 🔌 API 端点

#### 搜索接口

```http
POST /search
Content-Type: application/json
```

**请求示例：**

```json
{
  "query": "人工智能最新进展",
  "limit": 10,
  "disabled_engines": "wikipedia__general,currency__general,wikidata__general",
  "enabled_engines": "baidu__general,bing__general"
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | ✅ | 搜索关键词 |
| `limit` | integer | ❌ | 返回结果数量（默认：10） |
| `disabled_engines` | string | ❌ | 禁用的搜索引擎（逗号分隔） |
| `enabled_engines` | string | ❌ | 启用的搜索引擎（逗号分隔） |

**响应示例：**

```json
{
  "results": [
    {
      "content": "人工智能（AI）是计算机科学的一个分支...",
      "reference": "https://example.com/ai-article"
    },
    {
      "content": "最新的 GPT-4 模型展示了强大的能力...",
      "reference": "https://example.com/gpt4-news"
    }
  ],
  "success_count": 8,
  "failed_urls": [
    "https://example.com/timeout-page"
  ],
  "cache_hits": 3,
  "newly_crawled": 5
}
```

**响应字段说明：**

| 字段 | 说明 |
|------|------|
| `results` | 爬取的内容数组，包含内容和来源 URL |
| `success_count` | 成功返回的结果总数（缓存 + 新爬取） |
| `failed_urls` | 爬取失败的 URL 列表 |
| `cache_hits` | 从缓存中获取的结果数（启用缓存时） |
| `newly_crawled` | 新爬取的结果数（启用缓存时） |

### 📖 API 文档

服务启动后，访问以下地址查看交互式 API 文档：

- **Swagger UI**: `http://localhost:3000/docs`
- **ReDoc**: `http://localhost:3000/redoc`

### 🔧 配置选项

通过 `.env` 文件配置系统参数：

```env
# ========== SearXNG 配置 ==========
SEARXNG_HOST=localhost
SEARXNG_PORT=8080
SEARXNG_BASE_PATH=/search

# ========== API 服务配置 ==========
API_HOST=0.0.0.0
API_PORT=3000

# ========== Reader 服务配置 ==========
READER_ENABLED=false
READER_URL=http://localhost:3001
READER_API_KEY=

# ========== 爬虫配置 ==========
DEFAULT_SEARCH_LIMIT=10          # 默认搜索结果数量
CONTENT_FILTER_THRESHOLD=0.6     # 内容过滤阈值
WORD_COUNT_THRESHOLD=10          # 最小字数阈值
CRAWLER_POOL_SIZE=4              # 爬虫线程池大小

# ========== 缓存配置 ==========
CACHE_ENABLED=true               # 启用/禁用缓存
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_HOURS=24               # 缓存过期时间（小时）

# ========== 搜索引擎配置 ==========
DISABLED_ENGINES=wikipedia__general,currency__general,wikidata__general
ENABLED_ENGINES=baidu__general,bing__general
```

### 💾 缓存配置详解

tavily-open 支持基于 Redis 的分布式缓存，可显著提升性能：

- **CACHE_ENABLED**: 启用/禁用缓存功能（true/false）
- **REDIS_URL**: Redis 连接 URL（默认：redis://localhost:6379/0）
- **CACHE_TTL_HOURS**: 缓存过期时间，单位小时（默认：24）

**缓存优势：**
- ✅ 减少重复爬取，节省带宽和时间
- ✅ 多实例共享缓存，提高整体效率
- ✅ 自动过期机制，保证数据新鲜度

详细的缓存实现文档请参考：[`CACHE_IMPLEMENTATION.md`](CACHE_IMPLEMENTATION.md)

## 🛠️ 开发指南

### 📁 项目结构

```
tavily-open/
├── src/
│   └── searcrawl/
│       ├── __init__.py           # 包初始化
│       ├── cache.py              # Redis 缓存管理器
│       ├── config.py             # 配置加载模块
│       ├── crawler.py            # 爬虫核心逻辑
│       ├── logger.py             # 日志模块
│       └── main.py               # API 服务入口
├── tests/
│   ├── __init__.py
│   ├── test_config.py            # 配置测试
│   ├── test_crawler.py           # 爬虫测试
│   └── test_api.py               # API 测试
├── .env.example                  # 环境变量示例
├── .gitignore                    # Git 忽略规则
├── .pre-commit-config.yaml       # Pre-commit 钩子配置
├── docker-compose.yml            # Docker Compose 配置
├── Dockerfile                    # Docker 镜像定义
├── pyproject.toml                # 项目元数据和依赖
├── requirements.txt              # 生产依赖
├── requirements-dev.txt          # 开发依赖
├── CACHE_IMPLEMENTATION.md       # 缓存系统文档
├── LICENSE                       # MIT 许可证
└── README.md                     # 项目文档
```

### 🔨 开发环境设置

```bash
# 1. 安装开发依赖
pip install -e ".[dev]"

# 2. 安装 pre-commit 钩子
pre-commit install

# 3. 运行测试
pytest

# 4. 运行测试并生成覆盖率报告
pytest --cov=searcrawl --cov-report=html

# 5. 代码格式化
black src/ tests/

# 6. 代码检查
ruff check src/ tests/

# 7. 类型检查
mypy src/
```

### 🧪 代码质量工具

| 工具 | 用途 | 命令 |
|------|------|------|
| **Black** | 代码格式化 | `black src/ tests/` |
| **Ruff** | 快速 Python 代码检查 | `ruff check src/ tests/` |
| **MyPy** | 静态类型检查 | `mypy src/` |
| **isort** | 导入排序 | `isort src/ tests/` |
| **pytest** | 测试框架 | `pytest` |
| **pre-commit** | Git 钩子 | `pre-commit run --all-files` |

### 🔧 扩展功能

根据需求修改以下文件来扩展功能：

- [`src/searcrawl/cache.py`](src/searcrawl/cache.py) - 扩展缓存策略或添加新的缓存后端
- [`src/searcrawl/crawler.py`](src/searcrawl/crawler.py) - 添加新的爬取策略或内容处理方法
- [`src/searcrawl/main.py`](src/searcrawl/main.py) - 添加新的 API 端点
- [`src/searcrawl/config.py`](src/searcrawl/config.py) - 添加新的配置参数

### 📦 构建分发包

```bash
# 构建源码包和 wheel 包
python -m build

# 构建产物将在 dist/ 目录中
```

## 🚢 部署说明

### SearXNG 配置要点

部署 SearXNG 时，需要特别注意以下配置：

在 SearXNG 的 `settings.yml` 配置文件中，添加或修改 `search` 部分的 `formats` 配置：

```yaml
search:
  formats:
    - html
    - json
```

此配置确保 SearXNG 返回 JSON 格式的搜索结果，这是 tavily-open 正常工作的必要条件。

### 生产环境建议

- ✅ 使用 Docker Compose 部署，便于管理
- ✅ 启用 Redis 缓存以提升性能
- ✅ 配置适当的 `CRAWLER_POOL_SIZE` 以平衡性能和资源
- ✅ 设置合理的 `CACHE_TTL_HOURS` 以平衡新鲜度和效率
- ✅ 使用反向代理（如 Nginx）处理 SSL 和负载均衡

## 🤝 贡献指南

欢迎贡献代码！如果您想为项目做出贡献，请遵循以下步骤：

1. **Fork 仓库**
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **创建 Pull Request**

### 贡献要求

- ✅ 更新相应的测试用例
- ✅ 遵循代码风格（由 pre-commit 钩子强制执行）
- ✅ 更新相关文档
- ✅ 确保所有测试通过

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)

## 🙏 致谢

本项目基于以下优秀的开源项目构建：

- **[SearCrawl](https://github.com/Owoui/SearXNG-Crawl4AI)** - 本项目的前身，感谢原始项目的贡献
- **[SearXNG](https://github.com/searxng/searxng)** - 隐私友好的元搜索引擎
- **[Crawl4AI](https://github.com/unclecode/crawl4ai)** - 为 AI 设计的网页爬取库
- **[Jina Reader](https://github.com/jina-ai/reader)** - 一个快速、智能的网页阅读服务
- **[FastAPI](https://fastapi.tiangolo.com/)** - 现代、快速的 Web 框架
- **[Redis](https://redis.io/)** - 高性能的内存数据存储

感谢所有为这些项目做出贡献的开发者！

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/Owoui/SearXNG-Crawl4AI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Owoui/SearXNG-Crawl4AI/discussions)

## 🗺️ 路线图

- [ ] 支持更多搜索引擎
- [ ] 添加 GraphQL API
- [ ] 实现结果排序和相关性评分
- [ ] 支持自定义内容提取规则
- [ ] 添加 Web UI 管理界面
- [ ] 支持更多缓存后端（Memcached、DynamoDB 等）
- [ ] 实现分布式爬取集群

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 ⭐️**

Made with ❤️ by the tavily-open community

</div>
