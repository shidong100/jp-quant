# -*- coding:utf-8 -*-
import pandas as pd
import json
import datetime

from jp_base import JPRule
from jp_base import JPRuleGroup
from jp_base import JPRunType
import jp_utils


class JPGroupRuleTrans(JPRuleGroup):
    def __init__(self, params):
        JPRuleGroup.__init__(self, params)
        self.has_run = False

    def handle(self, data):
        for rule in self.rules:
            rule.handle(data)


class JPTransSellStocks(JPRule):
    def handle(self, data):
        # 卖出不在待买股票列表中的股票
        # 对于因停牌等原因没有卖出的股票则继续持有
        buy_stocks = self.cls.buy_stocks
        pindex = self.cls.pindex
        long_positions = self.platform.get_long_positions(pindex)
        for stock, position in long_positions.items():
            if stock not in buy_stocks:
                self.cls.close_position(position, pindex)

    def __str__(self):
        return '股票调仓卖出规则：卖出不在buy_stocks的股票'


class JPTransBuyStocks(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)

    def handle(self, data):
        # 买入股票
        # 始终保持持仓数目为g.buy_stock_count
        # 根据股票数量分仓
        # 此处只根据可用金额平均分配购买，不能保证每个仓位平均分配
        buy_stocks = [stock for stock in self.cls.buy_stocks if stock not in self.cls.sell_stocks]
        buy_cash = self.platform.get_total_money() * self.cls.position_than - self.platform.get_position_money()
        if buy_cash > 0:
            self.cls.open_position_list(buy_stocks, cash=buy_cash)
        pass

    def after(self):
        self.cls.sell_stocks = []

    def __str__(self):
        return '股票调仓买入规则：现金平分式买入股票达目标股票数'


class JPTransTime(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)
        # 配置调仓时间 times为二维数组，示例[[10,30],[14,30]] 表示 10:30和14：30分调仓
        self.time = params.get('time', [])

    def update_params(self, params):
        JPRule.update_params(self, params)
        self.time = params.get('time', self.time)
        pass

    def handle(self, data):
        current_dt = self.platform.get_current_date()
        hour = current_dt.hour
        minute = current_dt.minute
        self.is_break = not [hour, minute] in self.time
        pass

    def __str__(self):
        return '调仓时间控制器: [调仓时间: %s ]' % (
            str(['%d:%d' % (x[0], x[1]) for x in self.time]))


# '''-------------------------调仓日计数器-----------------------'''
class JPTransPeriod(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)
        # 调仓日计数器，单位：日
        self.period = params.get('period', 3)
        self.hold_days = 0

    def update_params(self, params):
        JPRule.update_params(self, params)
        self.period = params.get('period', self.period)

    def handle(self, data):
        self.platform.log_info("调仓日计数 [%d]" % self.hold_days)
        long_positions = self.platform.get_long_positions(self.cls.pindex)
        self.is_break = self.hold_days % self.period != 0 and (
            len(long_positions) == self.cls.buy_num and self.cls.buy_num > 0)
        self.hold_days += 1
        pass

    def on_sell_stock(self, position, order):
        pass

    # 清仓时调用的函数
    def on_clear_success(self):
        self.hold_days = 0
        pass

    def __str__(self):
        return '调仓日计数器:[调仓频率: %d日] [调仓日计数 %d]' % (
            self.period, self.hold_days)


'''大盘涨幅过大清仓'''


class JPTransPositionIndex(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)
        self.index = params.get('index', '000001.XSHG')
        self.period = params.get('period', 160)
        self.multiple = params.get('multiple', 2.2)
        self.is_clear_position = False

    def update_params(self, params):
        JPRule.update_params(self, params)
        self.index = params.get('index', '000001.XSHG')
        self.period = params.get('period', 160)
        self.multiple = params.get('multiple', 2.2)
        self.is_clear_position = False

    def handle(self, data):
        # 大盘指数前130日内最高价超过最低价2倍，则清仓止损
        # 基于历史数据判定，因此若状态满足，则当天都不会变化
        # 增加此止损，回撤降低，收益降低

        if not self.is_clear_position:
            h = self.platform.attribute_history(self.index, self.period, unit='1d', fields=['close', 'high', 'low'],
                                                skip_paused=True)
            period_low_price = h.low.min()
            period_high_price = h.high.max()
            if period_high_price > self.multiple * period_low_price and h['close'][-4] * 1 > h['close'][-1] > \
                    h['close'][-100]:
                # 当日第一次输出日志
                self.platform.log_info("==> 大盘止损，%s指数前130日内最高价超过最低价2倍, 最高价: %f, 最低价: %f" % (
                    self.platform.show_stock(self.index), period_high_price, period_low_price))
                self.is_clear_position = True

        if self.is_clear_position:
            self.cls.clear_position(self.cls.pindex)

        self.is_break = self.is_clear_position

    def before(self):
        self.is_clear_position = False
        pass

    def __str__(self):
        return '大盘高低价比例止损器:[指数: %s] [参数: %s日内最高最低价: %s倍] [当前状态: %s]' % (
            self.index, self.period, self.multiple, self.is_clear_position)


class JPTransIndexGrowthRate(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)
        self.index = params.get('index', ['000010.XSHG', '399678.XSHE'])
        self.min_rate = params.get('min_rate', [0.6, 0.6])
        self.period = params.get('period', 20)
        self.smart = params.get('smart', False)

    def update_params(self, params):
        JPRule.__init__(self, params)
        self.index = params.get('index', ['000010.XSHG', '399678.XSHE'])
        self.min_rate = params.get('min_rate', [0.6, 0.6])
        self.period = params.get('period', 20)
        self.smart = params.get('smart', False)

    def handle(self, data):
        self.is_break = False
        r = []
        if len(self.index) >= len(self.min_rate):
            # 智能切换
            if self.smart is True and self.platform.get_run_type().value < JPRunType.mask.value:
                # 回测
                # 默认计算index2的30日的平均振幅 > 0.3 代表振幅较大 将self.period设置20
                gr_index30 = self.platform.get_growth_rate(self.index[0], 30) * 100
                self.platform.log_info('index2 30天涨幅%.2f%%----%.2f%%' % (gr_index30, gr_index30 / 30.0))
                if (gr_index30 / 20.0) > 0.25:
                    self.period = 20
                else:
                    self.period = 30

            period_date = self.platform.get_trade_date(N=self.period)
            self.platform.log_info('目标日期: ', str(period_date))
            for i in range(len(self.index)):
                index = self.index[i]
                gr_index = self.platform.get_growth_rate(index, self.period) * 100
                r.append(gr_index > self.min_rate[i])
                self.platform.log_info('%d日涨幅  %.2f%%  [%s]' % (self.period, gr_index, self.platform.show_stock(index)))
            if sum(r) == 0:
                self.platform.log_warn('不符合持仓条件，清仓')
                self.cls.clear_position(self.cls.pindex)
                self.is_break = True

    def before(self):
        JPRule.after(self)
        pass

    def __str__(self):
        if len(self.min_rate) >= 2:
            return '多指数%d日涨幅损器[指数:%s] [涨幅:%.2f%%] [涨幅:%.2f%%]' % (self.period,
                                                                  str(self.index), self.min_rate[0], self.min_rate[1])

        return '多指数%d日涨幅止损配置错误' % self.period


'''大盘风险28明显清仓'''


class JPTransIndexGrowthRateDiff(JPRule):
    # df_index = pd.DataFrame(columns=['close'])

    def __init__(self, params):
        self.index = params.get('index', ['000016.XSHG', '399333.XSHE'])
        self.period = params.get('period', 5)
        pass

    def update_params(self, params):
        self.index = params.get('index', ['000016.XSHG', '399333.XSHE'])
        self.period = params.get('period', 5)
        pass

    def handle(self, data):
        self.is_break = False
        num = 2
        r = []
        # 目前只支持两个指数计算
        # 目前只支持两个指数计算
        if len(self.index) == num:
            for i in range(len(self.index)):
                index = self.index[i]
                df_index = self.platform.get_growth_arr_2(index, self.period + 2)
                df_index.columns = df_index.columns.map(lambda x: str(index) + '_' + str(x))
                df_index = jp_utils.jp_calc_rate(df_index, cols=[str(index) + '_close'], method='first')
                r.append(df_index)

        new_df = pd.concat(r, axis=1, join='inner')
        new_df = new_df.apply(lambda x: x * 100)
        new_df['date'] = new_df.index
        if self.platform.is_py3() is not True:
            new_df.set_index(pd.Int64Index(list(range(0, len(new_df)))), inplace=True)
        else:
            new_df.set_index(pd.RangeIndex(start=0, stop=len(new_df)), inplace=True)

        index2_close = str(self.index[0]) + '_close'
        index8_close = str(self.index[1]) + '_close'
        # self.platform.log_info('new_df before: \n', new_df)
        new_df = jp_utils.jp_rolling_slope(new_df, window=self.period, cols=[index2_close, index8_close])
        self.platform.log_info('new_df afters: \n', new_df)
        index2_sum = new_df[index2_close].sum()
        index8_sum = new_df[index8_close].sum()
        if index2_sum > 0 and index8_sum < 0 and index2_sum - index8_sum > 0:
            self.platform.log_warn('不符合持仓条件，2/8分化清仓 %.2f%% %.2ff' % (index2_sum, index8_sum))
            self.cls.clear_position(self.cls.pindex)
            self.is_break = True
    def before(self):
        self.is_break = False
        pass

    def __str__(self):
        return '大盘风险28明显清仓'


class JPTransGainLoss(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)
        self.gain_rate = params.get('gain_rate', 0)
        self.loss_rate = params.get('loss_rate', 0)
        self.black_day = params.get('black_day', 10)

    def update_params(self, params):
        JPRule.update_params(self, params)
        self.gain_rate = params.get('gain_rate', 0)
        self.loss_rate = params.get('loss_rate', 0)
        self.black_day = params.get('black_day', 10)

    def handle(self, data):
        pindex = self.cls.pindex
        long_positions = self.platform.get_long_positions(pindex)
        if len(long_positions) == 0 or (self.gain_rate == 0 and self.loss_rate == 0):
            return
        for stock, position in long_positions.items():
            rate = (position.price - position.avg_cost) / position.avg_cost * 100
            if 0 < self.gain_rate < rate:
                self.platform.log_info('个股涨幅{0} 止盈卖出{1}'.format(rate, stock))
                # 卖出
                self.platform.close_position(self.platform.get_position(stock, pindex=pindex))
            if self.loss_rate > 0 and rate < -self.loss_rate:
                self.platform.log_info('个股涨幅{0} 止损卖出{1}'.format(rate, stock))
                # 卖出
                self.platform.close_position(self.platform.get_position(stock, pindex=pindex))
                # 止损以后加入临时黑名单 black_day 个交易日内剔除该股
                self.cls.tmp_black_list[stock] = self.black_day + 1

        pass

    def before(self):
        self.is_break = False
        pass

    def after(self):
        self.is_break = False
        # 每天black_day - 1
        keys = []
        for black_stock in self.cls.tmp_black_list.keys():
            self.cls.tmp_black_list[black_stock] -= 1
            if self.cls.tmp_black_list[black_stock] <= 0:
                keys.append(black_stock)

        for key in keys:
            del self.cls.tmp_black_list[key]

        pass

    def __str__(self):
        return '个股止盈止损器'


'''MACD死叉'''


class JPGetMACDDead(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)

    def handle(self, data):
        long_positions = self.platform.get_long_positions(self.cls.pindex)
        if len(long_positions) == 0:
            return
        for stock in long_positions.keys():
            if self.platform.is_macd_dead(stock):
                self.platform.log_info('MACD金叉卖出: {}'.format(stock))
                # 卖出
                self.platform.close_position(self.platform.get_position(stock, pindex=self.cls.pindex))

    def __str__(self):
        return 'MACD金叉卖出'


'''11.10-1.10半仓'''


class JPSetPositions(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)
        self.period = params.get('period', 10)
        self.rate = params.get('rate', 1)
        self.value = params.get('value', 0)
        self.start = params.get('start_date', [11, 15])
        self.end = params.get('end_date', [12, 30])

    def update_params(self, params):
        JPRule.update_params(self, params)
        self.period = params.get('period', 10)
        self.rate = params.get('rate', 1)
        self.value = params.get('value', 0)
        self.start = params.get('start_date', [11, 15])
        self.end = params.get('end_date', [12, 30])

    def handle(self, data):
        # df = self.platform.attribute_history('000001.XSHG', count=20, fields=['close'])
        # is_gold = jp_utils.jp_get_ma_gold(df)
        # if is_gold:
        #     self.cls.position_than = 1.0
        # else:
        #     self.cls.position_than = float(self.value) / self.platform.get_total_money()
        # self.platform.log_info('is_gold: ', is_gold)
        cur_date = self.platform.get_current_date()
        cur_year = cur_date.year
        next_year = cur_year + 1
        start_date = datetime.date(cur_year, self.start[0], self.start[1])
        end_date = datetime.date(next_year, self.end[0], self.end[1])

        # if gr_index
        if start_date < datetime.date(cur_date.year, cur_date.month, cur_date.day) < end_date:
            df = self.platform.attribute_history('000001.XSHG', count=self.period, fields=['close'])
            is_gold = jp_utils.jp_get_ma_gold(df, window=self.period)
            if is_gold is not True:
                # 优先使用设置可用仓位值
                if self.value != 0:
                    self.cls.position_than = float(self.value) / self.platform.get_total_money()
                else:
                    self.cls.position_than = self.rate
            else:
                self.cls.position_than = 1.0
        else:
            self.cls.position_than = 1.0
