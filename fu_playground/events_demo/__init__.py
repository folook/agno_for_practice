"""
AGNO 框架事件系统演示包

本包包含了 AGNO 框架事件系统的完整演示和使用指南。

模块说明：
- basic_events_demo: 基本事件监听演示
- reasoning_events_demo: 推理事件演示  
- team_events_demo: 团队事件演示
- custom_event_handler: 自定义事件处理器演示
- event_usage_guide: 事件系统使用指南
- run_all_demos: 运行所有演示的统一入口

使用方法：
1. 运行 python run_all_demos.py 进入交互式菜单
2. 或者直接运行单个演示文件
3. 查看 README.md 了解详细使用说明

作者: Fu Manhua
版本: 1.0
"""

__version__ = "1.0"
__author__ = "Fu Manhua"
__email__ = "fumanhua@example.com"

# 导入主要的演示类
from .basic_events_demo import EventsDemo
from .reasoning_events_demo import ReasoningEventsDemo
from .team_events_demo import TeamEventsDemo
from .custom_event_handler import CustomEventDemo, CustomEventProcessor
from .event_usage_guide import EventGuide

__all__ = [
    "EventsDemo",
    "ReasoningEventsDemo", 
    "TeamEventsDemo",
    "CustomEventDemo",
    "CustomEventProcessor",
    "EventGuide",
] 