"""
自定义事件处理器演示
展示如何创建自定义的事件处理器和事件监听器
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field

from agno.agent import Agent, RunEvent
from agno.models.openai.chat import OpenAIChat
from agno.run.response import RunResponseEvent
from agno.tools.yfinance import YFinanceTools
from agno.tools.duckduckgo import DuckDuckGoTools


@dataclass
class EventMetrics:
    """事件指标数据类"""
    total_events: int = 0
    event_types: Dict[str, int] = field(default_factory=dict)
    tool_calls: Dict[str, int] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    reasoning_steps: int = 0
    content_chunks: int = 0
    
    def duration(self) -> float:
        """计算执行时间"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class EventHandler:
    """事件处理器基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    async def handle_event(self, event: RunResponseEvent) -> None:
        """处理事件的方法，子类需要实现"""
        pass
    
    def enable(self) -> None:
        """启用事件处理器"""
        self.enabled = True
    
    def disable(self) -> None:
        """禁用事件处理器"""
        self.enabled = False


class MetricsEventHandler(EventHandler):
    """指标收集事件处理器"""
    
    def __init__(self):
        super().__init__("指标收集器")
        self.metrics = EventMetrics()
        self.event_log: List[Dict] = []
    
    async def handle_event(self, event: RunResponseEvent) -> None:
        """收集事件指标"""
        if not self.enabled:
            return
            
        # 增加总事件计数
        self.metrics.total_events += 1
        
        # 记录事件类型
        event_type = event.event
        self.metrics.event_types[event_type] = self.metrics.event_types.get(event_type, 0) + 1
        
        # 记录开始时间
        if event.event == RunEvent.run_started:
            self.metrics.start_time = datetime.now()
        
        # 记录结束时间
        elif event.event == RunEvent.run_completed:
            self.metrics.end_time = datetime.now()
        
        # 记录工具调用
        elif event.event == RunEvent.tool_call_started:
            tool_name = event.tool.tool_name
            self.metrics.tool_calls[tool_name] = self.metrics.tool_calls.get(tool_name, 0) + 1
        
        # 记录推理步骤
        elif event.event == RunEvent.reasoning_step:
            self.metrics.reasoning_steps += 1
        
        # 记录内容块
        elif event.event == RunEvent.run_response_content:
            self.metrics.content_chunks += 1
        
        # 记录事件日志
        self.event_log.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "agent_id": getattr(event, 'agent_id', None),
            "agent_name": getattr(event, 'agent_name', None),
            "run_id": getattr(event, 'run_id', None),
        })
    
    def get_metrics_report(self) -> Dict:
        """获取指标报告"""
        return {
            "总事件数": self.metrics.total_events,
            "执行时间": f"{self.metrics.duration():.2f}秒",
            "事件类型分布": self.metrics.event_types,
            "工具调用统计": self.metrics.tool_calls,
            "推理步骤数": self.metrics.reasoning_steps,
            "内容块数": self.metrics.content_chunks,
        }


class LoggingEventHandler(EventHandler):
    """日志记录事件处理器"""
    
    def __init__(self, log_file: str = "agent_events.log"):
        super().__init__("日志记录器")
        self.log_file = log_file
        self.logs: List[str] = []
    
    async def handle_event(self, event: RunResponseEvent) -> None:
        """记录事件日志"""
        if not self.enabled:
            return
            
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {event.event}"
        
        if hasattr(event, 'agent_name') and event.agent_name:
            log_entry += f" - {event.agent_name}"
        
        if event.event == RunEvent.tool_call_started:
            log_entry += f" - 工具: {event.tool.tool_name}"
        
        elif event.event == RunEvent.reasoning_step:
            reasoning_content = getattr(event, 'reasoning_content', '')
            if reasoning_content:
                log_entry += f" - 推理: {reasoning_content[:50]}..."
        
        self.logs.append(log_entry)
    
    def save_logs(self) -> None:
        """保存日志到文件"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.logs))
            print(f"✅ 日志已保存到 {self.log_file}")
        except Exception as e:
            print(f"❌ 保存日志失败: {e}")
    
    def get_logs(self) -> List[str]:
        """获取日志记录"""
        return self.logs


class AlertEventHandler(EventHandler):
    """告警事件处理器"""
    
    def __init__(self, alert_threshold: int = 5):
        super().__init__("告警处理器")
        self.alert_threshold = alert_threshold
        self.tool_call_count = 0
        self.error_count = 0
    
    async def handle_event(self, event: RunResponseEvent) -> None:
        """处理告警事件"""
        if not self.enabled:
            return
            
        # 监控工具调用次数
        if event.event == RunEvent.tool_call_started:
            self.tool_call_count += 1
            if self.tool_call_count >= self.alert_threshold:
                print(f"⚠️  告警: 工具调用次数过多 ({self.tool_call_count})")
        
        # 监控错误事件
        elif event.event == RunEvent.run_error:
            self.error_count += 1
            print(f"🚨 告警: 检测到运行错误 (错误计数: {self.error_count})")
            if hasattr(event, 'content') and event.content:
                print(f"   错误详情: {event.content}")


class CustomEventProcessor:
    """自定义事件处理器管理器"""
    
    def __init__(self):
        self.handlers: List[EventHandler] = []
        self.event_filters: Dict[str, List[Callable]] = {}
        
        # 添加默认处理器
        self.metrics_handler = MetricsEventHandler()
        self.logging_handler = LoggingEventHandler()
        self.alert_handler = AlertEventHandler()
        
        self.add_handler(self.metrics_handler)
        self.add_handler(self.logging_handler)
        self.add_handler(self.alert_handler)
    
    def add_handler(self, handler: EventHandler) -> None:
        """添加事件处理器"""
        self.handlers.append(handler)
        print(f"✅ 已添加事件处理器: {handler.name}")
    
    def remove_handler(self, handler: EventHandler) -> None:
        """移除事件处理器"""
        if handler in self.handlers:
            self.handlers.remove(handler)
            print(f"❌ 已移除事件处理器: {handler.name}")
    
    def add_event_filter(self, event_type: str, filter_func: Callable) -> None:
        """添加事件过滤器"""
        if event_type not in self.event_filters:
            self.event_filters[event_type] = []
        self.event_filters[event_type].append(filter_func)
    
    async def process_event(self, event: RunResponseEvent) -> None:
        """处理事件"""
        # 应用过滤器
        if event.event in self.event_filters:
            for filter_func in self.event_filters[event.event]:
                if not filter_func(event):
                    return  # 过滤掉该事件
        
        # 分发事件到所有处理器
        for handler in self.handlers:
            try:
                await handler.handle_event(event)
            except Exception as e:
                print(f"❌ 处理器 {handler.name} 处理事件时出错: {e}")
    
    def get_summary(self) -> Dict:
        """获取处理器摘要"""
        return {
            "处理器数量": len(self.handlers),
            "活跃处理器": [h.name for h in self.handlers if h.enabled],
            "指标报告": self.metrics_handler.get_metrics_report(),
            "日志条目数": len(self.logging_handler.get_logs()),
        }


class CustomEventDemo:
    """自定义事件演示类"""
    
    def __init__(self):
        self.agent = Agent(
            agent_id="custom-event-demo",
            name="自定义事件演示代理",
            model=OpenAIChat(id="gpt-4o"),
            tools=[YFinanceTools(), DuckDuckGoTools()],
            reasoning=True,
            description="用于演示自定义事件处理的代理"
        )
        
        self.event_processor = CustomEventProcessor()
        
        # 添加自定义过滤器
        self.event_processor.add_event_filter(
            RunEvent.run_response_content,
            lambda event: len(event.content) > 5 if event.content else False
        )
    
    async def run_demo_with_custom_handlers(self, prompt: str) -> None:
        """使用自定义事件处理器运行演示"""
        print("=" * 80)
        print("🎛️  开始自定义事件处理器演示")
        print("=" * 80)
        print(f"任务: {prompt}")
        print("=" * 80)
        
        try:
            # 使用流式响应并监听中间步骤
            async for event in await self.agent.arun(
                prompt,
                stream=True,
                stream_intermediate_steps=True,
            ):
                await self.event_processor.process_event(event)
                
                # 实时显示部分事件
                if event.event == RunEvent.run_response_content and event.content:
                    print(event.content, end="", flush=True)
                
            print("\n" + "=" * 80)
            print("📊 自定义事件处理器摘要:")
            summary = self.event_processor.get_summary()
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            print("=" * 80)
            
            # 保存日志
            self.event_processor.logging_handler.save_logs()
            
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    async def run_advanced_demo(self) -> None:
        """运行高级演示"""
        advanced_task = """
        请帮我进行综合分析：
        1. 获取特斯拉(TSLA)的股价信息
        2. 搜索关于电动汽车行业的最新新闻
        3. 分析特斯拉的投资价值
        4. 提供详细的投资建议和风险评估
        
        请进行深度推理分析。
        """
        
        await self.run_demo_with_custom_handlers(advanced_task)


async def main():
    """主函数"""
    demo = CustomEventDemo()
    await demo.run_advanced_demo()


if __name__ == "__main__":
    asyncio.run(main()) 