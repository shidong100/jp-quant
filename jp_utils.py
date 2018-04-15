# -*- coding:utf-8 -*-

import pandas as pd
import numpy as np
import sys
from prettytable import PrettyTable
from scipy.optimize import leastsq  ##引入最小二乘法


def jp_calc_rate(df, cols=['close'], ascending=True, method='adjacent'):
    '''
    method adjacent、first end
    '''

    for field in cols:
        if ascending is True:
            if method == 'adjacent':
                df[field] = (df[field] - df[field].shift(1)) / df[field].shift(1)
            elif method == 'first':
                df[field] = (df[field] - df.iloc[0][field]) / df.iloc[0][field]
        else:
            if method == 'adjacent':
                df[field] = (df[field] - df[field].shift(-1)) / df[field].shift(-1)
            elif method == 'first':
                df[field] = (df[field] - df.iloc[-1][field]) / df.iloc[-1][field]
    return df


def jp_get_rate(df, field='close', ascending=True):
    '''
    method adjacent、first end
    '''
    if ascending is True:
        return (df.iloc[-1][field] - df.iloc[0][field]) / df.iloc[0][field]
    else:
        return (df.iloc[0][field] - df.iloc[-1][field]) / df.iloc[-1][field]


def jp_calc_slope(x, y, ascending=True):
    # log.info(ascending)
    if ascending:
        return (y[-1] - y[0]) / (x[-1] - x[0])
    else:
        '''倒序'''
        return (y[-1] - y[0]) / (x[0] - x[-1])


def jp_rolling_slope(df, window=3, cols=['000010.XSHG', '399678.XSHE'], ascending=True):
    def func(p, x):
        k, b = p
        return k * x + b

    ##偏差函数：x,y都是列表:这里的x,y更上面的Xi,Yi中是一一对应的
    def error(p, x, y):
        return func(p, x) - y

    # log.info('rolling_fit: \n', df)
    # cols = map(lambda x: x + '_close', cols)
    # cols
    # cols = [str(cols[0]) + '_close', str(cols[1]) + '_close']
    arr = []
    for index in range(len(df) - window + 1):
        item = {}
        pos = window + index
        for col in cols:
            result = leastsq(error, [1, pos], args=(df[index: pos].index, df.iloc[index: pos][col].values))
            k, b = result[0]
            # 画拟合直线
            x = np.linspace(index + 1, pos, window)  ##在0-15直接画100个连续点
            y = k * x + b  ##函数式

            # log.info(col + ':', y)
            item[col] = jp_calc_slope(x, y, ascending=ascending)
            # print(df[index: window + index]['date'])
            try:
                item['date'] = df[index: pos].iloc[-1 if ascending is True else 0]['date']
                # print(str(item['date']) + ':' + str(x) + ':' + str(y))
            except:
                print(str(x) + ':' + str(y))
                pass

                # print(str(df[index: window + index].iloc[-1]['date']) + ' - ' + col + ':', slope(x, y))
        arr.append(item)
    return pd.DataFrame(arr)


def jp_rolling_menu(df, window=5, cols=[], ascending=True):
    df[cols].rolling(window=window).mean()
    pass


def jp_reset_range_index(df, inplace=True):
    import platform
    if int(platform.python_version()[0: 1]) >= 3:
        '''python3'''
        df.set_index(pd.RangeIndex(start=0, stop=len(df)), inplace=inplace)
    else:
        df.set_index(pd.Int64Index(list(range(0, len(df)))), inplace=inplace)


def jp_set_index_suffix(data, method='add'):
    '''
        method add drop
    '''
    if isinstance(data, list) or isinstance(data, np.ndarray):

        if method == 'add':
            return list(map(lambda x: (x + '.XSHG') if x[0] == '6' else (x + '.XSHE'), data))
        elif method == 'drop':
            return list(map(lambda x: x.split('.')[0] if x.find('.') > -1 else x, data))
    elif isinstance(data, pd.DataFrame):
        '''dataframe'''
        # no impl
    pass


def jp_convert_table_show(data, cols=[], index_cols=True):
    def convert_df(df, cols=[], index_cols=True):
        if cols is None or len(cols) == 0:
            cols = list(df.columns.values)
        if len(df.columns.values) != len(cols):
            return PrettyTable(list(df.columns.values))
        if index_cols is True:
            cols.insert(0, 'index')
        table = PrettyTable(cols)

        for index, row in df.iterrows():  # 获取每行的index、row
            item = []
            if index_cols is True:
                item.append(index)

            for col_name in df.columns:
                item.append(row[col_name])

            table.add_row(item)
        return table

    if isinstance(data, list):
        data = pd.DataFrame(data)

    if isinstance(data, pd.DataFrame):
        return convert_df(data, cols=cols, index_cols=index_cols)
    else:
        return PrettyTable(cols)


def jp_convert_to_dict(obj):
    """把Object对象转换成Dict对象"""
    dict = {}
    dict.update(obj.__dict__)
    return dict


def jp_convert_to_dicts(objs):
    """把对象列表转换为字典列表"""
    obj_arr = []
    for o in objs:
        # 把Object对象转换成Dict对象
        dict = {}
        dict.update(o.__dict__)
        obj_arr.append(dict)

    return obj_arr


def jp_get_ma_gold(df, cols='close', window=20):
    tmp_df = pd.rolling_mean(df[[cols]], window)
    # tmp_df = df[[cols]].rolling_mean(window=window)
    if df.iloc[-1][cols] > tmp_df.iloc[-1][cols]:
        return True
    else:
        return False
