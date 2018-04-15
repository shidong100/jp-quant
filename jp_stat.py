# -*- coding:utf-8 -*-

import pandas as pd

pd.set_option('display.height', 1000)
pd.set_option('display.max_rows', 100000)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 1000)

import json
from jp_base import JPRule
from jp_base import JPUserEncoder
from jp_base import JPRunType

from prettytable import PrettyTable


# ''' ----------------------统计类----------------------------'''
class JPStat(JPRule):

    def __init__(self, params):
        JPRule.__init__(self, params)
        self.reset_params(params)

    def update_params(self, params):
        JPRule.update_params(self, params)
        self.reset_params(params)

    def reset_params(self, params):
        self.is_write_data = params.get('is_write', False)
        # 加载统计模块
        self.last_profit = 0.0
        self.max_draw_down = 0.0
        self.trade_total_count = 0
        self.trade_success_count = 0
        self.one_stock = {}  # 统计每个股票的操作数据
        self.stats = {'win': [], 'loss': []}  # 统计盈利和亏损数据
        self.table = []
        self.op_buy_stocks = []
        self.op_sell_stocks = []

    def after(self):
        self.stat_max_draw_down()
        self.print_win_rate()
        self.print_portfolio_info()
        run_type = self.platform.get_run_type()
        if len(self.cls.config_json) == 0:
            return
        if self.platform.get_current_date().strftime("%Y-%m-%d") == str(
                    self.platform.get_end_date()):
            if run_type == JPRunType.simple or run_type == JPRunType.run:
                if self.is_write_data:
                    self.platform.write_file_('/data/test/strategy.txt',
                                              json.dumps(self.cls.config_json, ensure_ascii=False, cls=JPUserEncoder),
                                              True)
                    self.platform.write_file_('/data/test/record/' + self.cls.config_json['sid'] + '.txt',
                                              json.dumps(self.cls.trade_record, ensure_ascii=False, cls=JPUserEncoder),
                                              False)
                    self.platform.write_file_('/data/test/score/' + self.cls.config_json['sid'] + '.txt',
                                              json.dumps(self.table, ensure_ascii=False, cls=JPUserEncoder),
                                              False)
                    self.platform.log_info('-----------------已写入文件成功-----------------')
                else:
                    self.platform.log_info(pd.DataFrame(self.table))
                    self.platform.log_info(pd.DataFrame(self.cls.trade_record))

                self.platform.log_info('--------------------回测结束--------------------')
            else:
                pass
                # 模拟或实盘
                # self.platform.write_file_('/data/trade/record/record.txt', json.dumps(self.table, ensure_ascii=False, cls=JPUserEncoder), False)

        pass

    def on_sell_success(self, record):
        if record.filled > 0:
            self.op_sell_stocks.append([record.security, record.filled])
            # 只要有成交，无论全部成交还是部分成交，则统计盈亏
            percent = self.watch(record.security, record.filled, record.avg_cost, record.price)
            try:
                record_dict = self.one_stock[record.security]
                record_dict['status'] = 2
                record_dict['rate'] = percent
                record_dict['end_date'] = self.platform.get_current_date().strftime("%Y-%m-%d")
            except Exception as e:
                self.platform.log_info(self.one_stock)
                self.platform.log_error('记录出错: {0}'.format(record.security))

    def on_buy_success(self, record):
        if record.filled > 0:
            self.op_buy_stocks.append([record.security, record.filled])
            self.one_stock[record.security] = {
                'code': record.security,
                'status': 1,
                'day': 0,
                'start_date': self.platform.get_current_date().strftime("%Y-%m-%d")
            }
        pass

    # 记录交易次数便于统计胜率
    # 卖出成功后针对卖出的量进行盈亏统计
    def watch(self, stock, sold_amount, avg_cost, cur_price):
        self.trade_total_count += 1
        current_value = sold_amount * cur_price
        cost = sold_amount * avg_cost
        percent = round((current_value - cost) / cost * 100, 2)
        if current_value > cost:
            self.trade_success_count += 1
            self.stats['win'].append([stock, percent])
        else:
            self.stats['loss'].append([stock, percent])
        return percent

    def report(self):
        context = self.context
        cash = context.portfolio.cash
        total_value = context.portfolio.portfolio_value
        position = 1 - cash / total_value
        self.platform.log_info("收盘后持仓概况:%s" % str(list(context.portfolio.positions)))
        self.platform.log_info("仓位概况:%.2f" % position)
        self.platform.print_win_rate(self.platform.get_current_data().strftime("%Y-%m-%d"),
                                     self.platform.get_current_date().strftime("%Y-%m-%d"))

    # 打印胜率
    def print_win_rate(self):
        keys = []
        for stock, val in self.one_stock.items():
            status = val['status']
            if status == 1:
                val['day'] += 1
            elif status == 2:
                keys.append(stock)

        for key in keys:
            self.cls.trade_record.append(self.one_stock.pop(key))

        context = self.context
        win_rate = 0
        if 0 < self.trade_total_count and 0 < self.trade_success_count:
            win_rate = round(self.trade_success_count / float(self.trade_total_count), 3)

        most_win = self.stat_most_win_percent()
        most_loss = self.stat_most_loss_percent()
        starting_cash = context.portfolio.starting_cash
        total_profit = self.stat_total_profit()
        if len(most_win) == 0 or len(most_loss) == 0:
            return

        record = {
            'date': self.platform.get_current_date(),  # 交易总次数
            'total_count': self.trade_total_count,  # 交易总次数
            'success_count': self.trade_success_count,  # 交易成功次数
            'success_rate': win_rate,  # 胜率
            'win_most': most_win['stock'],  # 单次最大盈利
            'win_most_rate': most_win['value'],  # 单次最大盈利
            'loss_most': most_loss['stock'],  # 单次最大亏损
            'loss_most_rate': most_loss['value'],  # 单次最大亏损
            'total_cash': starting_cash + total_profit,  # 总资产
            'start_cash': starting_cash,  # 本金资产
            'profit_cash': total_profit,  # 盈利资产
            'profit_rate': total_profit / starting_cash,  # 盈利比
            'draw_down': self.max_draw_down
        }
        self.table.append(record)

        # 保存到文件
        s = '\n----------------------------绩效报表----------------------------'
        s += '\n交易次数: {0}, 盈利次数: {1}, 胜率: {2}'.format(record['total_count'], record['success_count'],
                                                      str(record['success_rate'] * 100) + str('%'))
        s += '\n单次盈利最高: {0}, 盈利比例: {1}%'.format(record['win_most'], record['win_most_rate'])
        s += '\n单次亏损最高: {0}, 亏损比例: {1}%'.format(record['loss_most'], record['loss_most_rate'])
        s += '\n总资产: {0}, 本金: {1}, 盈利: {2}, 盈亏比率：{3}%'.format(record['total_cash'], record['start_cash'],
                                                              record['profit_cash'], (record['profit_rate']) * 100)
        s += '\n最大回撤:{0}%'.format(round(record['draw_down'], 2))
        s += '\n---------------------------------------------------------------'
        self.platform.log_info(s)

    def stat_max_draw_down(self):
        context = self.context
        current_profit = context.portfolio.portfolio_value
        # 计算最大回撤
        if self.last_profit != 0 and current_profit < self.last_profit:
            current_draw_down = (self.last_profit - current_profit) * 100 / self.last_profit
            if current_draw_down > self.max_draw_down:
                self.max_draw_down = current_draw_down
        if self.last_profit == 0 or current_profit > self.last_profit:
            self.last_profit = current_profit

    # 统计单次盈利最高的股票
    def stat_most_win_percent(self):
        result = {}
        if len(self.stats['win']) > 0:
            temp = sorted(self.stats['win'], key=lambda x: x[1], reverse=True)[0]
            result['stock'] = temp[0]
            result['value'] = temp[1]
        return result

    # 统计单次亏损最高的股票
    def stat_most_loss_percent(self):
        result = {}
        if len(self.stats['loss']) > 0:
            temp = sorted(self.stats['loss'], key=lambda x: x[1], reverse=False)[0]
            result['stock'] = temp[0]
            result['value'] = temp[1]
        return result

    # 统计总盈利金额
    def stat_total_profit(self):
        return self.context.portfolio.portfolio_value - self.context.portfolio.starting_cash

    def print_portfolio_info(self):
        sub_str = ''
        table = PrettyTable(["仓号", "股票", "持仓", "当前价", "盈亏", "持仓比"])
        pindex = self.cls.pindex
        cash = self.platform.get_position_cash(pindex)
        p_value = self.platform.get_position_value(pindex)
        total_values = p_value + cash
        sf_id_str = str(pindex)
        new_stocks = [x[0] for x in self.op_buy_stocks]
        for stock, position in self.platform.get_long_positions(pindex).items():
            if stock in new_stocks:
                stock_str = self.platform.show_stock(stock) + ' *'
            else:
                stock_str = self.platform.show_stock(stock)
            stock_rate = (position.total_amount * position.price) / total_values * 100
            table.add_row([sf_id_str,
                           stock_str,
                           position.total_amount,
                           position.price,
                           "%.2f%%" % ((position.price - position.avg_cost) / position.avg_cost * 100),
                           "%.2f%%" % stock_rate]
                          )
        if pindex < len(self.cls.stock_pindexs) - 1:
            table.add_row(['----', '---------------', '-----', '----', '-----', '-----'])
        sub_str += '[仓号: %d] [总值:%d] [持股数:%d] [仓位:%.2f%%] \n' % (pindex,
                                                                 total_values,
                                                                 len(self.platform.get_long_positions(pindex))
                                                                 , p_value * 100 / (cash + p_value))
        if len(self.platform.get_long_positions(pindex)) == 0:
            self.platform.log_info('子仓详情{0}'.format(sub_str))
        else:
            self.platform.log_info('子仓详情{0}{1}'.format(sub_str, str(table)))
        self.op_buy_stocks = []
        self.op_sell_stocks = []
        
    def __str__(self):
        return '策略绩效统计'

        # 订单是否相同 (以代码与日期def is_same_order(self, code, date):
        #     current = self.one_stock[]
        #     if self['code'] == code and self同时相等为条件)
        #
