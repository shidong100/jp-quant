# -*- coding:utf-8 -*-

from prettytable import PrettyTable

from jp_base import JPRule

# '''------------------持仓信息打印器-----------------'''


class JPShowPositionRecord(JPRule):

    def __init__(self, params):
        JPRule.__init__(self, params)
        self.op_sell_stocks = []
        self.op_buy_stocks = []

    def after(self):
        self.platform.log_info(self.__get_portfolio_info_text(self.cls.op_pindexs))
        self.op_buy_stocks = []
        self.op_buy_stocks = []

    def on_sell_success(self, record):
        self.op_sell_stocks.append([record.security, record.filled])
        pass

    def on_buy_success(self, record):
        self.op_buy_stocks.append([record.security, record.filled])
        pass

    # # 调仓后调用用
    # def after_adjust_end(self,context,data):
    #     print self.__get_portfolio_info_text(context,self.g.op_pindexs)
    #     pass
    # ''' ------------------------------获取持仓信息，普通文本格式------------------------------------------'''
    def __get_portfolio_info_text(self, op_sfs=[0]):
        context = self.platform.context
        sub_str = ''
        table = PrettyTable(["仓号", "股票", "持仓", "当前价", "盈亏", "持仓比"])
        for sf_id in self.cls.stock_pindexs:
            cash = context.subportfolios[sf_id].cash
            p_value = context.subportfolios[sf_id].positions_value
            total_values = p_value + cash
            if sf_id in op_sfs:
                sf_id_str = str(sf_id) + ' *'
            else:
                sf_id_str = str(sf_id)
            new_stocks = [x[0] for x in self.op_buy_stocks]
            for stock in context.subportfolios[sf_id].long_positions.keys():
                position = context.subportfolios[sf_id].long_positions[stock]
                if sf_id in op_sfs and stock in new_stocks:
                    stock_str = self.platform.show_stock(stock) + ' *'
                else:
                    stock_str = self.platform.show_stock(stock)
                stock_raite = (position.total_amount * position.price) / total_values * 100
                table.add_row([sf_id_str,
                               stock_str,
                               position.total_amount,
                               position.price,
                               "%.2f%%" % ((position.price - position.avg_cost) / position.avg_cost * 100),
                               "%.2f%%" % stock_raite]
                              )
            if sf_id < len(self.cls.stock_pindexs) - 1:
                table.add_row(['----', '---------------', '-----', '----', '-----', '-----'])
            sub_str += '[仓号: %d] [总值:%d] [持股数:%d] [仓位:%.2f%%] \n' % (sf_id,
                                                                     total_values,
                                                                     len(context.subportfolios[sf_id].long_positions)
                                                                     , p_value * 100 / (cash + p_value))
        if len(context.portfolio.positions) == 0:
            return '子仓详情:' + sub_str
        else:
            return '子仓详情:' + sub_str + str(table)

    def __str__(self):
        return '持仓信息打印'