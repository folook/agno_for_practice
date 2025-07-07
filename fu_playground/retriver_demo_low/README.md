# RetrieverAgent - 智能检索代理

一个基于 agno 框架的智能检索代理，能够根据查询自主决策最优检索策略，支持多数据源检索。

## 核心特性

### 1. 自主决策
- **智能查询分析**：自动分析用户查询意图
- **查询重写**：对简短或模糊的查询进行智能扩展
- **策略选择**：根据查询特征自动选择最合适的检索策略

### 2. 黑盒封装
- **简单接口**：对外只暴露一个 `search` 方法
- **透明处理**：调用方无需了解底层检索细节
- **统一响应**：所有数据源返回统一格式的结果

### 3. 多数据源支持
- **Zilliz Cloud**：向量搜索，适合语义检索
- **OpenSearch**：关键词搜索，适合精确匹配
- **Web Search**：网络搜索，获取最新信息
- **CRM/MCP**：预留接口，可扩展其他数据源

### 4. 智能降级
- **自动降级**：主策略失败时自动启用备选方案
- **策略链**：向量搜索 → 关键词搜索 → 网络搜索
- **错误处理**：优雅处理各种异常情况

### 5. 事件系统
- **实时监控**：支持事件监听，跟踪检索过程
- **性能指标**：记录耗时、结果数等关键指标
- **调试支持**：详细的事件日志便于问题排查

## 快速开始

### 基本使用

```python
import asyncio
from retriver_demo import RetrieverAgent

async def main():
    # 创建 RetrieverAgent
    retriever = RetrieverAgent(name="智能检索助手")
    
    # 执行搜索
    result = await retriever.search(
        query="Python 异步编程",
        context={
            "doc_type": "tutorial",
            "filters": {"language": "zh-CN"}
        }
    )
    
    # 处理结果
    if result["success"]:
        print(f"找到 {result['metadata']['total_results']} 个结果")
        for res in result["results"]:
            print(f"- {res['content'][:100]}...")

asyncio.run(main())
```

### 作为工具使用

```python
from agno.agent import Agent
from agno.tools import tool

@tool
async def search_tool(query: str) -> str:
    retriever = RetrieverAgent()
    result = await retriever.search(query)
    return format_results(result)

# 在 Agent 中使用
agent = Agent(
    name="研究助手",
    tools=[search_tool],
    instructions="使用搜索工具查找信息并回答问题"
)
```

## API 参考

### RetrieverAgent

#### 初始化参数

```python
RetrieverAgent(
    name: str = "Retriever Agent",
    model: Optional[Any] = None,
    zilliz_config: Optional[Dict] = None,
    opensearch_config: Optional[Dict] = None,
    enable_events: bool = True
)
```

- `name`: Agent 名称
- `model`: LLM 模型（默认使用 GPT-4）
- `zilliz_config`: Zilliz Cloud 配置
- `opensearch_config`: OpenSearch 配置
- `enable_events`: 是否启用事件系统

#### search 方法

```python
async def search(
    query: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]
```

**参数**：
- `query`: 搜索查询字符串
- `context`: 上下文信息字典
  - `doc_type`: 文档类型 (auto/pdf/news/documentation)
  - `filters`: 过滤条件
  - `limit`: 返回结果数量限制
  - `score_threshold`: 分数阈值

**返回值**：
```python
{
    "success": bool,
    "results": [
        {
            "content": str,
            "score": float,
            "metadata": dict,
            "source": str,
            "chunk_id": Optional[str]
        }
    ],
    "metadata": {
        "total_results": int,
        "query": str,
        "rewritten_query": str,
        "strategy_used": str,
        "data_source": str,
        "duration_seconds": float,
        "timestamp": str
    },
    "error": Optional[dict]
}
```

## 检索策略

### 策略类型

1. **VECTOR（向量搜索）**
   - 适用于语义理解需求高的查询
   - 使用 Zilliz Cloud 进行向量相似度搜索
   - 支持多语言、同义词理解

2. **KEYWORD（关键词搜索）**
   - 适用于精确匹配需求
   - 使用 OpenSearch 进行全文检索
   - 支持引号、通配符等高级语法

3. **HYBRID（混合搜索）**
   - 结合向量和关键词搜索优势
   - 默认权重：向量 70%，关键词 30%
   - 适用于大多数通用查询

4. **WEB（网络搜索）**
   - 获取最新的互联网信息
   - 使用 DuckDuckGo 搜索引擎
   - 适用于时效性要求高的查询

### 策略选择逻辑

```
查询分析
  ├─ 包含"最新"、"新闻"等关键词 → WEB
  ├─ 指定 doc_type="pdf" 或包含"文档" → VECTOR
  ├─ 包含引号或特殊格式 → KEYWORD
  └─ 其他情况 → HYBRID
```

## 事件系统

### 支持的事件

- `RetrievalStarted`: 检索开始
- `RetrievalStrategyCompleted`: 策略决策完成
- `ToolCallCompleted`: 工具调用完成
- `FallbackStrategyActivated`: 降级策略激活
- `RetrievalCompleted`: 检索完成
- `RetrievalError`: 检索错误

### 事件监听示例

```python
async def event_handler(event):
    print(f"[{event['event']}] {event['data']}")

retriever = RetrieverAgent()
retriever.add_event_handler(event_handler)
```

## 配置示例

### Zilliz Cloud 配置

```python
zilliz_config = {
    "uri": "https://your-instance.zillizcloud.com",
    "token": "your-api-token",
    "collection_name": "your_collection"
}
```

### OpenSearch 配置

```python
opensearch_config = {
    "hosts": ["https://localhost:9200"],
    "http_auth": ("username", "password"),
    "use_ssl": True,
    "verify_certs": True
}
```

## 高级用法

### 1. 自定义事件处理

```python
class MetricsCollector:
    def __init__(self):
        self.metrics = []
    
    async def collect(self, event):
        if event['event'] == 'RetrievalCompleted':
            self.metrics.append({
                'duration': event['data']['duration'],
                'results': event['data']['results_count']
            })

collector = MetricsCollector()
retriever.add_event_handler(collector.collect)
```

### 2. 批量检索

```python
async def batch_search(queries, retriever):
    tasks = [
        retriever.search(query) 
        for query in queries
    ]
    return await asyncio.gather(*tasks)
```

### 3. 结果缓存

```python
from functools import lru_cache

class CachedRetriever(RetrieverAgent):
    @lru_cache(maxsize=100)
    async def search_cached(self, query_hash):
        return await self.search(query_hash)
```

## 常见问题

### Q: 如何选择合适的检索策略？
A: RetrieverAgent 会自动根据查询特征选择策略。您也可以通过 `doc_type` 参数提供提示。

### Q: 如何处理大量并发请求？
A: 建议使用连接池和批量处理，参考"高级用法"中的批量检索示例。

### Q: 如何自定义查询重写逻辑？
A: 可以继承 `RetrieverTools` 类并重写 `_rewrite_query_if_needed` 方法。

### Q: 支持哪些过滤条件？
A: 常用过滤条件包括 `ws_id`（工作空间）、`time_range`（时间范围）、`doc_type`（文档类型）等。

## 性能优化建议

1. **复用实例**：避免每次查询都创建新的 RetrieverAgent 实例
2. **合理设置限制**：通过 `limit` 参数控制返回结果数量
3. **使用分数阈值**：设置 `score_threshold` 过滤低相关度结果
4. **启用缓存**：对于重复查询，考虑实现缓存机制
5. **异步并发**：充分利用异步特性处理多个查询

## 扩展开发

### 添加新的数据源

```python
class CustomRetrieverTools(RetrieverTools):
    async def custom_search(self, query, filters, parameters):
        # 实现自定义搜索逻辑
        results = await your_custom_api.search(query)
        return format_results(results)
```

### 自定义后处理

```python
class CustomRetrieverAgent(RetrieverAgent):
    def _post_process_results(self, results, strategy):
        # 调用父类方法
        results = super()._post_process_results(results, strategy)
        
        # 添加自定义处理
        return apply_custom_ranking(results)
```

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议！

## 许可证

本项目基于 MIT 许可证开源。 