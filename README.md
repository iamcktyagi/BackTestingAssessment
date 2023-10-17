# BackTestingAssessment
Classes are well commented and functions have self-explanatory names, but I could not find any time to comment the functions.


<a name="br1"></a> 

**Problem Statement**

The purpose is to build a back testing engine for testing Bollinger Mean Reversion strategy.

## **Strategy:**

### **Entry**

SELL <quantity> shares when “close” crosses above UBB(20,1,0) at <bar\_interval> candle interval using candlestick chart. Enter trade between 09:15 to 3:30. Note that if you are working with 15-min bars, you can enter last trade at 3:15 PM.

### **Exit:**

BUY <quantity> shares when “close” crosses below UBB(20,1,0) or at stop loss % of <stop\_loss> or target profit % of <target\_profit> at <bar\_interval> candle interval using candlestick chart.

### **Assumptions**

1\. Trading is assumed to be done on candlesticks. Trading can be done on any of 1-min, 5-min, 15-min, 1-hour or 1-day bars.
2\. There are no transaction costs and slippages involved
3\. Trading will happen between market hours i.e., 09:15 to 03:30
4\. Orders are placed in CNC code. We will assume that broker allows short selling in CNC code.
5\. No interest is earned on cash

## **Implementation**

You are provided with an Excel that contains 1-mintue candle data for tickers in Nifty 50 from 28<sup>th</sup> July 2023 to 11<sup>th</sup> August up till 12:44 PM. More on the data explained later. 

### We need to build a function that takes the following inputs:

1\. Ticker – ticker
2\. Back test start date – start\_date
3\. Back test end date – end\_date
4\. Trade interval (1M, 5M, 15M and so on) – bar\_interval
5\. Quantity of shares to be bought/sold for each ticker - quantity
6\. Starting capital - capital
7\. Stop loss (in %) for exit – stop\_loss
8\. Target Profit (in %) for exit – target\_profit

**The function should output the following:**



<a name="br2"></a> 

• A summary table containing data like – No. of trades, Number of wins, Number of

losses, Max loss, Avg gain/winning trade, Avg loss/losing trade and cumulative P&L


• A transaction summary of all trades including entries and exits (along with exit

reason – stop loss, signal, book profit) and type of transaction





• A candlestick plot with entries and exits shown


• A plot of cumulative P&L

**The data set**

You are provided with a excel that contains 1-mintue candle data for tickers in Nifty 50 from

28<sup>th</sup> July 2023 to 11<sup>th</sup> August up till 12:44 PM. Each row is indexed by ticker and time stamp

– CreatedOn. This is the starting time of the bar. For example, row corresponding to

RELIANCE and 28/07/23 9:15 is data for the first minute bar (9:15 – 9:16).

**Issues with data:**

You will always face issues with data in form of missing bars and incorrect data even in real

life. So it is important for our system to be cognizant of that and handle these issues

intelligently.

In the current data set, you will have 2 issues:

• Bar start time not exactly at minute interval. You will note start times like

28/07/2023 9:07:01 AM. We need to handle this.

• Missing bars – there will be instances of missing bars. Again, our back testing engine

should be able to handle missing bars

**Points will be rewarded on the following:**

• Accuracy of the solution
 

• Speed of execution


• Ease of understanding of code


**Submission**

Candidate should submit a python script and a readme.pdf that contains

• Approach taken and algorithm used


• All the assumptions made (over and above those provided above)


• How was data issues handled

**Bonus Points**



<a name="br3"></a> 

• Modify function above to also take order type as input. The other order type can be

MIS (intraday). Note that in MIS, trades are squared off at the open of last bar.


• Modify the function above to take a generic signal as input (instead of UBL) and

trade rules.


• Build a trading strategy that can take positions in any of the tickers in Nifty 50 (within

capital constraint). Output all the trades, P&L and capital growth curve and final IRR

of this strategy.


