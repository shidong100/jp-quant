# -*- coding:utf-8 -*-

from jp_base import JPBase
from jp_base import JPRule
from jp_base import JPRuleGroup
from jp_base import JPSortType

import jp_utils

import pandas as pd
import datetime


class JPFactor(JPBase):
    def __init__(self, factor, **kwargs):
        self.factor = factor
        self.min = kwargs.get('min', None)
        self.max = kwargs.get('max', None)


class JPChooseGroupRule(JPRuleGroup):
    cols = ['date', 'code name', 'market', 'circulating_market', 'turnover_ratio', 'pe_ratio', 'eps', 'close', 'rate20',
            'rate60', 'score']

    # cols = ['日期', '股票代码', '总市值', '流通市值', '成交量', '市盈率', '市净率', '当前价格', '20日涨幅', '60日涨幅', '总分数']

    def __init__(self, params):
        JPRuleGroup.__init__(self, params)
        self.sort_num = params.get('sort_num', 10)
        self.day_run_one = params.get('day_run_one', False)
        self.buy_num = params.get('buy_num', 3)
        self.has_run = False

    def update_params(self, params):
        self.sort_num = params.get('sort_num', 10)
        self.day_run_one = params.get('day_run_one', False)
        self.buy_num = params.get('buy_num', 3)
        self.has_run = False
        pass

    def handle(self, data):
        if self.day_run_one and self.has_run:
            return
        self.cls.buy_num = self.buy_num
        all_list = []
        '''条件查询股票'''
        for rule in self.rules:
            if isinstance(rule, JPFilterQuery):
                all_list.append(self.platform.get_fundamentals_data(rule._params))

        all_data = pd.concat(all_list)
        if all_data is None or len(all_data) == 0:
            self.has_run = True
            return

        filter_list = all_data['code'].values

        '''查询后的进行剔除'''
        for rule in self.rules:
            if isinstance(rule, JPFilterListGroup):
                filter_list = rule.filter(data, filter_list)

        all_data = all_data[all_data['code'].isin(filter_list)]
        # self.platform.log_info('filter after: %d\n %s' % (len(all_data), str(all_data)))
        if all_data is None or len(all_data) == 0:
            self.has_run = True
            return

        '''股票池做权重排序'''
        for rule in self.rules:
            if isinstance(rule, JPSortBaseGroup):
                params, all_data = rule.sort(data, all_data)

        all_data = all_data[0: self.sort_num] if len(all_data) >= 0 else all_data
        filter_list = all_data['code'].values
        '''筛选过后的最后10只股票做最终的打分'''
        for rule in self.rules:
            if isinstance(rule, JPFilterListUnlock):
                filter_list = rule.filter(data, filter_list)

        # 赛选完毕 进行数据处理
        filter_list = filter_list[:]
        if self.cls.is_send_message:
            # 将选出在股发送到微信
            message = ''
            for stock in filter_list:
                message += (self.platform.show_stock(stock) + '\n')
            self.platform.send_message_(message)

        all_data = all_data[all_data['code'].isin(filter_list)]
        '''筛选过后的最后10只股票做最终的打分'''
        '''
        for rule in self.rules:
            if isinstance(rule, JPSortTrendUpper):
                all_data = rule.sort(data, all_data)
        '''

        all_data['stock_code'] = all_data['code']
        all_data['code'] = all_data['code'].apply(lambda x: self.platform.show_stock(x))
        show_stock_list = all_data.drop('stock_code', 1).applymap(lambda x: round(x, 3) if isinstance(x, float) else x)
        self.platform.log_info('选出排行前{0}的股票信息:\n'.format(self.sort_num),
                               jp_utils.jp_convert_table_show(show_stock_list, index_cols=False))

        self.cls.buy_stocks = all_data[0: self.buy_num]['stock_code'].values if len(all_data) >= self.buy_num else \
            all_data[:]['stock_code'].values
        # 将选出在股发送到微信
        message = '最终选出的股票: ['
        for index, stock in enumerate(self.cls.buy_stocks):
            if index == len(self.cls.buy_stocks) - 1:
                # 最后一个
                message += (self.platform.show_stock(stock))
            else:
                message += (self.platform.show_stock(stock) + '  |  ')
        message += ']'
        self.platform.log_info(message)
        self.has_run = True

    def before(self):
        self.has_run = False


class JPFilterQuery(JPRule):
    def filter(self, data, q):
        return None


class JPFilterList(JPRule):
    def filter(self, data, stock_list):
        return None


class JPFilterFinancial(JPFilterQuery):
    def __init__(self, params):
        JPRule.__init__(self, params)
        pass

    def filter(self, data, q):
        return self.platform.get_financial_data(self._params)

    def handle(self, data):
        return self.platform.get_financial_data(self._params)


'''=================选出的股票做过滤======================'''


class JPFilterListGroup(JPRuleGroup):
    def __init__(self, params):
        JPRuleGroup.__init__(self, params)

    def filter(self, data, stock_list):
        for rule in self.rules:
            stock_list = rule.filter(data, stock_list)
        return stock_list


# add at 2017/12/14 V1.02


class JPFilterListUnlock(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)
        self.day = params.get('day', -1)  # 默认两个月
        self.trading_day = params.get('trading_day', 44)  # 默认两个月
        self.dir = params.get('dir')
        self.percentage = params.get('percentage', 10)
        pass

    def update_params(self, params):
        JPRule.update_params(self, params)
        self.day = params.get('day', 60)  # 默认两个月
        self.trading_day = params.get('trading_day', 44)  # 默认两个月
        self.dir = params.get('dir', None)
        self.percentage = params.get('percentage', 10)
        pass

    def filter(self, data, stock_list):
        if self.platform.is_py3():
            from io import StringIO
        else:
            from StringIO import StringIO

        year = self.platform.get_current_date().year
        fs = (self.dir + '/' + str(year) + '.csv') if self.dir is not None else (str(year) + '.csv')
        df = self.platform.read_file_(fs)
        if isinstance(df, str):
            df = pd.read_csv(StringIO(df), sep=',', index_col=0, dtype={'code': str})
            df['date'] = pd.to_datetime(df['date'])
        real_day = self.day
        drop_arr = []
        if real_day != -1:
            dt = self.platform.get_current_date()
            dd = datetime.date(dt.year, dt.month, dt.day) + datetime.timedelta(days=real_day)
            self.platform.log_info('real_day: ', real_day)
            self.platform.log_info('date: ', dd)
            df = df[(df['proportion'] > 15) & (df['date'] < dd) & (df['date'] > self.platform.get_current_date())]
            drop_arr = df['code'].drop_duplicates().values
        drop_arr = jp_utils.jp_set_index_suffix(drop_arr)
        self.platform.log_info('近期解禁股: \n', list(set(stock_list).intersection(set(drop_arr))))
        new_list = [stock for stock in stock_list if stock not in drop_arr]
        return new_list

    def __str__(self):
        return '近期%d日将解禁的股' % self.n


class JPFilterListTrading(JPFilterList):
    def __init__(self, params):
        JPFilterList.__init__(self, params)
        self.n = params.get('day')
        pass

    def update_params(self, params):
        JPFilterList.update_params(self, params)
        self.n = params.get('day')
        pass

    def filter(self, data, stock_list):
        return [stock for stock in stock_list if self.platform.get_trading_days(stock, self.n)]

    def __str__(self):
        return '过滤交易日不超过%d日的股票' % self.n


class JPFilterListRate(JPFilterList):
    def __init__(self, params):
        JPRule.__init__(self, params)
        self.n = params.get('day')
        self.p = params.get('rate')
        pass

    def update_params(self, params):
        JPFilterList.update_params(self, params)
        self.n = params.get('day')
        self.p = params.get('rate')
        pass

    def filter(self, data, stock_list):
        return [stock for stock in stock_list if self.platform.get_growth_rate(stock, self.n) < self.p]

    def __str__(self):
        return '过滤%d涨幅不超过%d的股票' % (self.n, self.p)


class JPFilterListGem(JPFilterList):
    def __init__(self, params):
        JPRule.__init__(self, params)
        pass

    def filter(self, data, stock_list):
        return [stock for stock in stock_list if stock[0:3] != '300']

    def __str__(self):
        return '过滤创业板股票'


class JPFilterListIndex(JPFilterList):
    def __init__(self, params):
        JPFilterList.__init__(self, params)
        self.index = params.get('index', '300')
        if len(self.index) > 3:
            self.index = self.index[0: 3]

    def update_params(self, params):
        JPFilterList.update_params(self, params)
        self.index = params.get('index', '300')
        if len(self.index) > 3:
            self.index = self.index[0: 3]
        pass

    def filter(self, data, stock_list):
        return [stock for stock in stock_list if stock[0:3] != self.index]

    def __str__(self):
        return '过滤创业板股票'


class JPFilterListPaused(JPFilterList):
    def filter(self, data, stock_list):
        current_data = self.platform.get_current_data()
        return [stock for stock in stock_list if not current_data[stock].paused]

    def __str__(self):
        return '过滤停牌股票'


class JPFilterListLimit(JPFilterList):
    def __init__(self, params):
        JPRule.__init__(self, params)
        self.is_limit_up = params.get('is_limit_up', True)
        pass

    def update_params(self, params):
        JPRule.update_params(self, params)
        self.is_limit_up = params.get('is_limit_up', True)
        pass

    def filter(self, data, stock_list):
        threshold = 1.00
        if self.is_limit_up:
            return [stock for stock in stock_list if stock in self.context.portfolio.positions.keys()
                    or data[stock].close < data[stock].high_limit * threshold]
        else:
            return [stock for stock in stock_list if stock in self.context.portfolio.positions.keys()
                    or data[stock].close > data[stock].low_limit * threshold]

    def __str__(self):
        if self.is_limit_up:
            return '过滤涨停股票'
        else:
            return '过滤跌停股票'


class JPFilterListST(JPFilterList):
    def filter(self, data, stock_list):
        current_data = self.platform.get_current_data()
        return [stock for stock in stock_list
                if not current_data[stock].is_st
                and 'ST' not in current_data[stock].name
                and '*' not in current_data[stock].name
                and '退' not in current_data[stock].name]

    def __str__(self):
        return '过滤ST股票'


class JPFilterListBlackList(JPFilterList):
    def __init__(self, params):
        JPFilterList.__init__(self, params)
        self.black_list = params.get('black_list', [])

    def update_params(self, params):
        JPFilterList.__init__(self, params)
        self.black_list = params.get('black_list', [])

    def filter(self, data, stock_list):
        new_black_list = self.black_list[:] + list(self.cls.tmp_black_list.keys())
        return [stock for stock in stock_list if stock not in new_black_list]

    def __str__(self):
        return '过滤黑名单股票'


'''======================排序===================='''


class JPSortBase(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)
        pass

    def sort(self, data, stock_list):
        pass


class JPSortWeightBase(JPSortBase):
    def __init__(self, params):
        JPSortBase.__init__(self, params)
        self.field = params.get('field', None)
        self.weight = params.get('weight', 10)
        self.is_asc = params.get('sort_type', JPSortType.asc) == JPSortType.asc
        pass

    def update_params(self, params):
        JPSortBase.update_params(self, params)
        self.field = params.get('field', None)
        self.weight = params.get('weight', 10)
        self.is_asc = params.get('sort_type', JPSortType.asc) == JPSortType.asc
        pass

    def _sort_type_str_(self):
        return '从小到大' if self.is_asc else '从大到小'


class JPSortRate(JPSortWeightBase):
    def __init__(self, params):
        JPSortWeightBase.__init__(self, params)
        self.day = params.get('day')
        self.field = str('rate') + str(self.day)
        pass

    def update_params(self, params):
        JPSortWeightBase.update_params(self, params)
        self.day = params.get('day')
        self.field = str('rate') + str(self.day)
        pass

    def sort(self, data, stock_list):
        stock_list[self.field] = stock_list['code'].apply(
            lambda x: self.platform.get_growth_rate(x, self.day))
        new_params = self._params.copy()
        del new_params['day']
        new_params['field'] = self.field
        
        return new_params, stock_list


class JPSortSingle(JPSortWeightBase):
    def __init__(self, params):
        JPSortWeightBase.__init__(self, params)
        pass

    def sort(self, data, stock_list):
        new_params = self._params.copy()
        new_params['field'] = self.field.replace('valuation.', '')
        return new_params, stock_list


class JPSortPrice(JPSortWeightBase):
    def __init__(self, params):
        JPSortWeightBase.__init__(self, params)
        pass

    def sort(self, data, stock_list):
        stock_list[self.field] = stock_list['code'].apply(
            lambda x: data[x].close)
        new_params = self._params.copy()
        return new_params, stock_list


class JPSortBaseGroup(JPRuleGroup):
    def __init__(self, params):
        JPRuleGroup.__init__(self, params)
        self.is_asc = params.get('sort_type', JPSortType.asc) == JPSortType.asc
        self.weight = {}
        pass

    def update_params(self, params):
        JPRuleGroup.update_params(self, params)
        self.is_asc = params.get('sort_type', JPSortType.asc) == JPSortType.asc
        self.weight = {}
        pass

    def sort(self, data, stock_list):
        self.handle_weight()
        for i, row in stock_list.iterrows():
            score = 0
            for key in self.weight:
                try:
                    score += row[key] * self.weight[key]
                except KeyError:
                    self.platform.log_info('没有该字段')
                    score = 0
            stock_list.at[i, 'score'] = score
        return None, stock_list.sort_values('score',
                                            ascending=self.is_asc) if self.platform.is_py3() else stock_list.sort(
            'score',
            ascending=self.is_asc)

    def handle_weight(self):
        total_weight = sum(self.weight.values())
        for key in self.weight:
            self.weight[key] = round(float(self.weight[key]) / total_weight, 2)
        pass


class JPSortWeightScore(JPSortBaseGroup):
    def sort(self, data, stock_list):
        for rule in self.rules:
            param, stock_list = rule.sort(data, stock_list)
            self.weight[param['field']] = param['weight']
        return JPSortBaseGroup.sort(self, data, stock_list)

    def handle(self, data, stock_list):
        return self.sort(data, stock_list)


class JPSortWeightIndex(JPSortBaseGroup):
    def sort(self, data, stock_list):
        for rule in self.rules:
            param, stock_list = rule.sort(data, stock_list)
            field = param['field']
            self.weight[field] = param['weight']
            '''按分数从小到大排序'''
            new_list = stock_list.sort_values(field,
                                              ascending=rule.is_asc) if self.platform.is_py3() else stock_list.sort(
                field, ascending=rule.is_asc)
            new_list['row'] = range(len(new_list))
            stock_list[field] = (new_list['row'] + 1)
        return JPSortBaseGroup.sort(self, data, stock_list)


'''放量多头趋势'''


class JPSortTrendUpper(JPSortWeightBase):
    def __init__(self, params):
        JPSortBase.__init__(self, params)
        self.unit = params.get('unit', '1d')
        self.periods = params.get('periods', [5, 10])

    def update_params(self, params):
        self.unit = params.get('unit', '1d')
        self.periods = params.get('periods', [5, 10])

    def sort(self, data, stock_list):
        day = max(self.periods) + 5
        # self.platform.log_info('stock_list: \n', stock_list)
        fields = ['close', 'volume']
        filter_stock = []
        stock_list['trend_val'] = 10
        for stock in stock_list['code']:
            df = self.platform.attribute_history(stock, day, unit=self.unit, fields=fields)
            for col in self.periods:
                ma = df[fields].rolling_mean(window=col) if self.platform.is_py3() else pd.rolling_mean(df[fields],
                                                                                                        window=col)
                for f in fields:
                    ma.rename(columns={f: 'MA' + f + str(col)}, inplace=True)
                df = df.join(ma)

            df['date'] = df.index
            df['code'] = stock
            jp_utils.jp_reset_range_index(df)
            df = df.dropna()
            # self.platform.log_info('dataframe: \n', df)
            # 5日均成交量 > 10日均成交量
            temp_flag = []
            for f in fields:
                for index in range(len(self.periods) - 1):
                    field0 = 'MA' + f + str(self.periods[index])
                    field1 = 'MA' + f + str(self.periods[index + 1])
                    flag = df.iloc[-1][field0] > df.iloc[-1][field1]
                    temp_flag.append(flag)
                    self.platform.log_info(field0 + '-' + field1 + '：' + str(flag))
            # self.platform.log_info('temp_flag: ', temp_flag)
            if sum(temp_flag) == len(fields) * (len(self.periods) - 1):
                filter_stock.append(stock)
                self.platform.log_info('code:', self.platform.get_security_info(stock))
        stock_list.loc[stock_list['code'].isin(filter_stock), 'trend_val'] = stock_list['trend_val'] / 2
        new_params = self._params.copy()
        new_params['field'] = 'trend_val'
        return new_params, stock_list


class JPChooseMACDGroupRule(JPRuleGroup):
    def __init__(self, params):
        JPRuleGroup.__init__(self, params)
        self.sort_num = params.get('sort_num', 10)
        self.day_run_one = params.get('day_run_one', False)
        self.buy_num = params.get('buy_num', 3)
        self.has_run = False

    def update_params(self, params):
        self.sort_num = params.get('sort_num', 10)
        self.day_run_one = params.get('day_run_one', False)
        self.buy_num = params.get('buy_num', 3)
        self.has_run = False
        pass

    def handle(self, data):
        if self.day_run_one and self.has_run:
            return
        self.cls.buy_num = self.buy_num
        all_list = []
        '''条件查询股票'''
        for rule in self.rules:
            if isinstance(rule, JPFilterQuery):
                all_list.append(self.platform.get_fundamentals_data(rule._params))

        all_data = pd.concat(all_list)
        if all_data is None or len(all_data) == 0:
            self.has_run = True
            return

        filter_list = all_data['code'].values

        '''查询后的进行剔除'''
        for rule in self.rules:
            if isinstance(rule, JPFilterListGroup):
                filter_list = rule.filter(data, filter_list)

        for rule in self.rules:
            if isinstance(rule, JPGetMACDGold):
                filter_list = rule.filter(data, filter_list)

        self.platform.log_info('macd : %d\n %s' % (len(filter_list), str(filter_list)))

        all_data = all_data[all_data['code'].isin(filter_list)]
        if all_data is None or len(all_data) == 0:
            self.has_run = True
            return

        '''股票池做权重排序'''
        for rule in self.rules:
            if isinstance(rule, JPSortBaseGroup):
                params, all_data = rule.sort(data, all_data)

        all_data = all_data[0: self.sort_num] if len(all_data) >= 0 else all_data
        show_stock_list = all_data.applymap(lambda x: round(x, 3) if isinstance(x, float) else x)
        self.platform.log_info('选出排行前{0}的股票信息:\n'.format(self.sort_num),
                               jp_utils.jp_convert_table_show(show_stock_list))
        filter_list = all_data['code'].values
        '''筛选过后的最后10只股票做最终的打分'''
        for rule in self.rules:
            if isinstance(rule, JPFilterListUnlock):
                filter_list = rule.filter(data, filter_list)
        all_data = all_data[all_data['code'].isin(filter_list)]
        '''筛选过后的最后10只股票做最终的打分'''
        '''
        for rule in self.rules:
            if isinstance(rule, JPSortTrendUpper):
                all_data = rule.sort(data, all_data)
        '''
        self.cls.buy_stocks = all_data[0: self.buy_num]['code'].values if len(all_data) >= self.buy_num else \
            all_data[:]['code'].values
        self.platform.log_info('最终选出的股票: %s ' % str(self.cls.buy_stocks))
        self.has_run = True

    def before(self):
        self.has_run = False


class JPMACDBase(JPRule):
    def __init__(self, params):
        JPRule.__init__(self, params)

    def filter(self, data, stock_list):
        pass


class JPGetMACDGold(JPMACDBase):
    def __init__(self, params):
        JPMACDBase.__init__(self, params)

    def filter(self, data, stock_list):
        return [stock for stock in stock_list if self.platform.is_macd_gold(stock)]

    def __str__(self):
        return 'MACD金叉买入'
