# AGNO 框架事件系统演示

本目录包含了 AGNO 框架事件系统的完整演示和使用指南。

## 📋 目录结构

```
events_demo/
├── README.md                    # 本文件
├── basic_events_demo.py         # 基本事件监听演示
├── reasoning_events_demo.py     # 推理事件演示
├── team_events_demo.py          # 团队事件演示
├── custom_event_handler.py      # 自定义事件处理器演示
├── event_usage_guide.py         # 事件系统使用指南
└── run_all_demos.py            # 运行所有演示的统一入口
```

## 🎯 AGNO 事件系统概述

AGNO 框架提供了丰富的事件系统，允许开发者监听和处理代理运行过程中的各种事件。主要事件类型包括：

### 🚀 基本事件
- `run_started` - 代理运行开始
- `run_completed` - 代理运行完成
- `run_error` - 代理运行错误
- `run_cancelled` - 代理运行取消
- `run_response_content` - 代理响应内容

### 🔧 工具事件
- `tool_call_started` - 工具调用开始
- `tool_call_completed` - 工具调用完成

### 🧠 推理事件
- `reasoning_started` - 推理开始
- `reasoning_step` - 推理步骤
- `reasoning_completed` - 推理完成

### 👥 团队事件
- `team_run_started` - 团队运行开始
- `team_tool_call_started` - 团队工具调用开始
- `team_reasoning_started` - 团队推理开始
- ... 以及其他团队相关事件

## 🚀 快速开始

### 1. 运行完整演示

```bash
# 进入 events_demo 目录
cd fu_playground/events_demo

# 运行交互式演示菜单
python run_all_demos.py

# 或者直接运行特定演示
python run_all_demos.py basic      # 基本事件演示
python run_all_demos.py reasoning  # 推理事件演示
python run_all_demos.py team       # 团队事件演示
python run_all_demos.py custom     # 自定义处理器演示
python run_all_demos.py all        # 所有演示
python run_all_demos.py guide      # 使用指南
```

### 2. 查看使用指南

```bash
python event_usage_guide.py
```

### 3. 运行单个演示

```bash
# 基本事件演示
python basic_events_demo.py

# 推理事件演示
python reasoning_events_demo.py

# 团队事件演示
python team_events_demo.py

# 自定义事件处理器演示
python custom_event_handler.py
```

## 📚 演示说明

### 1. 基本事件演示 (`basic_events_demo.py`)

展示如何监听基本的代理事件：
- 代理运行开始/完成
- 工具调用开始/完成
- 响应内容流式输出
- 事件统计

**关键特性：**
- 事件计数器
- 实时事件处理
- 事件信息提取

### 2. 推理事件演示 (`reasoning_events_demo.py`)

展示如何监听推理过程中的事件：
- 推理开始/完成
- 推理步骤跟踪
- 推理内容分析
- 推理步骤总结

**关键特性：**
- 推理步骤记录
- 推理内容分析
- 推理过程统计

### 3. 团队事件演示 (`team_events_demo.py`)

展示如何监听团队协作中的事件：
- 团队运行开始/完成
- 多代理协作
- 团队活动日志
- 代理间通信跟踪

**关键特性：**
- 团队活动日志
- 代理身份识别
- 团队协作监控

### 4. 自定义事件处理器演示 (`custom_event_handler.py`)

展示如何创建高级的事件处理系统：
- 自定义事件处理器
- 事件过滤器
- 指标收集
- 日志记录
- 告警机制

**关键特性：**
- 模块化事件处理
- 事件过滤机制
- 性能监控
- 告警系统

## 🎯 基本使用模式

### 简单事件监听

```python
import asyncio
from agno.agent import Agent, RunEvent
from agno.models.openai.chat import OpenAIChat

async def basic_event_listener():
    agent = Agent(
        name="示例代理",
        model=OpenAIChat(id="gpt-4o"),
    )
    
    # 启用流式响应和中间步骤监听
    async for event in await agent.arun(
        "你好",
        stream=True,
        stream_intermediate_steps=True,
    ):
        if event.event == RunEvent.run_started:
            print(f"运行开始: {event.agent_name}")
        elif event.event == RunEvent.run_response_content:
            print(event.content, end="")
        elif event.event == RunEvent.run_completed:
            print(f"\n运行完成: {event.agent_name}")

asyncio.run(basic_event_listener())
```

### 事件处理器模式

```python
class EventHandler:
    def __init__(self):
        self.event_count = 0
    
    async def handle_event(self, event):
        self.event_count += 1
        
        if event.event == RunEvent.tool_call_started:
            print(f"工具调用: {event.tool.tool_name}")
        elif event.event == RunEvent.reasoning_step:
            print(f"推理步骤: {event.reasoning_content[:50]}...")

# 使用事件处理器
handler = EventHandler()
async for event in await agent.arun(prompt, stream=True, stream_intermediate_steps=True):
    await handler.handle_event(event)
```

## 🛠️ 典型使用场景

### 1. 实时监控
- 监控代理运行状态
- 跟踪工具调用情况
- 统计执行时间和性能

### 2. 调试和诊断
- 跟踪代理执行过程
- 定位问题和异常
- 分析推理步骤

### 3. 用户界面更新
- 实时显示代理状态
- 流式输出响应内容
- 显示执行进度

### 4. 日志和审计
- 记录代理活动
- 创建审计日志
- 跟踪用户交互

### 5. 系统集成
- 与外部系统集成
- 触发后续流程
- 数据同步

## ⭐ 最佳实践

1. **总是使用流式响应**
   ```python
   async for event in await agent.arun(
       prompt, 
       stream=True, 
       stream_intermediate_steps=True
   ):
   ```

2. **使用事件处理器类**
   ```python
   class MyEventHandler:
       async def handle_event(self, event):
           # 处理逻辑
           pass
   ```

3. **实现事件过滤**
   ```python
   if event.event in [RunEvent.run_started, RunEvent.run_completed]:
       # 只处理特定事件
       pass
   ```

4. **异步处理**
   ```python
   async def handle_event(self, event):
       # 使用异步处理避免阻塞
       await some_async_operation()
   ```

5. **错误处理**
   ```python
   try:
       await handler.handle_event(event)
   except Exception as e:
       print(f"事件处理错误: {e}")
   ```

## 📝 注意事项

1. **虚拟环境**
   - 确保在正确的虚拟环境中运行
   - 安装所需的依赖包

2. **API 密钥**
   - 确保设置了正确的 OpenAI API 密钥
   - 检查网络连接

3. **依赖包**
   - 确保安装了 agno 框架
   - 检查工具包依赖（如 yfinance、duckduckgo-search）

4. **性能考虑**
   - 事件处理应该尽可能快速
   - 避免在事件处理中进行耗时操作

## 🤝 贡献

欢迎提供反馈和改进建议！如果您发现问题或有新的演示想法，请创建 issue 或提交 pull request。

## 📄 许可证

本演示遵循 AGNO 框架的许可证。 