"""
RetrieverAgent - 智能检索代理

一个基于 agno 框架的智能检索代理，能够：
- 自主决策最优检索策略
- 支持多数据源（Zilliz、OpenSearch、Web）
- 智能查询重写和降级
- 完整的事件追踪系统
"""

from .retriver_demo import (
    RetrieverAgent,
    RetrieverTools,
    SearchStrategy,
    SearchResult,
    RetrievalStrategy
)

__version__ = "1.0.0"
__author__ = "Agno Team"

__all__ = [
    "RetrieverAgent",
    "RetrieverTools",
    "SearchStrategy",
    "SearchResult",
    "RetrievalStrategy"
]

# 快速使用示例
"""
使用示例:

```python
from fu_playground.retriver_demo_low import RetrieverAgent

# 创建检索代理
retriever = RetrieverAgent(name="智能助手")

# 执行搜索
result = await retriever.search(
    query="机器学习入门教程",
    context={"doc_type": "tutorial"}
)

# 处理结果
if result["success"]:
    for res in result["results"]:
        print(res["content"])
```
"""
