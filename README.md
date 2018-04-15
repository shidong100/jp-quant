# jp-quant

### 该项目是的设计目的是针对市面上较流行的量化平台开发的平台，可以根据自己用的平台，继承JPPlatform实现各方法来达到跨平台的效果。

### 支持动态配置组合策略

```
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
```

## 使用方法
```
# 开盘前运行
# 1. 实际回测中 context 必须不能传None（必须传各平台传过来的context）
# 2. 实际回测中 platform 必须不能传None（必须继承JPPlatform根据各平台实现各个功能函数）
strategy = JPGroupStrategy(None, {
    'name': '通用跨平台小市值测试策略',
    'class': JPGlobalCls,
    'platform': None,
    'config': {}
})
strategy.initialize()
```
