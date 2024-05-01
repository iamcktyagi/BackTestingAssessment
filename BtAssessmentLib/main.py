from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import plotly.graph_objects as go

from BtAssessmentLib.BacktestModule import BTest, pandas


# {"Ticker": self.ticker, "OrderDateTime": self.__curr_dt, "InstrumentPrice": ip,
#                      "Quantity": self.quantity, "OrderPrice": ip * self.quantity,
#                      "TPPrice": self.__curr_tp, "SLPrice": self.__curr_sl, "OrderSide": orderside,
#                      "Status": st, "Reason": reason, "AmountRemaing": self.capital}
@dataclass
class BT:
    """
    BT - Backtesting Wrapper for class BTest

    This class is a wrapper for the BTest class. It allows for multiple backtests to be run in parallel.

    Parameters:
    -----------
    ticker : str or list
        Ticker symbol for the asset to be backtested. If a list is provided, multiple backtests will be run in parallel.

    start_date : str (yyyy-mm-dd hh-mm)
        Start date and time for the backtest period.

    end_date : str (yyyy-mm-dd hh-mm)
        End date and time for the backtest period.

    bar_interval : str
        Bar interval for price data. Possible values: '1min', '5min', '15min', '30min', '60min'.

    quantity : int
        The quantity of the asset to trade on each buy/sell signal.

    capital : float
        Initial capital amount available for trading.

    stop_loss : float
        Stop loss value as a percentage. Defines the maximum loss allowed on a trade.

    target : float
        Target profit value as a percentage. Defines the desired profit on a trade.

    excel_source : str (optional)

        Path to an Excel file with historical price data in xlsx format.
        Format of the Excel file:
            Column names:
                    * 'CreatedOn',
                    * 'InstrumentIdentifier',
                    * 'OpenValue',
                    * 'High',
                    * 'Low',
                    * 'CloseValue'

            - OpenValue, High, Low, CloseValue are float values
            - CreatedOn column: Date format: yyyy-mm-dd hh:mm:ss
            - InstrumentIdentifier column: Ticker symbol for the asset

    db_name : str (default: 'FastDb')
        Database name where the historical price data is stored.

    table_name : str (default: 'minute_candle')
        Table name within the database where the historical price data is stored.

    if_exists : str (default: 'replace')
        Action to take if the specified table already exists. Possible values: 'replace', 'append', 'fail'.

    change_bar_interval_at_start : bool (default: False)
        Whether to change the bar interval at the start of the backtest.

    log : bool (default: False)
        Whether to print transactions for the backtest process.

    pref_sl : bool (default: True)
        Whether to prefer stop loss over target profit.

    ordertype : str (default: 'CNC')
        Order type for the backtest. Possible values: 'CNC', 'MIS', 'NRML'.
        MIS will be cleared at or before 15:15
        CNC will be carried forward to next day
        NRML will be carried forward to next day

    Methods:
    --------
    run(workers=5)
        - Runs the backtest. If ticker is a list, multiple backtests will be run in parallel.
        - Returns a dictionary of DataFrames with the results of each backtest.
        workers : int (default: 5)
            Number of parallel backtests to run.
        Returns : dict
            Dictionary of DataFrames with the results of each backtest.
            DataFrame's columns:
                - Ticker : str (Ticker symbol for the asset)
                - OrderDateTime : str (yyyy-mm-dd hh:mm)
                - InstrumentPrice : float (Price of the asset at the time of the order)
                - Quantity : int (Quantity of the asset traded)
                - OrderPrice : float (Total value of the order)
                - TPPrice : float (Target profit price)
                - SLPrice : float (Stop loss price)
                - OrderSide : str (BUY or SELL)
                - Status : str (Order status)
                - Reason : str (Reason for order status)
                - AmountRemaing : float (Remaining capital after the order)

    """

    ticker: str or list
    start_date: str
    end_date: str
    bar_interval: str
    quantity: int
    capital: float
    stop_loss: float
    target: float
    excel_source: str = field(default='')
    db_name: str = field(default='FastDb')
    table_name: str = field(default='minute_candle')
    if_exists: str = field(default='replace')
    change_bar_interval_at_start: bool = field(default=False)
    log: bool = field(default=False)
    pref_sl: bool = field(default=True)
    ordertype: str = field(default='CNC')
    df_dict = {}
    results_dict = {}

    def __run(self, ticker=None):
        if ticker is None:
            ticker = self.ticker
        b = BTest(ticker=ticker, start_date=self.start_date, end_date=self.end_date,
                  bar_interval=self.bar_interval,
                  quantity=self.quantity, capital=self.capital, stop_loss=self.stop_loss, target=self.target,
                  excel_source=self.excel_source, db_name=self.db_name, table_name=self.table_name,
                  if_exists=self.if_exists, change_bar_interval_at_start=self.change_bar_interval_at_start,
                  log=self.log, pref_sl=self.pref_sl, ordertype=self.ordertype)
        self.df_dict[ticker] = b.get_df()
        return b.run()

    def run(self, workers=5):
        if isinstance(self.ticker, list):
            with ThreadPoolExecutor(max_workers=workers) as executor:
                results = executor.map(self.__run, self.ticker)
                self.results_dict = {x: pandas.DataFrame.from_records(y) for x, y in zip(self.ticker, results)}
                return self.results_dict
        else:
            results = {self.ticker: pandas.DataFrame.from_records(self.__run())}
            return self.results_dict

    def get_df_in_dict(self):
        return self.df_dict

    def plot_cumpnl(self, sym_name):
        equity_df = self.results_dict[sym_name].copy()
        equity_df.reset_index(inplace=True, drop=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=equity_df.index,
                                 y=equity_df['Balance'],
                                 hoverinfo='y+text',
                                 mode='lines',
                                 name='Cumulative Equity',
                                 hovertext=equity_df['OrderDateTime']))
        fig.update_layout(title='Equity Curve',
                          xaxis_title='No. of Trade',
                          yaxis_title='Cumulative P&L')
        return fig
