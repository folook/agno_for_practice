"""
运行所有事件演示
提供一个统一的入口来运行所有事件演示
"""

import asyncio
import sys
from typing import Dict, Callable

# 导入所有演示模块
from basic_events_demo import EventsDemo
from reasoning_events_demo import ReasoningEventsDemo
from team_events_demo import TeamEventsDemo
from custom_event_handler import CustomEventDemo
from event_usage_guide import EventGuide


class DemoRunner:
    """演示运行器"""

    def __init__(self):
        self.demos: Dict[str, Callable] = {
            "指南": self.show_guide,
            "基本事件": self.run_basic_events,
            "推理事件": self.run_reasoning_events,
            "团队事件": self.run_team_events,
            "自定义处理器": self.run_custom_handler,
            "所有演示": self.run_all_demos,
        }

        self.guide = EventGuide()
        self.basic_demo = EventsDemo()
        self.reasoning_demo = ReasoningEventsDemo()
        # self.team_demo = TeamEventsDemo()
        self.custom_demo = CustomEventDemo()

    def show_menu(self) -> None:
        """显示菜单"""
        print("=" * 80)
        print("🎭 AGNO 框架事件系统演示中心")
        print("=" * 80)
        print("请选择要运行的演示:")

        for i, (name, _) in enumerate(self.demos.items(), 1):
            print(f"  {i}. {name}")

        print("  0. 退出")
        print("=" * 80)

    async def show_guide(self) -> None:
        """显示使用指南"""
        self.guide.show_complete_guide()

    async def run_basic_events(self) -> None:
        """运行基本事件演示"""
        print("\n🚀 运行基本事件演示...")
        await self.basic_demo.run_demo()

    async def run_reasoning_events(self) -> None:
        """运行推理事件演示"""
        print("\n🧠 运行推理事件演示...")
        await self.reasoning_demo.run_simple_reasoning_demo()

    async def run_team_events(self) -> None:
        """运行团队事件演示"""
        print("\n👥 运行团队事件演示...")
        await self.team_demo.run_investment_analysis_demo()

    async def run_custom_handler(self) -> None:
        """运行自定义处理器演示"""
        print("\n🎛️ 运行自定义处理器演示...")
        await self.custom_demo.run_advanced_demo()

    async def run_all_demos(self) -> None:
        """运行所有演示"""
        print("\n🎪 运行所有演示...")

        demos = [
            ("基本事件演示", self.run_basic_events),
            ("推理事件演示", self.run_reasoning_events),
            ("团队事件演示", self.run_team_events),
            ("自定义处理器演示", self.run_custom_handler),
        ]

        for name, demo_func in demos:
            print(f"\n{'='*20} {name} {'='*20}")
            try:
                await demo_func()
            except Exception as e:
                print(f"❌ {name} 运行失败: {e}")

            print(f"\n{'='*20} {name} 完成 {'='*20}")

            # 暂停一下，让用户查看结果
            input("\n按回车键继续下一个演示...")

    async def run_interactive(self) -> None:
        """运行交互式演示选择"""
        while True:
            self.show_menu()

            try:
                choice = input("请输入选择 (0-6): ").strip()

                if choice == "0":
                    print("👋 感谢使用 AGNO 事件系统演示！")
                    break

                choice_num = int(choice)
                if 1 <= choice_num <= len(self.demos):
                    demo_name = list(self.demos.keys())[choice_num - 1]
                    demo_func = self.demos[demo_name]

                    print(f"\n🎯 开始运行: {demo_name}")
                    print("=" * 80)

                    try:
                        await demo_func()
                    except Exception as e:
                        print(f"❌ 演示运行失败: {e}")

                    print("\n" + "=" * 80)
                    print(f"✅ {demo_name} 演示完成")
                    input("\n按回车键继续...")
                else:
                    print("❌ 无效选择，请重试")

            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                print("\n👋 用户中断，退出演示")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")

    def show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
🎯 AGNO 事件系统演示说明

本演示包含以下内容：

1. 📚 指南 - 完整的事件系统使用指南
   - 所有事件类型说明
   - 基本用法示例
   - 高级使用模式
   - 最佳实践
   - 常见使用场景

2. 🚀 基本事件 - 基本事件监听演示
   - 代理运行事件
   - 工具调用事件
   - 响应内容事件
   - 事件统计

3. 🧠 推理事件 - 推理过程事件演示
   - 推理开始/完成事件
   - 推理步骤事件
   - 推理内容分析

4. 👥 团队事件 - 团队协作事件演示
   - 团队运行事件
   - 多代理协作
   - 团队活动日志

5. 🎛️ 自定义处理器 - 高级事件处理演示
   - 自定义事件处理器
   - 事件过滤器
   - 指标收集
   - 日志记录
   - 告警机制

6. 🎪 所有演示 - 依次运行所有演示

使用方法：
- 运行 python run_all_demos.py 进入交互式菜单
- 或者直接运行单个演示文件
        """
        print(help_text)


async def main():
    """主函数"""
    runner = DemoRunner()

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ["help", "-h", "--help"]:
            runner.show_help()
        elif arg == "guide":
            await runner.show_guide()
        elif arg == "basic":
            await runner.run_basic_events()
        elif arg == "reasoning":
            await runner.run_reasoning_events()
        elif arg == "team":
            await runner.run_team_events()
        elif arg == "custom":
            await runner.run_custom_handler()
        elif arg == "all":
            await runner.run_all_demos()
        else:
            print(f"❌ 未知参数: {arg}")
            runner.show_help()
    else:
        await runner.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
