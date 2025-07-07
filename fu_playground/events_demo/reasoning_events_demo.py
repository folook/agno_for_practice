"""
推理事件演示
展示 agno 框架中的推理事件监听用法
"""

import asyncio
from typing import Dict, List

from agno.agent import Agent, RunEvent
from agno.models.openai.chat import OpenAIChat
from agno.run.response import RunResponseEvent
from agno.tools.yfinance import YFinanceTools
from agno.tools.duckduckgo import DuckDuckGoTools


class ReasoningEventsDemo:
    """推理事件演示类"""
    
    def __init__(self):
        # 创建带推理功能的代理
        self.reasoning_agent = Agent(
            agent_id="reasoning-demo-agent",
            name="推理演示代理",
            model=OpenAIChat(id="gpt-4o"),
            reasoning=True,  # 启用推理功能
            tools=[YFinanceTools(), DuckDuckGoTools()],
            description="用于演示推理事件系统的代理"
        )
        
        # 推理步骤记录
        self.reasoning_steps: List[str] = []
        self.reasoning_content: List[str] = []
        
        # 事件计数器
        self.event_counters = {
            "reasoning_started": 0,
            "reasoning_step": 0,
            "reasoning_completed": 0,
            "run_started": 0,
            "run_completed": 0,
        }
    
    async def reasoning_event_listener(self, prompt: str) -> None:
        """推理事件监听器"""
        print("=" * 60)
        print("🧠 开始推理事件监听演示")
        print("=" * 60)
        print(f"任务: {prompt}")
        print("=" * 60)
        
        try:
            # 使用流式响应并监听中间步骤
            async for event in await self.reasoning_agent.arun(
                prompt,
                stream=True,
                stream_intermediate_steps=True,
            ):
                await self._handle_reasoning_event(event)
                
            print("\n" + "=" * 60)
            print("📊 推理事件统计:")
            for event_type, count in self.event_counters.items():
                print(f"  {event_type}: {count}")
            print("=" * 60)
            
            # 显示收集到的推理步骤
            if self.reasoning_steps:
                print("\n🎯 推理步骤总结:")
                for i, step in enumerate(self.reasoning_steps, 1):
                    print(f"  步骤 {i}: {step}")
                    
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    async def _handle_reasoning_event(self, event: RunResponseEvent) -> None:
        """处理推理事件"""
        
        # 推理开始事件
        if event.event == RunEvent.reasoning_started:
            self.event_counters["reasoning_started"] += 1
            print(f"\n🧠 推理开始")
            print(f"   代理ID: {event.agent_id}")
            print(f"   运行ID: {event.run_id}")
            print(f"   开始时间: {event.created_at}")
        
        # 推理步骤事件
        elif event.event == RunEvent.reasoning_step:
            self.event_counters["reasoning_step"] += 1
            reasoning_content = getattr(event, 'reasoning_content', '')
            if reasoning_content:
                print(f"\n🔍 推理步骤 {self.event_counters['reasoning_step']}:")
                print(f"   内容: {reasoning_content[:200]}...")
                self.reasoning_steps.append(reasoning_content)
        
        # 推理完成事件
        elif event.event == RunEvent.reasoning_completed:
            self.event_counters["reasoning_completed"] += 1
            print(f"\n✅ 推理完成")
            print(f"   推理步骤总数: {len(self.reasoning_steps)}")
            
            # 如果有内容，显示推理结果
            if hasattr(event, 'content') and event.content:
                print(f"   推理结果: {str(event.content)[:100]}...")
        
        # 运行开始事件
        elif event.event == RunEvent.run_started:
            self.event_counters["run_started"] += 1
            print(f"\n🎯 运行开始")
            print(f"   模型: {getattr(event, 'model', 'N/A')}")
        
        # 运行完成事件
        elif event.event == RunEvent.run_completed:
            self.event_counters["run_completed"] += 1
            print(f"\n🎉 运行完成")
        
        # 工具调用事件
        elif event.event == RunEvent.tool_call_started:
            print(f"\n🔧 工具调用: {event.tool.tool_name}")
            print(f"   参数: {event.tool.tool_args}")
        
        elif event.event == RunEvent.tool_call_completed:
            print(f"\n✅ 工具调用完成: {event.tool.tool_name}")
        
        # 响应内容事件
        elif event.event == RunEvent.run_response_content:
            if event.content:
                print(event.content, end="", flush=True)
    
    async def run_complex_reasoning_demo(self) -> None:
        """运行复杂推理演示"""
        complex_task = """
        分析以下投资策略的可行性:
        1. 比较苹果公司 (AAPL) 和微软公司 (MSFT) 的当前估值
        2. 评估科技股在当前市场环境下的风险
        3. 基于搜索到的最新市场新闻，提供投资建议
        4. 考虑宏观经济因素对这两只股票的影响
        
        请提供详细的分析和推理过程。
        """
        
        await self.reasoning_event_listener(complex_task)
    
    async def run_simple_reasoning_demo(self) -> None:
        """运行简单推理演示"""
        simple_task = """
        解释为什么人工智能在金融分析中越来越重要？
        请提供具体的例子和推理过程。
        """
        
        await self.reasoning_event_listener(simple_task)


async def main():
    """主函数"""
    demo = ReasoningEventsDemo()
    
    print("选择演示类型:")
    print("1. 简单推理演示")
    print("2. 复杂推理演示")
    
    # 为了演示目的，运行简单推理演示
    await demo.run_simple_reasoning_demo()
    
    print("\n" + "=" * 60)
    print("演示完成！")


if __name__ == "__main__":
    asyncio.run(main()) 