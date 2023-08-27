import datetime
from dataclasses import dataclass, field

from BtAssessmentMum.__deps import (EX2DB, DB2DF, seg_data, change_df_tf, bb, pandas, round_off_tick_size)


@dataclass
class BTest:
    """
    BTest - Backtesting Configuration Class

    This class represents the configuration for a backtesting process using historical price data. It defines various parameters and options required for the backtest.

    Parameters:
    -----------
    ticker : str
        Symbol name or identifier.

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
    ordertype: str = field(default='CNC')

    __df = None
    main_df = None
    __orderbook = None
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
    __sellprice = None
    __buyprice = None
    __curr_dt = None
    __last_candle_time = None
    __row = None
    __entry_time = None
    __reverse = False
    __pnl = 0

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
        use_cols = ['OpenValue', 'High', 'Low', 'CloseValue']
        if self.excel_source != '':
            self.load_data()
        self.__df = DB2DF(db_name=self.db_name, table_name=self.table_name, sym=self.ticker).copy()
        if len(self.__df) == 0:
            raise Exception("No data found in database. Perhaps wrong symbol or date?")
        self.main_df = self.__df.copy()
        self.__df = self.__df[use_cols].copy()
        if self.change_bar_interval_at_start:
            self.__df = change_df_tf(self.__df, x_minutes=self.__timeframe).copy()
        self.__df = seg_data(self.__df, start_h=self.__s_hour, start_m=self.__s_minute, end_h=self.__e_hour,
                             end_m=self.__e_minute).copy()
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
        m = 15 if self.ordertype == 'MIS' else 30
        dt = self.__curr_dt.replace(hour=15, minute=m)
        last_sig_time = dt - datetime.timedelta(minutes=self.__timeframe)
        return (self.__curr_close > self.__curr_ub and
                self.__trade_status is False and
                self.__signal is False and self.__curr_dt.time() < last_sig_time.time())

    def reversion_statement(self):
        return self.__curr_close < self.__curr_ub and self.__trade_status is True

    def entry_statement(self):
        dt_condition = self.__curr_dt.time() < datetime.time(15, 15)
        capital_validation = self.capital >= (self.__curr_open * self.quantity)
        resp = self.__signal is True and self.__trade_status is False and self.__curr_dt == self.__entry_time and dt_condition and capital_validation
        if resp:
            return resp
        else:
            self.__signal = False
            return False

    def add_entry_trade(self):
        self.__sellprice = self.__curr_open
        if self.__curr_sl is not None or self.__curr_tp is not None:
            input("Error: SL or TP not None")
        self.__curr_sl = round_off_tick_size(self.sl_cal(self.__sellprice, short=True))
        self.__curr_tp = round_off_tick_size(self.target_cal(self.__sellprice, short=True))
        self.__signal = False
        self.__trade_status = True
        self.add_order(orderside='Short', reason='Entry')
        print(
            f"Short Ent @ {self.__curr_dt} -SP:{self.__sellprice} SL:{self.__curr_sl} TP:{self.__curr_tp}\n{self.__row}") if self.log else None

    def trade_sig_time_validation(self):
        return self.__curr_dt + datetime.timedelta(minutes=self.__timeframe)

    def mis_square_off_statement(self):
        if self.ordertype == 'MIS' and self.__curr_dt.time() >= datetime.time(15, 15) and self.__trade_status is True:
            return True
        return False

    def assign_values(self, row):
        self.__row = row
        self.__curr_ub = row['UB']
        self.__curr_open = row['OpenValue']
        self.__curr_low = row['Low']
        self.__curr_high = row['High']
        self.__curr_close = row['CloseValue']

    def reset_values(self):
        self.__trade_status = False
        self.__curr_sl = None
        self.__curr_tp = None

    def add_order(self, orderside, reason):
        ip = self.__sellprice if orderside == 'Short' else self.__buyprice
        st = "Running" if orderside == 'Short' else "Closed"
        if orderside == 'Short':
            self.__pnl = 0
        else:
            self.__pnl = round((self.__sellprice - self.__buyprice) * self.quantity, 2)
        self.capital = self.capital + self.__pnl
        print(f"Capital: {self.capital}") if self.log else None
        pnl_to_add = self.__pnl if orderside == 'Long' else None
        order_log = {"Ticker": self.ticker, "OrderDateTime": self.__curr_dt, "InstrumentPrice": ip,
                     "Quantity": self.quantity, "OrderPrice": ip * self.quantity,
                     "TPPrice": self.__curr_tp, "SLPrice": self.__curr_sl, "OrderSide": orderside,
                     "Status": st, "Reason": reason, "Balance": self.capital, "PnL": pnl_to_add}
        self.__orderbook.append(order_log)
        del order_log

    def add_sl_trade(self):
        reason = "SL Hit"
        self.__buyprice = self.__curr_sl
        self.add_order(orderside='Long', reason=reason)
        print(f"SL hit [{reason}] @ {self.__curr_dt}-{self.__row}\n") if self.log else None
        self.reset_values()

    def add_profit_trade(self):
        reason = "TP Hit"
        self.__buyprice = self.__curr_tp
        print(f"Target hit [{reason}] @ {self.__curr_dt}-{self.__row}\n") if self.log else None
        self.add_order(orderside='Long', reason=reason)
        self.reset_values()

    def add_reversion_trade(self):
        reason = 'Trend Reversed'
        self.__reverse = False
        self.__signal = False
        self.__buyprice = self.__curr_open
        print(f"Trend Rev @ {self.__curr_dt}-{self.__row} [{reason}] \n") if self.log else None
        self.add_order(orderside='Long', reason=reason)

        self.reset_values()

    def auto_exit(self):
        reason = 'Auto SquaredOff'
        self.__buyprice = self.__curr_open
        print(f"MIS @ {self.__curr_dt}-{self.__row} [{reason}] \n") if self.log else None
        self.add_order(orderside='Long', reason=reason)
        self.reset_values()

    def __strategy(self):
        self.__orderbook = []
        self.__curr_sl, self.__curr_tp, self.__signal, self.__trade_status = None, None, False, False
        for date_index, row in self.__df_dict.items():
            if all(not pandas.isna(x) for x in row.values()):
                self.assign_values(row)
                self.__curr_dt = date_index
                if self.__reverse is True:
                    self.add_reversion_trade()
                if self.entry_statement():
                    self.add_entry_trade()
                if self.__trade_status is True:
                    if self.loss_statement():
                        self.add_sl_trade() if self.pref_sl is True else self.add_profit_trade() if self.profit_statement() else None
                    elif self.profit_statement():
                        self.add_profit_trade()
                if self.reversion_statement():
                    self.__reverse = True
                if self.mis_square_off_statement():
                    self.auto_exit()
                elif self.signal_statement():
                    self.__entry_time = self.trade_sig_time_validation()
                    self.__signal = True
                    print(f'Short Sig @ {date_index}-{row} {self.__entry_time}') if self.log else None

    def run(self):
        self.__strategy()
        return self.__orderbook
