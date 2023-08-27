import datetime
from dataclasses import dataclass
from enum import Enum


class Order(Enum):
    statusEXECUTED = 'executed'
    statusCANCELLED = 'cancelled'
    statusMODIFIED = 'modified'
    statusREJECTED = 'rejected'
    statusPENDING = 'pending'
    ordertypeMARKET = 'M'
    ordertypeLIMIT = 'L'
    ordertypeSTOP = 'S'
    ordertypeSTOP_LIMIT = 'SLL'
    ordertypeSTOP_MARKET = 'SLM'
    instrumentEQUITY = 'E'
    instrumentFUTURE = 'F'
    instrumentOPTION = 'O'
    instrumentFOREX = 'X'
    ordersideBUY = 'B'
    ordersideSELL = 'S'
    producttypeCNC = 'CNC'
    producttypeMIS = 'MIS'
    producttypeNRML = 'NRML'

    def __str__(self):
        return str(self.value)


@dataclass
class Broker:
    client_id: str
    margin: float
    __current_positions: dict

    def __init__(self, client_id, margin):
        self.client_id = client_id
        self.__margin = margin
        self.__current_positions = {}
        self.position_info_schema = {"symbol": str, "quantity": int, "price": float, "status": str}
        print("Init Called")

    def __genOrderId(self,sym):
        return  sym + ":" + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

    def placeOrder(self, order_type: Order, symbol: str, quantity: int, price: float, product_type: Order):
        print("Order Placed with values: ", order_type, symbol, quantity, price, product_type)
        order_id = self.__genOrderId(symbol)
        self.__current_positions[order_id] = {"symbol": symbol, "quantity": quantity, "price": price, "status": Order.statusPENDING}
        return order_id

    def modifyOrder(self, order_id: str, quantity: int, price: float):
        print("Order Modified with values: ", order_id, quantity, price)
        if order_id not in self.__current_positions:
            raise Exception("Order ID not found")
        if self.__current_positions[order_id]["status"] in [Order.statusMODIFIED, Order.statusPENDING]:
            self.__current_positions[order_id]["quantity"] = quantity
            self.__current_positions[order_id]["price"] = price
            self.__current_positions[order_id]["status"] = Order.statusMODIFIED


b = Broker("Zerodha", 10000)


#
# bt = BT(ticker=['HDFCBANK', 'SBIN', 'BAJFINANCE'], start_date='2023-07-28 09-15', end_date='2023-08-31 15-30',
#         bar_interval='1min', quantity=1, capital=100000, stop_loss=.2, target=.2, change_bar_interval_at_start=True,
#         log=False, pref_sl=True, ordertype='MIS')
#
# a = bt.runMulti()
# # print(a)
# for x in a.values():
#     print(x)