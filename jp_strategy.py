# -*- coding:utf-8 -*-

import hashlib
import json

from jp_base import JPGlobalCls
from jp_base import JPPlatform
from jp_base import JPRuleGroup
from jp_base import JPRunType


class JPGroupStrategy(JPRuleGroup):
    def __init__(self, context, params):
        JPRuleGroup.__init__(self, params)
        self.cn = params.get('name', None)
        self.platform = params.get('platform', JPPlatform)(context, self)
        self.cls = params.get('class', JPGlobalCls)(context, self, self.platform)
        self.cls.run_type = self.platform.get_run_type()
        self.get_strategy_dict()
        if self.platform.get_run_type() == JPRunType.simple:
            self.platform.log_info('=============>>>>编译回测开始<<<<<============')
        elif self.platform.get_run_type() == JPRunType.run:
            self.platform.log_info('=============>>>>运行回测开始<<<<<============')
        elif self.platform.get_run_type() == JPRunType.sim:
            self.platform.log_info('=============>>>>模拟交易开始<<<<<============')
        elif self.platform.get_run_type() == JPRunType.real:
            self.platform.log_info('=============>>>>实盘交易开始<<<<<============')

    def initialize(self):
        JPRuleGroup.initialize(self)
        pass

    def update_params(self, params):
        JPRuleGroup.update_params(self, params)
        self.cls.config = self.config
        self.get_strategy_dict()

    def handle(self, data):
        for rule in self.rules:
            rule.handle(data)
            if rule.is_break and not isinstance(rule, JPGroupStrategy):  # 这里新增控制，假如是其它策略组合器要求退出的话，不退出。
                self.is_break = True
                return
        self.is_break = False


    def before(self):
        JPRuleGroup.before(self)
        self.platform.log_info('=================>>>一天开始<<<=====================\n')


    def get_strategy_dict(self):
        if self.config is not None and len(self.config) > 0:
            copy_config = self.config[:]
            copy_config.append(str(self.platform.get_start_date()))
            copy_config.append(str(self.platform.get_end_date()))
            sid = hashlib.md5(str(copy_config).encode(encoding='utf-8')).hexdigest()
            self.cls.config_json[sid] = copy_config
            self.cls.config_json['sid'] = sid
            self.cls.config_json['start_date'] = str(self.platform.get_start_date())
            self.cls.config_json['end_date'] = str(self.platform.get_end_date())



