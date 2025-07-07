"""
智能检索代理（Retriever Agent）
一个自主决策的检索代理，根据查询自动选择最优检索策略
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from agno.agent import Agent, RunEvent
from agno.models.openai import OpenAIChat
from agno.tools import tool, Toolkit
from agno.run.response import RunResponseEvent
from agno.utils.log import logger

# 导入向量数据库和知识库相关模块
try:
    from agno.vectordb.zilliz import Zilliz
    from agno.knowledge.pdf import PDFKnowledgeBase
    ZILLIZ_AVAILABLE = True
except ImportError:
    ZILLIZ_AVAILABLE = False
    logger.warning("Zilliz 模块未安装，向量搜索功能将不可用")

# 导入 OpenSearch（可选）
try:
    from opensearchpy import OpenSearch
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False
    logger.warning("OpenSearch 模块未安装，关键词搜索功能将受限")

# 导入网络搜索工具
from agno.tools.duckduckgo import DuckDuckGoTools


class SearchStrategy(Enum):
    """搜索策略枚举"""
    VECTOR = "vector"  # 向量搜索
    KEYWORD = "keyword"  # 关键词搜索
    HYBRID = "hybrid"  # 混合搜索
    WEB = "web"  # 网络搜索
    CRM = "crm"  # CRM 搜索（预留）


@dataclass
class SearchResult:
    """搜索结果数据类"""
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    chunk_id: Optional[str] = None


@dataclass
class RetrievalStrategy:
    """检索策略数据类"""
    strategy_type: SearchStrategy
    data_source: str
    query: str  # 可能被重写的查询
    original_query: str
    filters: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    fallback_strategy: Optional['RetrievalStrategy'] = None


class RetrieverTools(Toolkit):
    """Retriever 工具集"""

    def __init__(self, zilliz_config: Optional[Dict] = None,
                 opensearch_config: Optional[Dict] = None,
                 *args, **kwargs):
        super().__init__(name="retriever_tools", *args, **kwargs)

        # 初始化 Zilliz 配置
        self.zilliz_config = zilliz_config or {}
        self.zilliz_client = None
        if ZILLIZ_AVAILABLE and zilliz_config:
            try:
                self.zilliz_client = Zilliz(**zilliz_config)
            except Exception as e:
                logger.error(f"初始化 Zilliz 失败: {e}")

        # 初始化 OpenSearch 配置
        self.opensearch_config = opensearch_config or {}
        self.opensearch_client = None
        if OPENSEARCH_AVAILABLE and opensearch_config:
            try:
                self.opensearch_client = OpenSearch(**opensearch_config)
            except Exception as e:
                logger.error(f"初始化 OpenSearch 失败: {e}")

        # 初始化网络搜索工具
        self.web_search_tools = DuckDuckGoTools()

        # 注册工具
        self.register(self.think_retrieval_strategy)
        self.register(self.zilliz_search)
        self.register(self.opensearch_search)
        self.register(self.web_search)

    def think_retrieval_strategy(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能分析查询并决定检索策略

        Args:
            query: 用户查询
            context: 上下文信息，包含 filters、caller_agent 等

        Returns:
            检索策略字典
        """
        # 分析查询意图
        query_lower = query.lower()

        # 判断是否需要重写查询
        rewritten_query = self._rewrite_query_if_needed(query, context)

        # 选择搜索策略
        strategy = self._select_search_strategy(rewritten_query, context)

        # 构建检索参数
        parameters = self._build_search_parameters(rewritten_query, context, strategy)

        return {
            "strategy_type": strategy.value,
            "data_source": self._get_data_source_for_strategy(strategy),
            "query": rewritten_query,
            "original_query": query,
            "filters": context.get("filters", {}),
            "parameters": parameters,
            "fallback_strategy": self._get_fallback_strategy(strategy)
        }

    def _rewrite_query_if_needed(self, query: str, context: Dict) -> str:
        """根据需要重写查询"""
        # 这里可以集成 LLM 来智能重写查询
        # 简化实现：如果查询过于简短或模糊，进行扩展
        if len(query.split()) < 3:
            # 可以调用 LLM 来扩展查询
            return f"{query} 相关信息和详细内容"
        return query

    def _select_search_strategy(self, query: str, context: Dict) -> SearchStrategy:
        """选择最合适的搜索策略"""
        doc_type = context.get("doc_type", "auto")
        caller_agent = context.get("caller_agent", "")

        # 根据查询特征选择策略
        if any(keyword in query.lower() for keyword in ["最新", "新闻", "实时", "current", "latest"]):
            return SearchStrategy.WEB

        # 如果明确指定了文档类型
        if doc_type == "pdf" or "文档" in query:
            return SearchStrategy.VECTOR

        # 如果是精确查询（包含引号或特定格式）
        if '"' in query or '`' in query:
            return SearchStrategy.KEYWORD

        # 默认使用混合搜索
        return SearchStrategy.HYBRID

    def _get_data_source_for_strategy(self, strategy: SearchStrategy) -> str:
        """获取策略对应的数据源"""
        mapping = {
            SearchStrategy.VECTOR: "zilliz_cloud",
            SearchStrategy.KEYWORD: "opensearch",
            SearchStrategy.HYBRID: "zilliz_cloud",  # Zilliz 也支持混合搜索
            SearchStrategy.WEB: "duckduckgo",
            SearchStrategy.CRM: "crm_api"
        }
        return mapping.get(strategy, "unknown")

    def _build_search_parameters(self, query: str, context: Dict,
                                strategy: SearchStrategy) -> Dict[str, Any]:
        """构建搜索参数"""
        params = {
            "limit": context.get("limit", 10),
            "score_threshold": context.get("score_threshold", 0.5)
        }

        # 根据策略添加特定参数
        if strategy == SearchStrategy.VECTOR:
            params["search_fields"] = ["content", "summary"]
        elif strategy == SearchStrategy.KEYWORD:
            params["search_fields"] = ["title", "content", "keywords"]
        elif strategy == SearchStrategy.HYBRID:
            params["vector_weight"] = 0.7
            params["keyword_weight"] = 0.3

        return params

    def _get_fallback_strategy(self, primary_strategy: SearchStrategy) -> Optional[Dict]:
        """获取降级策略"""
        fallback_mapping = {
            SearchStrategy.VECTOR: SearchStrategy.KEYWORD,
            SearchStrategy.KEYWORD: SearchStrategy.WEB,
            SearchStrategy.HYBRID: SearchStrategy.KEYWORD,
        }

        fallback = fallback_mapping.get(primary_strategy)
        if fallback:
            return {
                "strategy_type": fallback.value,
                "data_source": self._get_data_source_for_strategy(fallback)
            }
        return None

    async def zilliz_search(self, query: str, filters: Dict[str, Any],
                          parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        使用 Zilliz Cloud 进行向量搜索

        Args:
            query: 搜索查询
            filters: 过滤条件
            parameters: 搜索参数

        Returns:
            搜索结果列表
        """
        if not self.zilliz_client:
            logger.warning("Zilliz 客户端未初始化")
            return []

        try:
            # 构建搜索参数
            search_params = {
                "query": query,
                "limit": parameters.get("limit", 10),
                "filter": self._build_zilliz_filter(filters)
            }

            # 执行搜索
            results = await self.zilliz_client.search(**search_params)

            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {}),
                    "source": "zilliz_cloud",
                    "chunk_id": result.get("id")
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Zilliz 搜索失败: {e}")
            return []

    def _build_zilliz_filter(self, filters: Dict) -> str:
        """构建 Zilliz 过滤条件"""
        conditions = []

        if "ws_id" in filters:
            conditions.append(f"ws_id == '{filters['ws_id']}'")

        if "time_range" in filters:
            if filters["time_range"] == "recent":
                # 最近7天
                conditions.append("create_time >= now() - interval '7 days'")

        return " AND ".join(conditions) if conditions else ""

    async def opensearch_search(self, query: str, filters: Dict[str, Any],
                              parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        使用 OpenSearch 进行关键词搜索

        Args:
            query: 搜索查询
            filters: 过滤条件
            parameters: 搜索参数

        Returns:
            搜索结果列表
        """
        if not self.opensearch_client:
            logger.warning("OpenSearch 客户端未初始化")
            return []

        try:
            # 构建查询
            body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": parameters.get("search_fields", ["*"])
                                }
                            }
                        ],
                        "filter": self._build_opensearch_filter(filters)
                    }
                },
                "size": parameters.get("limit", 10)
            }

            # 执行搜索
            response = self.opensearch_client.search(body=body)

            # 格式化结果
            formatted_results = []
            for hit in response["hits"]["hits"]:
                formatted_results.append({
                    "content": hit["_source"].get("content", ""),
                    "score": hit["_score"],
                    "metadata": hit["_source"],
                    "source": "opensearch",
                    "chunk_id": hit["_id"]
                })

            return formatted_results

        except Exception as e:
            logger.error(f"OpenSearch 搜索失败: {e}")
            return []

    def _build_opensearch_filter(self, filters: Dict) -> List[Dict]:
        """构建 OpenSearch 过滤条件"""
        filter_clauses = []

        if "ws_id" in filters:
            filter_clauses.append({"term": {"ws_id": filters["ws_id"]}})

        if "doc_type" in filters:
            filter_clauses.append({"term": {"doc_type": filters["doc_type"]}})

        return filter_clauses

    async def web_search(self, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        使用网络搜索

        Args:
            query: 搜索查询
            parameters: 搜索参数

        Returns:
            搜索结果列表
        """
        try:
            # 使用 DuckDuckGo 进行搜索
            results = self.web_search_tools.duckduckgo_search(
                query=query,
                max_results=parameters.get("limit", 5)
            )

            # 格式化结果
            formatted_results = []

            # DuckDuckGo 可能返回字符串列表或字典列表
            if isinstance(results, list):
                for idx, result in enumerate(results):
                    if isinstance(result, dict):
                        formatted_results.append({
                            "content": result.get("snippet", result.get("body", "")),
                            "score": 1.0 - (idx * 0.1),  # 简单的评分递减
                            "metadata": {
                                "title": result.get("title", ""),
                                "link": result.get("link", result.get("href", ""))
                            },
                            "source": "web",
                            "chunk_id": None
                        })
                    elif isinstance(result, str):
                        # 如果是字符串，直接作为内容
                        formatted_results.append({
                            "content": result,
                            "score": 1.0 - (idx * 0.1),
                            "metadata": {},
                            "source": "web",
                            "chunk_id": None
                        })

            return formatted_results

        except Exception as e:
            logger.error(f"网络搜索失败: {e}")
            return []


class RetrieverAgent:
    """
    智能检索代理
    对外只暴露 search 方法，内部自主决策检索策略
    """

    def __init__(self,
                 name: str = "Retriever Agent",
                 model: Optional[Any] = None,
                 zilliz_config: Optional[Dict] = None,
                 opensearch_config: Optional[Dict] = None,
                 enable_events: bool = True):
        """
        初始化 Retriever Agent

        Args:
            name: Agent 名称
            model: LLM 模型
            zilliz_config: Zilliz 配置
            opensearch_config: OpenSearch 配置
            enable_events: 是否启用事件系统
        """
        self.name = name
        self.enable_events = enable_events

        # 初始化工具集
        self.tools = RetrieverTools(
            zilliz_config=zilliz_config,
            opensearch_config=opensearch_config
        )

        # 初始化内部 Agent
        self.agent = Agent(
            agent_id=f"{name.lower().replace(' ', '_')}_agent",
            name=name,
            model=model or OpenAIChat(id="gpt-4o"),
            tools=[self.tools],
            description="智能检索代理，自主决策最优检索策略",
            instructions="""
            你是一个智能检索代理，负责：
            1. 分析用户查询意图
            2. 自主选择最合适的检索策略
            3. 执行检索并返回结果
            4. 如果主策略失败，自动使用降级策略

            始终确保返回高质量、相关的检索结果。
            """
        )

        # 事件监听器
        self.event_handlers = []

    async def search(self,
                    query: str,
                    context: Optional[Dict[str, Any]] = None,
                    session_id: Optional[str] = None,
                    user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        执行智能搜索

        Args:
            query: 搜索查询
            context: 上下文信息，包含 filters、doc_type 等
            session_id: 会话 ID
            user_id: 用户 ID

        Returns:
            搜索结果字典，包含结果列表和元信息
        """
        # 初始化上下文
        if context is None:
            context = {}

        # 记录开始时间
        start_time = datetime.now()

        try:
            # 发出检索开始事件
            if self.enable_events:
                await self._emit_event("RetrievalStarted", {
                    "query": query,
                    "context": context,
                    "timestamp": start_time.isoformat()
                })

            # 1. 智能分析查询，决定检索策略
            strategy_result = self.tools.think_retrieval_strategy(query, context)
            # 将 strategy_type 字符串转换为枚举
            strategy_result['strategy_type'] = SearchStrategy(strategy_result['strategy_type'])
            strategy = RetrievalStrategy(**strategy_result)

            # 发出策略完成事件
            if self.enable_events:
                await self._emit_event("RetrievalStrategyCompleted", {
                    "strategy": strategy.strategy_type.value,
                    "data_source": strategy.data_source,
                    "rewritten_query": strategy.query
                })

            # 2. 执行主检索策略
            results = await self._execute_search_strategy(strategy)

            # 3. 如果结果为空且有降级策略，执行降级
            if not results and strategy.fallback_strategy:
                logger.info(f"主策略无结果，执行降级策略: {strategy.fallback_strategy}")

                if self.enable_events:
                    await self._emit_event("FallbackStrategyActivated", {
                        "fallback": strategy.fallback_strategy
                    })

                fallback_strategy = RetrievalStrategy(
                    strategy_type=SearchStrategy(strategy.fallback_strategy["strategy_type"]),
                    data_source=strategy.fallback_strategy["data_source"],
                    query=strategy.query,
                    original_query=strategy.original_query,
                    filters=strategy.filters,
                    parameters=strategy.parameters
                )
                results = await self._execute_search_strategy(fallback_strategy)

            # 4. 后处理结果
            processed_results = self._post_process_results(results, strategy)

            # 计算执行时间
            duration = (datetime.now() - start_time).total_seconds()

            # 5. 构建响应
            response = {
                "success": True,
                "results": processed_results,
                "metadata": {
                    "total_results": len(processed_results),
                    "query": query,
                    "rewritten_query": strategy.query,
                    "strategy_used": strategy.strategy_type.value,
                    "data_source": strategy.data_source,
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat()
                },
                "error": None
            }

            # 发出检索完成事件
            if self.enable_events:
                await self._emit_event("RetrievalCompleted", {
                    "results_count": len(processed_results),
                    "duration": duration,
                    "strategy": strategy.strategy_type.value
                })

            return response

        except Exception as e:
            logger.error(f"检索过程出错: {e}")

            # 发出错误事件
            if self.enable_events:
                await self._emit_event("RetrievalError", {
                    "error": str(e),
                    "query": query
                })

            # 返回错误响应
            return {
                "success": False,
                "results": [],
                "metadata": {
                    "query": query,
                    "error_message": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                "error": {
                    "code": "RETRIEVAL_FAILED",
                    "message": str(e)
                }
            }

    async def _execute_search_strategy(self, strategy: RetrievalStrategy) -> List[Dict[str, Any]]:
        """执行具体的搜索策略"""
        results = []

        try:
            if strategy.data_source == "zilliz_cloud":
                results = await self.tools.zilliz_search(
                    query=strategy.query,
                    filters=strategy.filters,
                    parameters=strategy.parameters
                )
            elif strategy.data_source == "opensearch":
                results = await self.tools.opensearch_search(
                    query=strategy.query,
                    filters=strategy.filters,
                    parameters=strategy.parameters
                )
            elif strategy.data_source == "duckduckgo":
                results = await self.tools.web_search(
                    query=strategy.query,
                    parameters=strategy.parameters
                )

            # 发出工具调用完成事件
            if self.enable_events:
                await self._emit_event("ToolCallCompleted", {
                    "tool": strategy.data_source,
                    "results_count": len(results)
                })

        except Exception as e:
            logger.error(f"执行搜索策略失败: {e}")

        return results

    def _post_process_results(self, results: List[Dict[str, Any]],
                            strategy: RetrievalStrategy) -> List[Dict[str, Any]]:
        """后处理搜索结果"""
        # 1. 去重
        seen = set()
        unique_results = []
        for result in results:
            # 使用内容的前100个字符作为去重键
            key = result.get("content", "")[:100]
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        # 2. 按分数排序
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)

        # 3. 应用分数阈值过滤
        threshold = strategy.parameters.get("score_threshold", 0.5)
        filtered_results = [
            r for r in unique_results
            if r.get("score", 0) >= threshold
        ]

        # 4. 限制返回数量
        limit = strategy.parameters.get("limit", 10)
        return filtered_results[:limit]

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """发出自定义事件"""
        event = {
            "event": event_type,
            "agent_name": self.name,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # 通知所有事件处理器
        for handler in self.event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {e}")

    def add_event_handler(self, handler) -> None:
        """添加事件处理器"""
        self.event_handlers.append(handler)

    def remove_event_handler(self, handler) -> None:
        """移除事件处理器"""
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)


# 使用示例
async def demo():
    """演示 Retriever Agent 的使用"""

    # 创建 Retriever Agent
    retriever = RetrieverAgent(
        name="智能检索代理",
        # 配置 Zilliz（如果有）
        zilliz_config={
            # "uri": "your_zilliz_uri",
            # "token": "your_token",
            # "collection_name": "your_collection"
        },
        # 配置 OpenSearch（如果有）
        opensearch_config={
            # "hosts": ["localhost:9200"],
            # "http_auth": ("user", "pass")
        }
    )

    # 添加事件监听器
    async def event_listener(event):
        print(f"[事件] {event['event']}: {event['data']}")

    retriever.add_event_handler(event_listener)

    # 测试不同类型的查询
    test_queries = [
        {
            "query": "AWS GPU 实例类型信息",
            "context": {
                "doc_type": "auto",
                "filters": {"ws_id": "workspace_001"}
            }
        },
        {
            "query": "最新的人工智能发展动态",
            "context": {
                "doc_type": "news",
                "filters": {"time_range": "recent"}
            }
        },
        {
            "query": "如何配置 Kubernetes",
            "context": {
                "doc_type": "documentation",
                "caller_agent": "tech_support_agent"
            }
        }
    ]

    # 执行查询
    for test in test_queries:
        print(f"\n{'='*80}")
        print(f"查询: {test['query']}")
        print(f"上下文: {test['context']}")
        print(f"{'='*80}")

        result = await retriever.search(
            query=test['query'],
            context=test['context'],
            session_id=f"demo_session_{datetime.now().timestamp()}",
            user_id="demo_user"
        )

        if result["success"]:
            print(f"\n✅ 搜索成功!")
            print(f"策略: {result['metadata']['strategy_used']}")
            print(f"数据源: {result['metadata']['data_source']}")
            print(f"结果数: {result['metadata']['total_results']}")
            print(f"耗时: {result['metadata']['duration_seconds']:.2f}秒")

            # 显示前3个结果
            for i, res in enumerate(result["results"][:3], 1):
                print(f"\n结果 {i}:")
                print(f"  内容: {res['content'][:100]}...")
                print(f"  分数: {res['score']:.3f}")
                print(f"  来源: {res['source']}")
        else:
            print(f"\n❌ 搜索失败: {result['error']['message']}")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo())
