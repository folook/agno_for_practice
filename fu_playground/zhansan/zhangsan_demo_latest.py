#!/usr/bin/env python3
"""
高级版 Agentic RAG Demo - 使用 Workflow 编排多个专门的 Agent
实现清晰的架构和优美的日志输出
"""

from typing import Optional, Dict, List
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.workflow import Workflow
from agno.utils.log import logger
from agno.utils.pprint import pprint_run_response
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime


# Mock数据存储
mock_db = {
    "张三": {
        "爱好": "张三的爱好和李四相同"
    },
    "李四": {
        "爱好": "李四喜欢和王五一样的东西"
    },
    "王五": {
        "爱好": "王五喜欢踢足球"
    }
}


class RAGWorkflow(Workflow):
    """高级 Agentic RAG 工作流 - 通过多个专门的 Agent 协作完成复杂查询"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.console = Console()
        self.retrieval_history: List[Dict] = []
        self.analysis_history: List[Dict] = []
        self.iteration_count = 0

        # 初始化专门的 Agents
        self._init_agents()

    def _init_agents(self):
        """初始化所有专门的 Agent"""

        # 1. Retriever Agent - 专门负责信息检索
        self.retriever = Agent(
            name="🔍 Retriever",
            model=OpenAIChat(id="gpt-4"),
            instructions="""
            你是一个信息检索专家。你的任务是：
            1. 根据查询精确检索相关信息
            2. 保持检索的准确性和相关性
            3. 只返回检索到的原始信息，不进行解释或推理

            重要：直接返回检索结果，不要添加任何额外说明。
            """,
            markdown=True,
            show_tool_calls=True
        )

        # 2. Analyzer Agent - 专门负责信息分析和规划
        self.analyzer = Agent(
            name="🧠 Analyzer",
            model=OpenAIChat(id="gpt-4"),
            instructions="""
            你是一个信息分析和规划专家。你的任务是：
            1. 分析所有检索历史，判断是否足够回答用户问题
            2. 识别信息中的引用关系（如"和XX相同"、"和XX一样"、"喜欢XX"等）
            3. 追踪完整的推理链，判断是否需要进一步查询
            4. 避免重复查询已经查询过的内容
            5. 基于分析结果直接决定下一步行动

            重要：仔细分析所有检索结果，建立完整的推理链。
            例如：如果A和B相同，B和C一样，那么需要查询C的具体内容才能知道A的具体内容。

            请按以下JSON格式返回分析结果：
            {
                "sufficient": true/false,
                "reasoning": "分析原因，包括推理链分析",
                "missing_info": "缺少什么信息（如果不充足）",
                "next_query": "下一步应该查询什么（如果需要）",
                "decision": "ANSWER 或 RETRIEVE"
            }
            """,
            markdown=False
        )

        # 3. Final Answer Agent - 负责生成最终答案
        self.answerer = Agent(
            name="✅ Final Answer",
            model=OpenAIChat(id="gpt-4"),
            instructions="""
            你是一个答案生成专家。基于所有收集到的信息，生成清晰、准确的最终答案。

            要求：
            1. 基于实际获得的信息进行推理
            2. 展示完整的推理链条
            3. 给出明确的结论
            """,
            markdown=True
        )

    def _retrieve(self, query: str) -> str:
        """执行信息检索"""
        self.console.print(Panel(
            f"[bold cyan]执行检索:[/bold cyan] {query}",
            title=f"🔍 第 {len(self.retrieval_history) + 1} 轮检索",
            border_style="cyan"
        ))

        # 智能匹配查询内容
        result = "未找到相关信息"

        for person, info in mock_db.items():
            if person in query:
                if "爱好" in query:
                    result = info["爱好"]
                    break

        # 记录检索历史
        self.retrieval_history.append({
            "iteration": len(self.retrieval_history) + 1,
            "query": query,
            "result": result,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

        self.console.print(f"[green]检索结果:[/green] {result}\n")
        return result

    # 包装 analyzer
    def _analyze_info(self, question: str, all_retrieval_history: List[Dict]) -> Dict:
        """分析信息完整性并规划下一步行动"""
        # 构建所有历史检索结果的显示
        history_display = "\n".join([
            f"第{item['iteration']}轮: {item['query']} -> {item['result']}"
            for item in all_retrieval_history
        ])

        self.console.print(Panel(
            f"[bold yellow]分析信息完整性并规划下一步[/bold yellow]\n"
            f"原始问题: {question}\n"
            f"所有检索历史:\n{history_display}",
            title="🧠 信息分析与规划",
            border_style="yellow"
        ))

        analysis_prompt = f"""
        分析以下信息是否足够回答用户问题，并规划下一步行动：

        用户问题：{question}

        所有检索历史：
        {history_display}

        请仔细分析所有检索结果，识别其中的引用关系（如"和XX相同"、"和XX一样"），
        判断是否需要进一步查询来完成推理链。

        请返回JSON格式的结果。
        """

        response = self.analyzer.run(analysis_prompt, stream=False)

        try:
            import json
            analysis_result = json.loads(response.content)
        except:
            # 如果解析失败，创建默认结果
            analysis_result = {
                "sufficient": False,
                "reasoning": "需要进一步分析",
                "missing_info": "未知",
                "next_query": None,
                "decision": "RETRIEVE"
            }

        # 记录分析历史
        self.analysis_history.append({
            "iteration": len(self.analysis_history) + 1, # Changed to len(self.analysis_history) + 1
            "analysis": analysis_result,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

        # 美化输出分析结果
        status = "[green]充足[/green]" if analysis_result.get("sufficient") else "[red]不足[/red]"
        self.console.print(f"[bold]分析结果:[/bold] {status}")
        self.console.print(f"[dim]原因:[/dim] {analysis_result.get('reasoning', 'N/A')}")

        if not analysis_result.get("sufficient"):
            self.console.print(f"[dim]缺失信息:[/dim] {analysis_result.get('missing_info', 'N/A')}")
            self.console.print(f"[dim]建议查询:[/dim] {analysis_result.get('next_query', 'N/A')}")

        # 显示决策结果
        decision = analysis_result.get("decision", "RETRIEVE")
        if decision == "ANSWER":
            self.console.print("[green]决策: 信息充足，准备生成最终答案[/green]\n")
        else:
            self.console.print(f"[yellow]决策: 需要进一步检索 - {analysis_result.get('next_query', 'N/A')}[/yellow]\n")

        return analysis_result

    def _generate_final_answer(self, question: str, all_info: List[Dict]) -> str:
        """生成最终答案"""
        self.console.print(Panel(
            "[bold green]生成最终答案[/bold green]",
            title="✅ 答案生成",
            border_style="green"
        ))

        # 构建完整的信息上下文
        info_context = "\n".join([
            f"第{item['iteration']}轮检索 - 查询：{item['query']} -> 结果：{item['result']}"
            for item in self.retrieval_history
        ])

        answer_prompt = f"""
        基于以下检索到的信息，回答用户问题：

        用户问题：{question}

        检索历史：
        {info_context}

        请基于以上信息进行推理并给出最终答案。
        """

        response = self.answerer.run(answer_prompt, stream=False)
        return response.content

    def _display_summary(self):
        """显示执行摘要"""
        # 创建检索历史表格
        table = Table(title="📊 检索历史", border_style="blue")
        table.add_column("轮次", style="cyan", width=6)
        table.add_column("时间", style="dim", width=10)
        table.add_column("查询", style="yellow")
        table.add_column("结果", style="green")

        for item in self.retrieval_history:
            table.add_row(
                str(item["iteration"]),
                item["timestamp"],
                item["query"],
                item["result"]
            )

        self.console.print(table)
        self.console.print("")

    def run(self, message: str = None, **kwargs) -> RunResponse:
        """执行工作流"""
        # 从 kwargs 中获取参数，如果没有则使用 message
        if message is None:
            message = kwargs.get("message", "默认查询")

        logger.info(f"Starting Agentic RAG workflow for query: '{message}'")

        # 显示开始信息
        self.console.print(Panel(
            f"[bold blue]🚀 启动 Agentic RAG 工作流[/bold blue]\n"
            f"查询: {message}",
            title="工作流开始",
            border_style="blue",
            expand=False
        ))
        self.console.print("")

        # 初始化
        self.retrieval_history = []
        self.analysis_history = []
        current_info = ""

        # 主循环 - 最多5轮迭代
        for iteration in range(1, 6):
            self.console.print(f"[bold cyan]--- 第 {iteration} 轮迭代 ---[/bold cyan]\n")

            # Step 1: 检索信息
            if iteration == 1:
                query = message
            else:
                # 从上一轮分析中获取查询建议
                last_analysis = self.analysis_history[-1]["analysis"]
                query = last_analysis.get("next_query", message)

            retrieved_info = self._retrieve(query)
            current_info = retrieved_info

            # Step 2: 分析信息
            analysis = self._analyze_info(message, self.retrieval_history)

            # Step 3: 根据决策执行
            if analysis.get("decision") == "ANSWER":
                # 生成最终答案
                final_answer = self._generate_final_answer(message, self.retrieval_history)

                # 显示执行摘要
                self._display_summary()

                # 返回最终结果
                return RunResponse(
                    run_id=self.run_id,
                    content=final_answer
                )
            elif analysis.get("decision") == "RETRIEVE":
                # 继续下一轮检索
                continue

        # 如果达到最大迭代次数
        self.console.print("[red]达到最大迭代次数，基于当前信息生成答案[/red]\n")
        final_answer = self._generate_final_answer(message, self.retrieval_history)

        # 显示执行摘要
        self._display_summary()

        return RunResponse(
            run_id=self.run_id,
            content=final_answer
        )


def main():
    """运行高级版演示"""
    rprint("\n[bold blue]🎯 高级版 Agentic RAG Demo - Workflow 架构[/bold blue]")
    rprint("[dim]使用 Workflow 编排多个专门的 Agent，实现清晰的架构和优美的日志输出[/dim]\n")

    # 创建工作流
    workflow = RAGWorkflow(debug_mode=True)

    # 测试问题
    question = "张三的爱好是什么？"

    # 运行工作流
    response = workflow.run(message=question)

    # 打印最终响应
    rprint("\n[bold green]🎉 工作流执行完成！[/bold green]")
    rprint(f"\n[bold cyan]最终答案:[/bold cyan]\n{response.content}")

    # 显示响应详情
    rprint(f"\n[dim]响应详情:[/dim]")
    rprint(f"[dim]- Run ID: {response.run_id}[/dim]")
    rprint(f"[dim]- Session ID: {response.session_id}[/dim]")
    rprint(f"[dim]- Workflow ID: {response.workflow_id}[/dim]")


if __name__ == "__main__":
    main()
