# -*- coding:utf-8 -*-

from jp_base import JPRuleGroup
from jp_choose import JPFactor
from jp_choose import JPChooseGroupRule
from jp_choose import JPFilterFinancial
from jp_choose import JPFilterListGroup
from jp_choose import JPFilterListGem
from jp_choose import JPFilterListPaused
from jp_choose import JPFilterListIndex
from jp_choose import JPFilterListRate
from jp_choose import JPFilterListST
from jp_choose import JPFilterListBlackList
from jp_choose import JPFilterListLimit
from jp_choose import JPFilterListUnlock
from jp_choose import JPSortPrice
from jp_choose import JPSortRate
from jp_choose import JPSortSingle
from jp_choose import JPSortType
from jp_choose import JPSortWeightScore
from jp_choose import JPSortWeightIndex
from jp_choose import JPSortTrendUpper
from jp_choose import JPGetMACDGold
from jp_choose import JPChooseMACDGroupRule

from jp_transfer import JPGroupRuleTrans
from jp_transfer import JPTransTime
from jp_transfer import JPTransPeriod
from jp_transfer import JPTransIndexGrowthRate
from jp_transfer import JPTransIndexGrowthRateDiff
from jp_transfer import JPTransPositionIndex
from jp_transfer import JPTransSellStocks
from jp_transfer import JPTransBuyStocks
from jp_transfer import JPTransGainLoss
from jp_transfer import JPGetMACDDead
from jp_transfer import JPSetPositions

from jp_record import JPShowPositionRecord

from jp_stat import JPStat
from jp_sys import JPSysParams
from jp_sys import JPSysMessage
from jp_sys import JPSlippageType

'''
V1.1 版本更新 at 2017.12.09
1. 主要解决买入股票记录数组存的数据不一致问题，导致某种情况下买入不到设置数量的股票
2. 添加大盘2/8行情分化清仓策略

V1.2 版本更新 at 2017.12.14
1. 趋势放量转变

V1.3 bug修复 at 2017.12.16
1. 修复在清仓以后调用on_clear_success()回调，将持仓计数变量清0的bug

V1.4 bug修复 at 2017.12.28
1. 添加MACD金叉买入，MACD死叉买入策略
'''


class JPBaseConfig(object):
    index2 = '000010.XSHG'
    index8 = '399678.XSHE'
    black_list = ['000033.XSHE']
    
    config_time = [
        [True, '调仓时间', JPTransTime, {
            'time': [[14, 50]]  # 调仓时间列表，二维数组，可指定多个时间点
        }]
    ]

    config_common_group = [
        [
            True, '基本操作组合', JPRuleGroup, {
                'config': [
                    [True, '平台设置', JPSysParams, {
                        'level': ['order', 'error']
                        , 'benchmark': index8
                        , 'slippage': {'value': 0.001, 'type': JPSlippageType.percent}
                    }],
                    [True, '发送消息', JPSysMessage, {
                        'is_send_message': False
                    }]
                ]
            }
        ]
    ]

    config_trans_option_group = [
        [
            True, '调仓操作组合', JPGroupRuleTrans, {
                'config': [
                    [True, '卖出股票', JPTransSellStocks, {}]
                    , [True, '卖出股票', JPTransBuyStocks, {}]
                ]
            }
        ]
        , [False, '显示操作记录', JPShowPositionRecord, {}]
        , [True, '统计信息', JPStat, {'is_write': False}]
    ]


class JPConfigSmallMarket(JPBaseConfig):
    pass


class JPConfigSmallMarketTest(JPConfigSmallMarket):
    config_choose = [
        [True, '设置系统参数', JPFilterFinancial, {
            'factors': [
                # JPFactor('valuation.market_cap', min=0, max=100)  # 流通市值0~100亿
                JPFactor('valuation.pe_ratio', min=0, max=150)  # pe > 0
                , JPFactor('indicator.eps', min=0.0)
                , JPFactor('valuation.turnover_ratio', min=1.2)  # 剔除成交量小于1.2的心电图
                # , JPFactor('indicator.inc_net_profit_year_on_year', min=0.0)
                # , JPFactor('indicator.inc_revenue_year_on_year', min=0.0)
            ]
            , 'order_by': 'valuation.circulating_market_cap'  # 按流通市值排序
            , 'sort_type': JPSortType.asc  # 从小到大排序
            , 'limit':100  # 只取前200只
        }],
        [True, '过滤股票', JPFilterListGroup, {
            'config': [
                [True, '过滤创业板', JPFilterListGem, {}]
                , [True, '过滤停牌股', JPFilterListPaused, {}]
                , [True, '过滤涨停板', JPFilterListLimit, {'is_limit_up': True}]
                , [True, '过滤跌停板', JPFilterListLimit, {'is_limit_up': False}]
                , [True, '过滤ST股', JPFilterListST, {}]
                , [True, '过滤黑名单股', JPFilterListBlackList, {'black_list': JPBaseConfig.black_list}]
            ]
        }],
        [True, '权重排序', JPSortWeightScore, {
            'config': [
                [True, '流通市值排序', JPSortSingle,
                 {'sort_type': JPSortType.asc, 'field': 'valuation.circulating_market_cap', 'weight': 100}]
                , [False, '流通市值排序', JPSortSingle,
                   {'sort_type': JPSortType.asc, 'field': 'valuation.circulating_market_cap', 'weight': 0}]
                , [False, '动态市盈率排序', JPSortSingle,
                   {'sort_type': JPSortType.asc, 'field': 'valuation.pe_ratio', 'weight': 10}]
                , [False, '换手率排序', JPSortSingle,
                   {'sort_type': JPSortType.asc, 'field': 'indicator.inc_net_profit_year_on_year', 'weight': 10}]
                , [True, '换手率排序', JPSortSingle,
                   {'sort_type': JPSortType.asc, 'field': 'valuation.turnover_ratio', 'weight': 10}]
                , [True, '当前价格排序', JPSortPrice, {'sort_type': JPSortType.asc, 'field': 'close', 'weight': 20}]
                , [True, '20日涨幅排序', JPSortRate, {'sort_type': JPSortType.asc, 'day': 20, 'weight': 10}]
                , [True, '60日涨幅排序', JPSortRate, {'sort_type': JPSortType.asc, 'day': 60, 'weight': 10}]
                , [False, '120日涨幅排序', JPSortRate, {'sort_type': JPSortType.asc, 'day': 90, 'weight': 10}]
                , [False, '趋势筛选', JPSortTrendUpper,
                   {'sort_type': JPSortType.asc, 'field': 'close', 'weight': 50, 'unit': '5m', 'periods': [5, 10]}]
            ]
            , 'sort_type': JPSortType.asc
        }],
        [False, '趋势筛选', JPSortTrendUpper, {
            'unit': '5m',
            'periods': [5, 10, 15]
        }]
        , [False, '过滤解禁股', JPFilterListUnlock, {'day': 60, 'trading_day': -1, 'dir': 'data/unlock'}]
    ]
    config_trans_condition_group = [[

        True, '调仓组合', JPRuleGroup, {
            'config': [
                [
                    True, '大盘涨幅超过光速', JPTransPositionIndex, {
                        'index': '000001.XSHG'  # 上证指数
                        , 'period': 130
                        , 'multiple': 1.8
                    }
                ]
                , [
                    True, '大盘进入即将空头', JPTransIndexGrowthRate, {
                        'index': [JPBaseConfig.index2, JPBaseConfig.index8]
                        , 'min_rate': [0.6, 0.6]
                        , 'period': 30
                        , 'smart': False
                    }
                ]
                , [
                    False, '大盘2/8分化严重', JPTransIndexGrowthRateDiff, {
                        'index': ['000016.XSHG', JPBaseConfig.index8]
                        , 'period': 3
                    }
                ]
                , [False, '个股止盈止损器', JPTransGainLoss, {
                        'black_day': 10,
                        'loss_rate': 0
                    }
                ]
                , [
                    True, '调仓周期N天一次', JPTransPeriod, {
                        'period': 3
                    }
                ]
                , [
                    True, '控制仓位资金', JPSetPositions, {
                        'period': 10,
                        'rate': 0.5,
                        'start_date': [11, 15],
                        'end_date': [12, 30]
                    }
                ]
            ]
        }
    ]]

    config_choose_group = [
        [

            True, '选股组合', JPChooseGroupRule, {
                'config': config_choose
                , 'buy_num': 2
                , 'sort_num': 10
                , 'day_run_one': True
            }
        ]
    ]
    config_all_group = JPBaseConfig.config_common_group + JPBaseConfig.config_time + config_trans_condition_group + config_choose_group + JPBaseConfig.config_trans_option_group
    pass


class JPConfigMACDTest(JPBaseConfig):
    config_choose = [
        [True, '设置系统参数', JPFilterFinancial, {
            'factors': [
                # JPFactor('valuation.market_cap', min=0, max=100)  # 流通市值0~100亿
                JPFactor('valuation.pe_ratio', min=0, max=200)  # pe > 0
                # , JPFactor('indicator.eps', min=0.0)
                # , JPFactor('valuation.turnover_ratio', min=1.2)  # 剔除成交量小于1.2的心电图
                # , JPFactor('indicator.inc_net_profit_year_on_year', min=0.0)
                # , JPFactor('indicator.inc_revenue_year_on_year', min=0.0)
            ]
            , 'order_by': 'valuation.circulating_market_cap'  # 按流通市值排序
            , 'sort_type': JPSortType.asc  # 从小到大排序
            , 'limit':100  # 只取前200只
        }],
        [False, '过滤股票', JPFilterListGroup, {
            'config': [
                [True, '过滤创业板', JPFilterListGem, {}]
                , [True, '过滤停牌股', JPFilterListPaused, {}]
                , [True, '过滤涨停板', JPFilterListLimit, {'is_limit_up': True}]
                , [True, '过滤跌停板', JPFilterListLimit, {'is_limit_up': False}]
                , [True, '过滤ST股', JPFilterListST, {}]
                , [True, '过滤黑名单股', JPFilterListBlackList, {'black_list': JPBaseConfig.black_list}]
            ]
        }],
        [True, 'MACD金叉', JPGetMACDGold, {}],
        [True, '权重排序', JPSortWeightScore, {
            'config': [
                [True, '流通市值排序', JPSortSingle,
                 {'sort_type': JPSortType.asc, 'field': 'valuation.circulating_market_cap', 'weight': 100}]
                , [False, '流通市值排序', JPSortSingle,
                   {'sort_type': JPSortType.asc, 'field': 'valuation.circulating_market_cap', 'weight': 0}]
                , [False, '动态市盈率排序', JPSortSingle,
                   {'sort_type': JPSortType.asc, 'field': 'valuation.pe_ratio', 'weight': 10}]
                , [False, '换手率排序', JPSortSingle,
                   {'sort_type': JPSortType.asc, 'field': 'indicator.inc_net_profit_year_on_year', 'weight': 10}]
                , [True, '换手率排序', JPSortSingle,
                   {'sort_type': JPSortType.asc, 'field': 'valuation.turnover_ratio', 'weight': 10}]
                , [True, '当前价格排序', JPSortPrice, {'sort_type': JPSortType.asc, 'field': 'close', 'weight': 20}]
                , [True, '20日涨幅排序', JPSortRate, {'sort_type': JPSortType.asc, 'day': 20, 'weight': 10}]
                , [True, '60日涨幅排序', JPSortRate, {'sort_type': JPSortType.asc, 'day': 60, 'weight': 10}]
                , [False, '趋势筛选', JPSortTrendUpper,
                   {'sort_type': JPSortType.asc, 'field': 'close', 'weight': 50, 'unit': '5m', 'periods': [5, 10]}]
            ]
            , 'sort_type': JPSortType.asc
        }],
        [False, '趋势筛选', JPSortTrendUpper, {
            'unit': '5m',
            'periods': [5, 10, 15]
        }]
        , [False, '过滤解禁股', JPFilterListUnlock, {'day': 60, 'trading_day': -1, 'dir': 'data/unlock'}]
    ]
    config_trans_condition_group = [[

        True, '调仓组合', JPRuleGroup, {
            'config': [
                [
                    True, '大盘涨幅超过光速', JPTransPositionIndex, {
                        'index': '000001.XSHG'  # 上证指数
                        , 'period': 130
                        , 'multiple': 1.8
                    }
                ]
                , [
                    True, '大盘进入即将空头', JPTransIndexGrowthRate, {
                        'index': [JPBaseConfig.index2, JPBaseConfig.index8]
                        , 'min_rate': [0.6, 0.6]
                        , 'period': 30
                    }
                ]
                , [
                    False, '大盘2/8分化严重', JPTransIndexGrowthRateDiff, {
                        'index': ['000016.XSHG', JPBaseConfig.index8]
                        , 'period': 3
                    }
                ]
                , [False, '个股止盈止损器', JPTransGainLoss, {
                        'black_day': 10,
                        'loss_rate': 0
                    }
                ]
                , [True, 'MACD死叉', JPGetMACDDead, {}]
                , [
                    False, '调仓周期N天一次', JPTransPeriod, {
                        'period': 3
                    }
                ]
            ]
        }
    ]]

    config_choose_group = [
        [

            True, '选股组合', JPChooseMACDGroupRule, {
                'config': config_choose
                , 'buy_num': 2
                , 'sort_num': 10
                , 'day_run_one': True
            }
        ]
    ]
    config_all_group = JPBaseConfig.config_common_group + JPBaseConfig.config_time + config_trans_condition_group + config_choose_group + JPBaseConfig.config_trans_option_group
    pass