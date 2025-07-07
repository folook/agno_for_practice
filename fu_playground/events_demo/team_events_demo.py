"""
团队事件演示
展示 agno 框架中的团队事件监听用法
"""

import asyncio
from typing import Dict, List

from agno.agent import Agent
from agno.models.openai.chat import OpenAIChat
from agno.run.team import TeamRunEvent, TeamRunResponseEvent
from agno.team import Team
from agno.tools.yfinance import YFinanceTools
from agno.tools.duckduckgo import DuckDuckGoTools


class TeamEventsDemo:
    """团队事件演示类"""
    
    def __init__(self):
        # 创建金融分析师代理
        self.financial_analyst = Agent(
            agent_id="financial-analyst",
            name="金融分析师",
            model=OpenAIChat(id="gpt-4o"),
            tools=[YFinanceTools()],
            description="专门负责金融数据分析和股票信息获取"
        )
        
        # 创建市场研究员代理
        self.market_researcher = Agent(
            agent_id="market-researcher",
            name="市场研究员",
            model=OpenAIChat(id="gpt-4o"),
            tools=[DuckDuckGoTools()],
            description="专门负责市场新闻和趋势研究"
        )
        
        # 创建投资顾问代理
        self.investment_advisor = Agent(
            agent_id="investment-advisor",
            name="投资顾问",
            model=OpenAIChat(id="gpt-4o"),
            description="基于分析结果提供投资建议"
        )
        
        # 创建团队
        self.investment_team = Team(
            agents=[
                self.financial_analyst,
                self.market_researcher,
                self.investment_advisor
            ],
            name="投资分析团队",
            description="专业的投资分析团队，提供全面的投资建议"
        )
        
        # 事件计数器
        self.event_counters = {
            "team_run_started": 0,
            "team_run_completed": 0,
            "team_tool_call_started": 0,
            "team_tool_call_completed": 0,
            "team_run_response_content": 0,
            "team_reasoning_started": 0,
            "team_reasoning_step": 0,
            "team_reasoning_completed": 0,
        }
        
        # 团队活动日志
        self.team_activity_log: List[Dict] = []
    
    async def team_event_listener(self, prompt: str) -> None:
        """团队事件监听器"""
        print("=" * 70)
        print("👥 开始团队事件监听演示")
        print("=" * 70)
        print(f"任务: {prompt}")
        print("=" * 70)
        
        try:
            # 使用流式响应并监听中间步骤
            async for event in await self.investment_team.arun(
                prompt,
                stream=True,
                stream_intermediate_steps=True,
            ):
                await self._handle_team_event(event)
                
            print("\n" + "=" * 70)
            print("📊 团队事件统计:")
            for event_type, count in self.event_counters.items():
                print(f"  {event_type}: {count}")
            print("=" * 70)
            
            # 显示团队活动日志
            if self.team_activity_log:
                print("\n📋 团队活动日志:")
                for i, activity in enumerate(self.team_activity_log, 1):
                    print(f"  {i}. {activity['event']} - {activity['description']}")
                    
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    async def _handle_team_event(self, event: TeamRunResponseEvent) -> None:
        """处理团队事件"""
        
        # 团队运行开始事件
        if event.event == TeamRunEvent.run_started:
            self.event_counters["team_run_started"] += 1
            print(f"\n🎯 团队运行开始")
            print(f"   团队会话ID: {event.team_session_id}")
            print(f"   运行ID: {event.run_id}")
            print(f"   模型: {getattr(event, 'model', 'N/A')}")
            
            self.team_activity_log.append({
                "event": "团队运行开始",
                "description": f"团队开始处理任务 (会话ID: {event.team_session_id})"
            })
        
        # 团队运行完成事件
        elif event.event == TeamRunEvent.run_completed:
            self.event_counters["team_run_completed"] += 1
            print(f"\n✅ 团队运行完成")
            print(f"   运行状态: {getattr(event, 'status', 'N/A')}")
            
            self.team_activity_log.append({
                "event": "团队运行完成",
                "description": "团队成功完成任务"
            })
        
        # 团队工具调用开始事件
        elif event.event == TeamRunEvent.tool_call_started:
            self.event_counters["team_tool_call_started"] += 1
            print(f"\n🔧 团队工具调用开始")
            print(f"   代理ID: {event.agent_id}")
            print(f"   代理名称: {event.agent_name}")
            print(f"   工具名称: {event.tool.tool_name}")
            print(f"   工具参数: {event.tool.tool_args}")
            
            self.team_activity_log.append({
                "event": "工具调用",
                "description": f"{event.agent_name} 开始使用 {event.tool.tool_name}"
            })
        
        # 团队工具调用完成事件
        elif event.event == TeamRunEvent.tool_call_completed:
            self.event_counters["team_tool_call_completed"] += 1
            print(f"\n🎉 团队工具调用完成")
            print(f"   代理名称: {event.agent_name}")
            print(f"   工具名称: {event.tool.tool_name}")
            print(f"   调用结果: {str(event.tool.result)[:100]}...")
            
            self.team_activity_log.append({
                "event": "工具调用完成",
                "description": f"{event.agent_name} 完成了 {event.tool.tool_name} 的调用"
            })
        
        # 团队推理开始事件
        elif event.event == TeamRunEvent.reasoning_started:
            self.event_counters["team_reasoning_started"] += 1
            print(f"\n🧠 团队推理开始")
            print(f"   代理名称: {event.agent_name}")
            
            self.team_activity_log.append({
                "event": "推理开始",
                "description": f"{event.agent_name} 开始推理过程"
            })
        
        # 团队推理步骤事件
        elif event.event == TeamRunEvent.reasoning_step:
            self.event_counters["team_reasoning_step"] += 1
            reasoning_content = getattr(event, 'reasoning_content', '')
            if reasoning_content:
                print(f"\n🔍 团队推理步骤")
                print(f"   代理名称: {event.agent_name}")
                print(f"   推理内容: {reasoning_content[:150]}...")
        
        # 团队推理完成事件
        elif event.event == TeamRunEvent.reasoning_completed:
            self.event_counters["team_reasoning_completed"] += 1
            print(f"\n✅ 团队推理完成")
            print(f"   代理名称: {event.agent_name}")
            
            self.team_activity_log.append({
                "event": "推理完成",
                "description": f"{event.agent_name} 完成推理过程"
            })
        
        # 团队响应内容事件
        elif event.event == TeamRunEvent.run_response_content:
            self.event_counters["team_run_response_content"] += 1
            if event.content:
                # 显示哪个代理在发言
                if hasattr(event, 'agent_name') and event.agent_name:
                    print(f"\n💬 {event.agent_name}: ", end="")
                print(event.content, end="", flush=True)
        
        # 团队运行错误事件
        elif event.event == TeamRunEvent.run_error:
            print(f"\n❌ 团队运行错误")
            print(f"   错误内容: {event.content}")
            
            self.team_activity_log.append({
                "event": "运行错误",
                "description": f"团队运行出现错误: {event.content}"
            })
    
    async def run_investment_analysis_demo(self) -> None:
        """运行投资分析演示"""
        investment_task = """
        我想投资科技股，请团队帮我分析：
        1. 获取苹果公司(AAPL)和微软公司(MSFT)的最新股价和财务数据
        2. 搜索这两家公司的最新新闻和市场动态
        3. 基于数据分析和市场研究，提供投资建议
        
        请各位专家分工合作，提供全面的分析报告。
        """
        
        await self.team_event_listener(investment_task)
    
    async def run_market_research_demo(self) -> None:
        """运行市场研究演示"""
        market_task = """
        请团队帮我研究当前人工智能行业的投资机会：
        1. 分析主要AI公司的股价表现
        2. 搜索AI行业的最新发展趋势
        3. 评估AI投资的风险和机会
        
        请提供详细的市场分析报告。
        """
        
        await self.team_event_listener(market_task)


async def main():
    """主函数"""
    demo = TeamEventsDemo()
    
    print("选择演示类型:")
    print("1. 投资分析演示")
    print("2. 市场研究演示")
    
    # 为了演示目的，运行投资分析演示
    await demo.run_investment_analysis_demo()
    
    print("\n" + "=" * 70)
    print("团队演示完成！")


if __name__ == "__main__":
    asyncio.run(main()) 