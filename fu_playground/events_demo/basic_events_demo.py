"""
基本事件监听演示
展示 agno 框架中的基本事件监听用法
"""

import asyncio
from typing import AsyncGenerator

from agno.agent import Agent, RunEvent
from agno.models.openai.chat import OpenAIChat
from agno.tools.yfinance import YFinanceTools
from agno.run.response import RunResponseEvent


class EventsDemo:
    """事件演示类"""
    
    def __init__(self):
        self.agent = Agent(
            agent_id="events-demo-agent",
            name="事件演示代理",
            model=OpenAIChat(id="gpt-4o"),
            tools=[YFinanceTools()],
            description="用于演示事件系统的代理"
        )
        
        # 事件计数器
        self.event_counters = {
            "run_started": 0,
            "run_completed": 0,
            "tool_call_started": 0,
            "tool_call_completed": 0,
            "run_response_content": 0,
        }
    
    async def basic_event_listener(self, prompt: str) -> None:
        """基本事件监听器"""
        print("=" * 50)
        print("🚀 开始基本事件监听演示")
        print("=" * 50)
        
        try:
            # 使用流式响应并监听中间步骤
            async for event in await self.agent.arun(
                prompt,
                stream=True,
                stream_intermediate_steps=True,
            ):
                await self._handle_basic_event(event)
                
            print("\n" + "=" * 50)
            print("📊 事件统计:")
            for event_type, count in self.event_counters.items():
                print(f"  {event_type}: {count}")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    async def _handle_basic_event(self, event: RunResponseEvent) -> None:
        """处理基本事件"""
        
        # 运行开始事件
        if event.event == RunEvent.run_started:
            self.event_counters["run_started"] += 1
            print(f"\n🎯 运行开始")
            print(f"   代理ID: {event.agent_id}")
            print(f"   代理名称: {event.agent_name}")
            print(f"   运行ID: {event.run_id}")
            print(f"   模型: {getattr(event, 'model', 'N/A')}")
        
        # 运行完成事件
        elif event.event == RunEvent.run_completed:
            self.event_counters["run_completed"] += 1
            print(f"\n✅ 运行完成")
            print(f"   内容类型: {getattr(event, 'content_type', 'N/A')}")
            print(f"   运行状态: {getattr(event, 'status', 'N/A')}")
        
        # 工具调用开始事件
        elif event.event == RunEvent.tool_call_started:
            self.event_counters["tool_call_started"] += 1
            print(f"\n🔧 工具调用开始")
            print(f"   工具名称: {event.tool.tool_name}")
            print(f"   工具参数: {event.tool.tool_args}")
        
        # 工具调用完成事件
        elif event.event == RunEvent.tool_call_completed:
            self.event_counters["tool_call_completed"] += 1
            print(f"\n🎉 工具调用完成")
            print(f"   工具名称: {event.tool.tool_name}")
            print(f"   调用结果: {str(event.tool.result)[:100]}...")
        
        # 响应内容事件
        elif event.event == RunEvent.run_response_content:
            self.event_counters["run_response_content"] += 1
            if event.content:
                print(event.content, end="", flush=True)
    
    async def run_demo(self) -> None:
        """运行演示"""
        await self.basic_event_listener(
            "获取苹果公司(AAPL)的当前股价和基本信息"
        )


async def main():
    """主函数"""
    demo = EventsDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main()) 