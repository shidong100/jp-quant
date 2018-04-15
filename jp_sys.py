# -*- coding:utf-8 -*-

import enum

from jp_base import JPRule

# '''---------------------------------系统参数一般性设置---------------------------------'''

# 滑点类型类型


class JPSlippageType(enum.Enum):
    percent = 0  # 百分比滑点
    fixed = 1  # 固定滑点


class JPSysParams(JPRule):

    def __init__(self, params):
        JPRule.__init__(self, params)
        self.buy_min_money = params.get('buy_min_money', 10000)
        self.benchmark = params.get('benchmark', '000300.XSHG')
        self.slippage = params.get('slippage', {})
        self.slip_value = self.slippage.get('value', 0.04)
        self.slip_type = self.slippage.get('type', JPSlippageType.fixed)
        pass

    def initialize(self):
        self.cls.buy_min_money = self.buy_min_money
        self.platform.set_benchmark_(self.benchmark)
        slippage = self._params.get('slippage', None)
        self.platform.set_slippage_(self.slip_value, self.slip_type)
    
    def update_params(self, params):
        JPRule.update_params(self, params)
        self.buy_min_money = params.get('buy_min_money', 10000)
        self.benchmark = params.get('benchmark', '000300.XSHG')
        self.slippage = params.get('slippage', {})
        self.slip_value = self.slippage.get('value', 0.04)
        self.slip_type = self.slippage.get('type', JPSlippageType.fixed)
        pass 

    def __str__(self):
        return '设置系统参数：[使用真实价格交易] [忽略order 的 log] [设置基准]'

    
'''系统消息'''


class JPSysMessage(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)
        self.is_send_message = params.get('is_send_message', False)
        pass
    
    def update_params(self, params):
        JPRule.update_params(self, params)
        self.is_send_message = params.get('is_send_message', False)
        pass 
    
    def initialize(self):
        self.cls.is_send_message = self.is_send_message
        pass