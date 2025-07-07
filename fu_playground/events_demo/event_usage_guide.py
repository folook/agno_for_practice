"""
agno 框架事件系统使用指南
全面展示 agno 框架中的事件系统使用方法和最佳实践
"""

import asyncio
from typing import Dict, List, Optional

from agno.agent import Agent, RunEvent
from agno.models.openai.chat import OpenAIChat
from agno.run.response import RunResponseEvent
from agno.run.team import TeamRunEvent, TeamRunResponseEvent
from agno.team import Team
from agno.tools.yfinance import YFinanceTools
from agno.tools.duckduckgo import DuckDuckGoTools


class EventGuide:
    """事件系统使用指南"""
    
    def __init__(self):
        self.examples = {}
        self.best_practices = []
        self.common_patterns = []
        
    def show_event_types(self) -> None:
        """显示所有可用的事件类型"""
        print("=" * 80)
        print("🎯 AGNO 框架事件类型总览")
        print("=" * 80)
        
        agent_events = {
            RunEvent.run_started: "代理运行开始",
            RunEvent.run_completed: "代理运行完成",
            RunEvent.run_error: "代理运行错误",
            RunEvent.run_cancelled: "代理运行取消",
            RunEvent.run_paused: "代理运行暂停",
            RunEvent.run_continued: "代理运行继续",
            RunEvent.run_response_content: "代理响应内容",
            RunEvent.tool_call_started: "工具调用开始",
            RunEvent.tool_call_completed: "工具调用完成",
            RunEvent.reasoning_started: "推理开始",
            RunEvent.reasoning_step: "推理步骤",
            RunEvent.reasoning_completed: "推理完成",
            RunEvent.memory_update_started: "内存更新开始",
            RunEvent.memory_update_completed: "内存更新完成",
            RunEvent.parser_model_response_started: "解析器模型响应开始",
            RunEvent.parser_model_response_completed: "解析器模型响应完成",
        }
        
        team_events = {
            TeamRunEvent.run_started: "团队运行开始",
            TeamRunEvent.run_completed: "团队运行完成",
            TeamRunEvent.run_error: "团队运行错误",
            TeamRunEvent.run_cancelled: "团队运行取消",
            TeamRunEvent.run_response_content: "团队响应内容",
            TeamRunEvent.tool_call_started: "团队工具调用开始",
            TeamRunEvent.tool_call_completed: "团队工具调用完成",
            TeamRunEvent.reasoning_started: "团队推理开始",
            TeamRunEvent.reasoning_step: "团队推理步骤",
            TeamRunEvent.reasoning_completed: "团队推理完成",
            TeamRunEvent.memory_update_started: "团队内存更新开始",
            TeamRunEvent.memory_update_completed: "团队内存更新完成",
            TeamRunEvent.parser_model_response_started: "团队解析器模型响应开始",
            TeamRunEvent.parser_model_response_completed: "团队解析器模型响应完成",
        }
        
        print("\n📋 代理事件类型:")
        for event, description in agent_events.items():
            print(f"  • {event.value:<30} - {description}")
        
        print("\n👥 团队事件类型:")
        for event, description in team_events.items():
            print(f"  • {event.value:<30} - {description}")
        
        print("=" * 80)
    
    def show_basic_usage(self) -> None:
        """显示基本用法"""
        print("=" * 80)
        print("🚀 基本事件监听用法")
        print("=" * 80)
        
        basic_example = '''
# 基本事件监听模式
async def basic_event_listener():
    agent = Agent(
        name="示例代理",
        model=OpenAIChat(id="gpt-4o"),
        tools=[YFinanceTools()]
    )
    
    # 启用流式响应和中间步骤监听
    async for event in await agent.arun(
        "查询苹果股价",
        stream=True,
        stream_intermediate_steps=True,
    ):
        # 处理不同类型的事件
        if event.event == RunEvent.run_started:
            print(f"运行开始: {event.agent_name}")
        
        elif event.event == RunEvent.tool_call_started:
            print(f"工具调用: {event.tool.tool_name}")
        
        elif event.event == RunEvent.run_response_content:
            print(event.content, end="")
        
        elif event.event == RunEvent.run_completed:
            print(f"运行完成: {event.agent_name}")
        '''
        
        print(basic_example)
        print("=" * 80)
    
    def show_advanced_patterns(self) -> None:
        """显示高级使用模式"""
        print("=" * 80)
        print("🔧 高级事件处理模式")
        print("=" * 80)
        
        advanced_example = '''
# 高级事件处理模式
class AdvancedEventHandler:
    def __init__(self):
        self.event_stats = {}
        self.tool_performance = {}
        
    async def handle_event(self, event):
        # 1. 事件统计
        event_type = event.event
        self.event_stats[event_type] = self.event_stats.get(event_type, 0) + 1
        
        # 2. 工具性能监控
        if event.event == RunEvent.tool_call_started:
            self.tool_performance[event.tool.tool_name] = {
                "start_time": time.time(),
                "calls": self.tool_performance.get(event.tool.tool_name, {}).get("calls", 0) + 1
            }
        
        elif event.event == RunEvent.tool_call_completed:
            tool_name = event.tool.tool_name
            if tool_name in self.tool_performance:
                duration = time.time() - self.tool_performance[tool_name]["start_time"]
                self.tool_performance[tool_name]["last_duration"] = duration
        
        # 3. 推理过程跟踪
        elif event.event == RunEvent.reasoning_step:
            reasoning_content = getattr(event, 'reasoning_content', '')
            # 分析推理内容，提取关键信息
            self.analyze_reasoning(reasoning_content)
        
        # 4. 错误处理
        elif event.event == RunEvent.run_error:
            await self.handle_error(event)
            
    def analyze_reasoning(self, content):
        # 分析推理内容的自定义逻辑
        pass
        
    async def handle_error(self, event):
        # 错误处理逻辑
        print(f"检测到错误: {event.content}")
        '''
        
        print(advanced_example)
        print("=" * 80)
    
    def show_best_practices(self) -> None:
        """显示最佳实践"""
        print("=" * 80)
        print("⭐ 事件系统最佳实践")
        print("=" * 80)
        
        practices = [
            "1. 总是使用 stream=True 和 stream_intermediate_steps=True 来获取完整的事件流",
            "2. 使用事件处理器类来组织复杂的事件处理逻辑",
            "3. 实现事件过滤器来避免处理不必要的事件",
            "4. 使用异步处理来避免阻塞事件流",
            "5. 记录事件统计信息来分析代理性能",
            "6. 为不同类型的事件实现不同的处理策略",
            "7. 使用事件来实现实时监控和调试",
            "8. 在团队场景中，注意区分个体代理事件和团队事件",
            "9. 实现错误恢复机制来处理事件处理中的异常",
            "10. 使用事件来实现用户交互和反馈机制"
        ]
        
        for practice in practices:
            print(f"  {practice}")
        
        print("=" * 80)
    
    def show_common_use_cases(self) -> None:
        """显示常见使用场景"""
        print("=" * 80)
        print("🎯 常见使用场景")
        print("=" * 80)
        
        use_cases = {
            "🔍 实时监控": "监控代理运行状态、工具调用次数、执行时间等",
            "📊 性能分析": "分析代理执行效率、工具使用情况、推理步骤等",
            "🐛 调试和诊断": "跟踪代理执行过程、定位问题、分析异常",
            "📝 日志记录": "记录代理活动、创建审计日志、跟踪用户交互",
            "🚨 告警和通知": "设置阈值告警、异常通知、状态变化提醒",
            "🎮 用户交互": "实现实时聊天、进度显示、交互式操作",
            "🔧 系统集成": "与外部系统集成、触发后续流程、数据同步",
            "📈 业务分析": "分析用户行为、统计使用情况、优化策略",
            "🎨 UI更新": "实时更新用户界面、显示执行状态、展示结果",
            "🔐 安全审计": "记录敏感操作、监控异常行为、合规检查"
        }
        
        for scenario, description in use_cases.items():
            print(f"  {scenario}: {description}")
        
        print("=" * 80)
    
    def show_team_event_specifics(self) -> None:
        """显示团队事件特殊性"""
        print("=" * 80)
        print("👥 团队事件特殊性")
        print("=" * 80)
        
        team_specifics = '''
团队事件与单个代理事件的区别：

1. 事件来源标识
   - 团队事件包含 team_session_id 字段
   - 个体事件包含 agent_id 和 agent_name 字段
   
2. 事件处理策略
   - 团队事件需要区分不同代理的活动
   - 可能需要协调多个代理的事件序列
   
3. 性能考虑
   - 团队事件量可能比单个代理事件多
   - 需要高效的事件分发和处理机制
   
4. 使用场景
   - 团队协作过程监控
   - 代理间通信跟踪
   - 集体决策过程分析
   
示例团队事件处理：
```python
async def handle_team_event(event):
    if event.event == TeamRunEvent.run_started:
        print(f"团队开始工作: {event.team_session_id}")
    
    elif event.event == TeamRunEvent.tool_call_started:
        print(f"{event.agent_name} 开始使用工具 {event.tool.tool_name}")
    
    elif event.event == TeamRunEvent.run_response_content:
        print(f"{event.agent_name}: {event.content}")
```
        '''
        
        print(team_specifics)
        print("=" * 80)
    
    def show_complete_guide(self) -> None:
        """显示完整指南"""
        self.show_event_types()
        self.show_basic_usage()
        self.show_advanced_patterns()
        self.show_best_practices()
        self.show_common_use_cases()
        self.show_team_event_specifics()
        
        print("\n" + "=" * 80)
        print("🎉 恭喜！您已经掌握了 agno 框架的事件系统使用方法")
        print("=" * 80)
        print("📚 推荐阅读:")
        print("  • basic_events_demo.py - 基本事件监听示例")
        print("  • reasoning_events_demo.py - 推理事件示例")
        print("  • team_events_demo.py - 团队事件示例")
        print("  • custom_event_handler.py - 自定义事件处理器示例")
        print("=" * 80)


async def main():
    """主函数"""
    guide = EventGuide()
    guide.show_complete_guide()


if __name__ == "__main__":
    asyncio.run(main()) 