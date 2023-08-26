import datetime
from dataclasses import dataclass, field

from DataETL import (EX2DB, DB2DF, seg_data, change_df_tf, bb, pandas, round_off_tick_size)


@dataclass
class BTest:
    """
    BTest - Backtesting Configuration Class

    This class represents the configuration for a backtesting process using historical price data. It defines various parameters and options required for the backtest.

    Parameters:
    -----------
    ticker : str
        Symbol name or identifier.

    start_date : str (yyyy-mm-dd hh:mm)
        Start date and time for the backtest period.

    end_date : str (yyyy-mm-dd hh:mm)
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


    """

    ticker: str
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

    __df = None
    main_df = None
    __position = []
    __signal = None
    __curr_low = None
    __curr_tp = None
    __trade_status = None
    __curr_sl = None
    __curr_high = None
    __curr_close = None
    __curr_open = None
    __curr_ub = None
    __df_dict = None
    __buyprice = None

    def __post_init__(self):
        assert self.start_date != self.end_date, "Start and End date cannot be same."
        assert self.bar_interval != '', "Bar Interval cannot be empty."
        assert self.quantity > 0, "Quantity cannot be zero or negative."
        assert self.capital > 0, "Capital cannot be zero or negative."
        assert self.stop_loss > 0, "Stop Loss cannot be zero or negative."
        assert self.target > 0, "Target cannot be zero or negative."
        if self.excel_source != '':
            self.load_data()
        self.__start_date = datetime.datetime.strptime(self.start_date, '%Y-%m-%d %H-%M')
        self.__end_date = datetime.datetime.strptime(self.end_date, '%Y-%m-%d %H-%M')
        self.__s_hour = self.__start_date.hour
        self.__s_minute = self.__start_date.minute
        self.__e_hour = self.__end_date.hour
        self.__e_minute = self.__end_date.minute
        self.__timeframe = int(self.bar_interval.lower().replace('min', ''))
        self.__assign_data()
        self.__df_dict = self.__df.to_dict('index')

    def __assign_data(self):
        use_cols = ['CreatedOn', 'OpenValue', 'High', 'Low', 'CloseValue']
        if self.excel_source != '':
            self.load_data()
        self.__df = DB2DF(db_name=self.db_name, table_name=self.table_name, sym=self.ticker)[use_cols].copy()
        self.__df = seg_data(self.__df, start_h=self.__s_hour, start_m=self.__s_minute, end_h=self.__e_hour,
                             end_m=self.__e_minute).copy()
        self.main_df = self.__df.copy()
        if self.change_bar_interval_at_start:
            self.__df = change_df_tf(self.__df, x_minutes=self.__timeframe).copy()
        self.__df[['MB', 'UB', 'LB']] = bb(self.__df, window=20, std=1)

    def load_data(self):
        EX2DB(self.excel_source, self.db_name, self.table_name, if_exists=self.if_exists)

    def get_df(self):
        return self.__df

    def sl_cal(self, price, short=False):
        if short is True:
            return round(price + ((price * self.stop_loss) / 100), 4)
        return round(price - ((price * self.stop_loss) / 100), 4)

    def target_cal(self, price, short=False):
        if short is True:
            return round(price - ((price * self.target) / 100), 2)
        return round(price + ((price * self.target) / 100), 2)

    def profit_statement(self):
        return self.__curr_tp >= self.__curr_open or self.__curr_tp >= self.__curr_low

    def loss_statement(self):
        return self.__curr_sl <= self.__curr_open or self.__curr_sl <= self.__curr_high

    def signal_statement(self):
        return self.__curr_close > self.__curr_ub and self.__trade_status is False and self.__signal is False

    def entry_statement(self):
        return self.__signal is True and self.__trade_status is False

    def last_sig(self, x, datetime_obj):
        return datetime_obj - datetime.timedelta(minutes=x)

    def add_sl_trade(self, date_index, row):
        reason = 'Open' if self.__curr_sl > self.__curr_open else 'High'
        print(f"SL hit [{reason}] @ {date_index}-{row}\n") if self.log else None
        self.__position.append(
            {"entry": self.__buyprice, "exit": self.__curr_sl, "profit": round(self.__curr_sl - self.__buyprice, 4),
             "status": "SL",
             "time": date_index, "reason": reason})
        self.__trade_status = False
        self.__curr_sl = None
        self.__curr_tp = None

    def add_profit_trade(self, date_index, row):
        reason = 'Open' if self.__curr_tp < self.__curr_open else 'Low'
        print(f"target hit [{reason}] @ {date_index}-{row}\n") if self.log else None
        self.__position.append(
            {"entry": self.__buyprice, "exit": self.__curr_tp, "profit": round(self.__curr_tp - self.__buyprice, 4),
             "status": "TP",
             "time": date_index, "reason": reason})
        self.__trade_status = False
        self.__curr_sl = None
        self.__curr_tp = None

    def add_reversion_trade(self, date_index, row):
        reason = 'Reverse'
        print(f"Trend Rev @ {date_index}-{row} [{reason}] \n")
        self.__position.append(
            {"entry": self.__buyprice, "exit": self.__curr_close,
             "profit": round(self.__curr_close - self.__buyprice, 4),
             "status": "CL",
             "time": date_index, "reason": reason})
        self.__trade_status = False
        self.__curr_sl = None
        self.__curr_tp = None

    def strategy(self):
        self.__position = []
        self.__curr_sl, self.__curr_tp, self.__signal, self.__trade_status = None, None, False, False
        for date_index, row in self.__df_dict.items():
            if all(not pandas.isna(x) for x in row.values()):
                print(pandas.to_datetime(date_index), "-----", row)
                # print("Signal: ",self.last_sig(self.__timeframe, date_index), '     ', date_index)
                self.__curr_ub = row['UB']
                self.__curr_open = row['OpenValue']
                self.__curr_low = row['Low']
                self.__curr_high = row['High']
                self.__curr_close = row['CloseValue']
                if self.entry_statement():
                    self.__buyprice = self.__curr_open
                    if self.__curr_sl is not None or self.__curr_tp is not None:
                        input("Error: SL or TP not None")
                    self.__curr_sl = round_off_tick_size(b.sl_cal(self.__buyprice, short=True))
                    self.__curr_tp = round_off_tick_size(b.target_cal(self.__buyprice, short=True))
                    print(
                        f"Short Ent @ {date_index}-BP:{self.__buyprice} SL:{self.__curr_sl} TP:{self.__curr_tp}\n{row}") if self.log else None
                    self.__signal = False
                    self.__trade_status = True

                if self.__trade_status is True:
                    if self.profit_statement() and self.loss_statement():  # Delete it after debugging
                        input(f"Both SL and TP hit @ {date_index}{row}")
                    if self.loss_statement():
                        self.add_sl_trade(date_index, row) if self.pref_sl is False and self.profit_statement() is True else None
                    elif self.profit_statement():
                        self.add_profit_trade(date_index, row)
                    if self.__curr_close < self.__curr_ub:
                        self.add_reversion_trade(date_index, row)

                if self.signal_statement():
                    self.__signal = True
                    print(f'Short Sig @ {date_index}-{row}') if self.log else None

    def run(self):
        self.strategy()
        return self.__position


b = BTest(ticker='SBIN',
          start_date='2023-07-28 09-15',
          end_date='2023-08-31 15-30',
          bar_interval='15min',
          quantity=1,
          capital=100000,
          stop_loss=.2,
          target=.2,
          change_bar_interval_at_start=True, log=True)
position = b.run()
adfg = pandas.DataFrame(position)
adfg['profit'] = adfg['profit'].astype(float)
print(adfg['profit'].sum())
print(adfg.to_excel("position.xlsx"))
