from BtAssessmentMum import BT

bt = BT(ticker=['HDFCBANK', 'SBIN', 'BAJFINANCE'], start_date='2023-07-28 09-15', end_date='2023-08-31 15-30',
        bar_interval='1min', quantity=1, capital=100000, stop_loss=.2, target=.2, change_bar_interval_at_start=True,
        log=False, pref_sl=True, ordertype='MIS')

a = bt.run()
for x in a.values():
    print(x)


