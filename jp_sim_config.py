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

from jp_transfer import JPGroupRuleTrans
from jp_transfer import JPTransTime
from jp_transfer import JPTransPeriod
from jp_transfer import JPTransIndexGrowthRate
from jp_transfer import JPTransIndexGrowthRateDiff
from jp_transfer import JPTransPositionIndex
from jp_transfer import JPTransSellStocks
from jp_transfer import JPTransBuyStocks
from jp_transfer import JPTransGainLoss
from jp_transfer import JPSetPositions

from jp_record import JPShowPositionRecord

from jp_stat import JPStat
from jp_sys import JPSysParams
from jp_sys import JPSlippageType

from jp_config import JPConfigSmallMarket
from jp_config import JPBaseConfig


class JPConfigSmallMarketSim(JPConfigSmallMarket):
    config_choose = [
        [True, '设置系统参数', JPFilterFinancial, {
            'factors': [
                JPFactor('valuation.pe_ratio', min=10, max=200)  # pe > 0
                , JPFactor('indicator.eps', min=0.0)
            ]
            , 'order_by': 'valuation.circulating_market_cap'  # 按流通市值排序
            , 'sort_type': JPSortType.asc  # 从小到大排序
            , 'limit': 100  # 只取前100只
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
                 {'sort_type': JPSortType.asc, 'field': 'valuation.circulating_market_cap', 'weight': 10}]
                , [True, '换手率排序', JPSortSingle,
                   {'sort_type': JPSortType.asc, 'field': 'valuation.turnover_ratio', 'weight': 10}]
                , [True, '当前价格排序', JPSortPrice, {'sort_type': JPSortType.asc, 'field': 'close', 'weight': 10}]
                , [True, '20日涨幅排序', JPSortRate, {'sort_type': JPSortType.asc, 'day': 20, 'weight': 10}]
                , [True, '60日涨幅排序', JPSortRate, {'sort_type': JPSortType.asc, 'day': 60, 'weight': 10}]
                , [True, '120日涨幅排序', JPSortRate, {'sort_type': JPSortType.asc, 'day': 120, 'weight': 10}]
            ]
            , 'sort_type': JPSortType.asc
        }],
        [True, '趋势筛选', JPSortTrendUpper, {
            'unit': '5m',
            'periods': [5, 10, 15]
        }]
        # , [False, '过滤解禁股', JPFilterListUnlock, {'day': 60, 'trading_day': -1, 'dir': 'data/unlock'}]
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
                    True, '大盘2/8分化严重', JPTransIndexGrowthRateDiff, {
                        'index': ['000016.XSHG', JPBaseConfig.index8]
                        , 'period': 3
                    }
                ]
                , [True, '个股止盈止损器', JPTransGainLoss, {
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
                , 'buy_num': 5
                , 'sort_num': 10
                , 'day_run_one': True
            }
        ]
    ]
    config_all_group = JPBaseConfig.config_common_group + JPBaseConfig.config_time + config_trans_condition_group + config_choose_group + JPBaseConfig.config_trans_option_group
    pass
