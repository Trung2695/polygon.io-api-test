from polygon import RESTClient
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

print("Vol: Oversized - high delta price/vol w.r.t 2 previous period")
print("Trend detection - e.g. higher highs+lows = uptrend")
print("[1-bar] Only checks the singular bar with no surrounding context")
client = RESTClient(api_key="") ########### INSERT API KEY ############

ticker = "NVDA"

#Collecting candle information
aggs = []
for a in client.get_aggs(ticker=ticker, multiplier=15, timespan="minute", from_="2024-11-20", to="2024-11-24", limit=3000):
    aggs.append(a)

#simplified trend detection
#3 bar
def ft_trend(cur, past, past_1):
    if cur.open < past.open and past.open < past_1.open and cur.close < past.close and past.close < past_1.close:
        return("Downtrend detected (-) / ")
    elif cur.open > past.open and past.open > past_1.open and cur.close > past.close and past.close > past_1.close:
        return("Uptrend detected (+) / ")
    else:
        return("")

#1 bar potential pattern warning
#tolerance levels:
tol = 0.25
doji = 0.01
def ft_1bar(agg):
    out_str = ""
    if (agg.high - agg.low != 0 and abs(agg.open - agg.close)/abs(agg.high - agg.low) > tol):
        #print("No clear 1 bar result")
        return ("No clear 1 bar result")
    else:
        if agg.high-agg.low == 0 or abs(agg.open-agg.close)/abs(agg.high - agg.low) < doji:
            out_str += "[1-bar] Doji"
        elif abs(agg.open - agg.close)/abs(agg.high - agg.low) > doji and abs(agg.open-agg.close)/abs(agg.high - agg.low) < tol and min(abs(agg.open - agg.high),abs(agg.close-agg.high))/(agg.high-agg.low) < tol:
            if agg.open - agg.close < 0: #Green bar + near the top
                out_str += "[1-bar] Uptrend reversal (-)"
            elif agg.open -agg.close >0: #Red bar + near the top
                out_str += "[1-bar] Downtrend reversal (+)"
        elif abs(agg.open - agg.close)/abs(agg.high - agg.low) > doji and abs(agg.open-agg.close)/abs(agg.high - agg.low) < tol and min(abs(agg.open - agg.low),abs(agg.close-agg.low))/(agg.high-agg.low) < tol:
            if agg.open - agg.close < 0: #Green bar + near the bottom
                out_str += "[1-bar] Downtrend reversal (-)"
            elif agg.open -agg.close >0: #Red bar + near the top
                out_str += "[1-bar] Uptrend reversal (-)"
        else:
            return ("No clear 1 bar result")
    
        return(str(datetime.utcfromtimestamp(agg.timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')) + " " + out_str)

#vol significance i.e. comparing ratio of open-close/vol
#vol tolerance
vol_tol = .25
def ft_3bar_vol(cur,past,past_1):
    cur_ratio = abs(cur.open-cur.close)/cur.volume
    past_ratio = abs(past.open-past.close)/past.volume
    past_1_ratio = abs(past_1.open-past_1.close)/past_1.volume

    if cur_ratio > (1+vol_tol)*past_ratio and cur_ratio > (1+vol_tol)*past_1_ratio:
        return("Vol: Oversized / ")
    elif cur_ratio > (1-vol_tol)*past_ratio and cur_ratio > (1-vol_tol)*past_1_ratio:
        return("Vol: Undersized / ")
    else:
        return("Vol: Consistent / ")

#2 bar tests def ft_2bar(

for i in range(len(aggs)-2):
    final = ft_trend(aggs[i+2],aggs[i+1],aggs[i]) +ft_3bar_vol(aggs[i+2],aggs[i+1],aggs[i]) + ft_1bar(aggs[i+2])
    if final.count("No clear 1 bar result") != 1 and final.count("(-)") == 1 and final.count("(+)") == 1:
        print(ft_trend(aggs[i+2],aggs[i+1],aggs[i]) +ft_3bar_vol(aggs[i+2],aggs[i+1],aggs[i]) + ft_1bar(aggs[i+2]))
    
#Example of the Aggs object: open=235.5, high=235.5, low=234.6, close=235.16, volume=16407, vwap=235.1507, timestamp=1732698000000, transactions=392, otc=None
#ft_filter creates a list with only one properties: open/high/low/close/volume & timestamp
def ft_filter(prop):
    result=[]
    if prop == "open":
        for i in aggs:
            result.append(i.open)
    elif prop == "close":
        for i in aggs:
            result.append(i.close)
    elif prop == "high":
        for i in aggs:
            result.append(i.high)
    elif prop == "low":
        for i in aggs:
            result.append(i.low)
    elif prop == "volume":
        for i in aggs:
            result.append(i.volume)
    elif prop == "timestamp":
        for i in aggs:
            result.append(str(datetime.utcfromtimestamp(i.timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')))
    return (result)


#Sorting out the data to plot:
data = {
    "Open" : ft_filter("open"),
    "High" : ft_filter("high"),
    "Low" : ft_filter("low"),
    "Close" : ft_filter("close"),
    "Volume" : ft_filter("volume"),
    "Timestamp" : ft_filter("timestamp")
    }


df = pd.DataFrame(data)
df.set_index("Timestamp", inplace = True)



fig, axs = plt.subplots(2,1,sharex = True, figsize=(12, 8))

axs[0].set_title("Price over time")
axs[0].set_ylabel("Price")
axs[0].grid(True, linestyle="--", alpha=0.6)

axs[1].bar(df.index, df["Volume"], color="blue", width=1)  # Adjust width for timestamp precision
axs[1].set_title("Volume Over Time")
axs[1].set_ylabel("Volume")
axs[1].grid(True, linestyle="--", alpha=0.6)

for idx, row in df.iterrows():
    color = "green" if row["Close"] > row["Open"] else "red"
    # Plot candle body
    axs[0].plot([idx, idx], [row["Open"], row["Close"]], color=color, linewidth=4)
    # Plot high-low line
    axs[0].plot([idx, idx], [row["Low"], row["High"]], color="black", linewidth=1)
    # Thicken the vol data


plt.xticks(rotation=45)
plt.tight_layout()

plt.show()


