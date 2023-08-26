import datetime
from dataclasses import dataclass, field

from DataETL import (EX2DB, DB2DF, seg_data, change_df_tf, bb)


@dataclass
class BTest:
    """
    start_date: yyyy-mm-dd hh-mm
    end_date: yyyy-mm-dd hh-mm

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
    __df = None

    def __post_init__(self):
        assert self.start_date != self.end_date, "Start and End date cannot be same."
        assert self.bar_interval != '', "Bar Interval cannot be empty."
        assert self.quantity > 0, "Quantity cannot be zero or negative."
        assert self.capital > 0, "Capital cannot be zero or negative."
        assert self.stop_loss > 0, "Stop Loss cannot be zero or negative."
        assert self.target > 0, "Target cannot be zero or negative."
        assert self.stop_loss < self.target, "Stop Loss cannot be greater than Target."
        if self.excel_source != '':
            self.load_data()
        self.__start_date = datetime.datetime.strptime(self.start_date, '%Y-%m-%d %H-%M')
        self.__end_date = datetime.datetime.strptime(self.end_date, '%Y-%m-%d %H-%M')
        self.__s_hour = self.__start_date.hour
        self.__s_minute = self.__start_date.minute
        self.__e_hour = self.__end_date.hour
        self.__e_minute = self.__end_date.minute
        self.__timeframe = int(self.bar_interval.lower().replace('min', ''))
        self.assign_data()

    def assign_data(self):
        use_cols = ['CreatedOn', 'OpenValue', 'High', 'Low', 'CloseValue']
        if self.excel_source != '':
            self.load_data()
        self.__df = DB2DF(db_name=self.db_name, table_name=self.table_name, sym=self.ticker)[use_cols].copy()
        self.__df = seg_data(self.__df, start_h=self.__s_hour, start_m=self.__s_minute, end_h=self.__e_hour,
                             end_m=self.__e_minute).copy()
        if self.change_bar_interval_at_start:
            self.__df = change_df_tf(self.__df, x_minutes=self.__timeframe).copy()
        self.__df[['MB','UB','LB']] = bb(self.__df, window=20, std=1)

    def load_data(self):
        EX2DB(self.excel_source, self.db_name, self.table_name, if_exists=self.if_exists)

b = BTest(ticker='SBIN', start_date='2023-07-28 09-15', end_date='2023-08-10 15-30', bar_interval='1min', quantity=1000,
          capital=100000, stop_loss=1, target=1.5, change_bar_interval_at_start=True)
b.assign_data()
