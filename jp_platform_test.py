
from jp_base import JPGlobalCls
from jp_strategy import JPGroupStrategy


# 开盘前运行
# 1. 实际回测中 context 必须不能传None（必须传各平台传过来的context）
# 2. 实际回测中 platform 必须不能传None（必须继承JPPlatform根据各平台实现各个功能函数）
strategy = JPGroupStrategy(None, {
    'name': '通用跨平台小市值测试策略',
    'class': JPGlobalCls,
    'platform': None,
    'config': {}
})
strategy.initialize()

