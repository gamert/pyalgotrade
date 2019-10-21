# Pyalgotrade是事件驱动的回测框架，支持虚盘和实盘两种交易。文档完整，整合了TA-Lib(技术分析库)。在速度和灵活方面都表现出众。但它的一大硬伤是不支持 Pandas 的模块和对象，而且数据格式不支持国内股票数据，需要我们自己实现数据转换。
#
# PyAlgoTrade 六大组件：
# Strategies策略： 定义的实现交易逻辑的类：何时买、何时卖，等等；
# Feeds数据源：These are data providing abstractions. 例如，你可以使用CSV数据源从一个格式化后的csv(以逗号分割)文件中加载数据推送给策略。 数据源不仅限于bars。
# Brokers经纪商：经纪商模块负责执行订单。
# DataSeries数据序列：DataSeries 是用于管理时间序列的抽象类
# Technicals指标计算：这是你用来对DataSeries进行计算的一组过滤（指标）器。 例如简单移动平均线（SMA）,相对强弱指标(RSI)等. 这些过滤(指标)器被建模为DataSeries 的装饰器。
# Optimizer优化：这是能让你在不同电脑之间、或多进程、或二者结合以加快回测效率的一组类。


# 基于 pyalgotrade 的交易策略类
from pyalgotrade.stratanalyzer import returns, sharpe

from pyalgotrade.technical import ma, cross

from pyalgotrade import strategy, plotter


class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, smaPeriod):
        super(MyStrategy, self).__init__(feed)
        self.__instrument = instrument
        self.__closed = feed[instrument].getCloseDataSeries()
        self.__sma = ma.SMA(self.__closed, smaPeriod)
        self.__position = None
        self.getBroker()

    def getSMA(self):
        return self.__sma

    def onEnterLong(self, position):
        print("onEnterLong", position.getShares())

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY at %.2f" % (execInfo.getPrice()))

    def onEnterCanceled(self, position):
        self.__position = None
        print("onEnterCanceled", position.getShares())

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL at $%.2f" % (execInfo.getPrice()))
        self.__position = None
        print("onExitOk", position.getShares())

    def onExitCanceled(self, position):
        self.__position.exitMarket()
        print("onExitCanceled", position.getShares())

    def onBars(self, bars):
        if self.__position is None:
            if cross.cross_above(self.__closed, self.__sma) > 0:
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                print("cross_above shares,", shares)
                # Enter a buy market order. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, shares, True)
        elif not self.__position.exitActive() and cross.cross_below(self.__closed, self.__sma) > 0:
            print("cross_below")
            self.__position.exitMarket()

    def getClose(self):
        return self.__closed

#以 格力电器（000651）为例，初始资本 100万，回溯时间 2018年1月1日 至 2019年 2月 12日，SMA周期 30：
code = "000651" # 格力电器
feed = tsfeed.Feed()
feed.addBarsFromCode(code,start='2018-01-01',end='2019-02-12')

# Evaluate the strategy with the feed's bars.
myStrategy = MyStrategy(feed, code, 30) # SMA周期 30
returnsAnalyzer = returns.Returns()
myStrategy.attachAnalyzer(returnsAnalyzer)
sharpe_ratio = sharpe.SharpeRatio()
myStrategy.attachAnalyzer(sharpe_ratio)

plt = plotter.StrategyPlotter(myStrategy)
plt.getInstrumentSubplot(code).addDataSeries("SMA", myStrategy.getSMA())
plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", returnsAnalyzer.getReturns())

myStrategy.run()
myStrategy.info("Final portfolio value: $%.2f" % myStrategy.getResult())

plt.plot()


# 基于我们的策略，坚持长期策略投资，其最大收益高于大盘表现（最大收益率 347% ：格力电器，10年期，SMA 20）；
# 选取SMA 周期，在 20 左右（在15 ~ 30 之间），其收益最大，相对亏损风险较小；
# 选取SMA 周期越大（等于 50 时），风险越小；
# 综合来看，投资格力电器收益率更大，而风险在可控范围内。
