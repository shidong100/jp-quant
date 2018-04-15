# -*- coding:utf-8 -*-

import enum
import json
import datetime
import jp_utils


# 整个策略的基类
class JPBase(object):
    pass


# 自定义序列化编码
class JPUserEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, type):
            return str(obj.__name__)
        elif isinstance(obj, JPBase):
            return jp_utils.jp_convert_to_dict(obj)
        elif isinstance(obj, enum.Enum):
            return obj.value
        return json.JSONEncoder.default(self, obj)


# 运行 方式
class JPRunType(enum.Enum):
    simple = 1  # 编译回测
    run = 2  # 运行回测
    mask = 10
    sim = 11  # 模拟交易
    real = 12  # 实盘交易


# 因子排序类型
class JPSortType(enum.Enum):
    asc = 0  # 从小到大排序
    desc = 1  # 从大到小排序


# 价格因子排序选用的价格类型
class JPPriceType(enum.Enum):
    now = 0  # 当前价
    open = 1  # 开盘价
    pre_open = 2  # 昨日开盘价
    close = 3  # 收盘价
    ma = 4  # N日均价


class JPRecord(JPBase):
    def __init__(self, security, filled, avg_cost=0, price=0):
        self.security = security
        self.filled = filled
        self.avg_cost = avg_cost
        self.price = price
        pass


class JPPlatform(JPBase):
    def __init__(self, context, owner):
        self.context = context
        self.owner = owner
        pass

    ''' ==============================持仓操作函数，共用================================'''

    # 获取总资金
    def get_total_money(self, pindex=0):
        pass

    # 获取持仓资金
    def get_position_money(self, pindex=0):
        pass

    # 获取可用资金
    def get_available_cash(self, pindex=0):
        pass

    # 获取可用资金
    def get_available_cash(self, pindex=0):
        pass

    # 获取所有仓位
    def get_long_positions(self, pindex=0):
        pass

    def get_position_cash(self, pindex=0):
        pass

    def get_position_value(self, pindex=0):
        pass

    # 获取某个仓位
    def get_position(self, security, pindex=0):
        pass

    def open_position(self, security, value, pindex=0):
        pass

    # 开仓，买入指定价值的证券
    # 报单成功并成交（包括全部成交或部分成交，此时成交量大于0），返回True
    # 报单失败或者报单成功但被取消（此时成交量等于0），返回False
    # 报单成功，触发所有规则的when_buy_stock函数
    def open_position_list(self, buy_stocks, pindex=0, cash=0):
        pass

    def close_position(self, position, pindex=0):
        pass

    def clear_position(self, pindex=0):
        pass

    def get_security_info(self, security):
        pass

    def get_current_data(self):
        pass

    def get_trading_days(self, security, N=60):
        pass

    def get_growth_rate(self, security, N=20):
        return N

    def get_growth_arr(self, security, N=20):
        day = N + 1
        df = self.attribute_history(security, day, fields=['close', 'date'])
        df['close'] = (df['close'] - df['close'].shift(-1)) / df['close'].shift(-1)
        return df.dropna()

    def get_growth_arr_2(self, security, N=20):
        return self.attribute_history(security, N, fields=['close'])

    def get_close_price(self, security, N, unit='1d'):
        pass

    def attribute_history(self, security, count, unit='1d', fields=['open', 'close', 'high', 'low', 'volume', 'money'],
                          skip_paused=True, df=True, fq='pre'):
        pass

    def get_price(self, security, start_date=None, end_date=None, frequency='daily', fields=None, skip_paused=False,
                  fq='pre', count=None):
        pass

    def show_stock(self, security):
        pass

    def get_fundamentals_data(self, params):
        pass

    def get_financial_data(self, params):
        pass

    def get_trade_date(self, N=1):
        pass

    def log_debug(self):
        pass

    def log_info(self):
        pass

    def log_warn(self):
        pass

    def log_error(self):
        pass

    @staticmethod
    def py_version():
        import platform
        return platform.python_version()

    def is_py3(self):
        return True if (int(self.py_version()[0]) >= 3) else False

    # 系统函数
    def set_benchmark_(self, security):
        pass

    def set_order_cost_(self, cost, type):
        pass

    def set_slippage_(self, obj):
        pass

    def set_options_(self, key, value):
        pass

    def read_file_(self, path):
        pass

    # 系统函数
    def write_file_(self, path, content, append=False):
        pass

    def record_(self, **kwargs):
        pass

    def send_message_(self, message, channel='weixin'):
        pass

    def get_run_type(self):
        pass

    def get_current_date(self):
        pass

    def get_previous_date(self):
        pass

    def get_start_date(self):
        pass

    def get_end_date(self):
        pass

    def is_macd_gold(self, security):
        pass

    def is_macd_dead(self, security):
        pass


class JPGlobalCls(JPBase):
    context = None
    sell_stocks = []
    buy_stocks = []
    pindex = 0
    stock_pindexs = [pindex]
    op_pindexs = [pindex]

    index_rate = []

    # 启动资金
    start_price = {}
    # 运行类型
    run_type = JPRunType.run

    # 策略字典
    config_json = {}

    # 全局配置
    config = []
    # 交易记录
    trade_record = []
    # 设置买入的股票数
    buy_num = 0

    tmp_black_list = {}

    # 持仓比例
    position_than = 1.0
    
    # 是否发送消息
    is_send_message = False

    def __init__(self, context, owner, platform):
        self.context = context
        self.owner = owner
        self.platform = platform

    # 开仓，买入指定价值的证券
    # 报单成功并成交（包括全部成交或部分成交，此时成交量大于0），返回True
    # 报单失败或者报单成功但被取消（此时成交量等于0），返回False
    # 报单成功，触发所有规则的when_buy_stock函数
    def open_position(self, security, index=0):
        return self.platform.open_position(security, index)

    def open_position_list(self, buy_stocks, index=0, cash=0):
        return self.platform.open_position_list(buy_stocks, index, cash=cash)

    def close_position(self, position, index=0):
        if self.platform.close_position(position, index) and position.security not in self.sell_stocks:
            self.sell_stocks.append(position.security)

    def clear_position(self, index=0):
        self.sell_stocks = list(set(self.sell_stocks + self.platform.clear_position(index)))


class JPRule(JPBase):
    cls = None
    context = None
    platform = None
    # 控制是否不执行操作
    is_break = False

    def __init__(self, params):
        self._params = params.copy()

    def update_params(self, params):
        self._params = params.copy()
        pass

    def reset_params(self, params):
        pass

    def after_code_changed(self):
        pass

    def initialize(self):
        pass

    def handle(self, data):
        pass

    def before(self):
        pass

    def after(self):
        pass

    def update(self):
        pass

    def on_sell_success(self, record):
        pass

    def on_buy_success(self, record):
        pass

    def on_clear_success(self):
        pass


class JPRuleGroup(JPRule):
    rules = []
    enable, name, class_type, param = range(4)

    def __init__(self, params):
        JPRule.__init__(self, params)
        self.config = params.get('config', [])
        pass

    def update_params(self, params):
        JPRule.update_params(self, params)
        self.config = params.get('config', self.config)

    def initialize(self):
        # 创建规则
        self.rules = self.create_rules(self.config)
        for rule in self.rules:
            rule.initialize()
        pass

    def after_code_changed(self):
        # 重整所有规则
        self.rules = self.init_strategy(self.rules)
        pass

    def on_sell_success(self, record):
        for rule in self.rules:
            rule.on_sell_success(record)
        pass

    def on_buy_success(self, record):
        for rule in self.rules:
            rule.on_buy_success(record)
        pass

    def on_clear_success(self):
        for rule in self.rules:
            rule.on_clear_success()
        pass

    def create_rule(self, class_type, params, name):
        obj = class_type(params)
        obj.cn = name
        obj.cls = self.cls
        obj.context = self.cls.context
        obj.platform = self.cls.platform
        return obj

    def before(self):
        JPRule.before(self)
        for rule in self.rules:
            rule.before()

    def after(self):
        JPRule.after(self)
        for rule in self.rules:
            if rule.is_break is False:
                rule.after()

    def handle(self, data):
        for rule in self.rules:
            rule.handle(data)
            if rule.is_break:
                self.is_break = True
                return
        self.is_break = False

    # 根据规则配置创建规则执行器
    def create_rules(self, config):
        # return config
        return [self.create_rule(c[self.class_type], c[self.param], c[self.name]) for c in config if
                c[self.enable]]

    def init_strategy(self, rules):
        nl = []
        config = self.config
        for c in config:
            # 按顺序循环处理新规则
            if not c[self.enable]:  # 不使用则跳过
                continue

            # 查找旧规则是否存在
            find_old = None
            for old_r in rules:
                if old_r.__class__ == c[self.class_type] and old_r.cn == c[self.name]:
                    find_old = old_r
                    break
            if find_old is not None:
                find_old = old_r
                # 旧规则存在则添加到新列表中,并调用规则的更新函数，更新参数。
                nl.append(find_old)
                find_old.update_params(c[self.param])
                find_old.after_code_changed()
            else:
                # 旧规则不存在，则创建并添加
                new_r = self.create_rule(c[self.class_type], c[self.param], c[self.name])
                nl.append(new_r)
                # 调用初始化时该执行的函数
                new_r.initialize()
        return nl
