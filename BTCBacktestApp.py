
from scipy.signal import find_peaks
import datetime
from st_aggrid import AgGrid
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, datetime
import platform
print(platform.python_version())
import warnings
warnings.filterwarnings('ignore')


### Sidebar Header###
st.sidebar.header('User Input')



################### Declaration of Functions ###########################                
sellOrder = 0
totalBTCToSell = 0
profitToBuy = 0     
# Find the market top peaks that trigger the strategy of waiting to buy until market bottom is reached
def getMarketPeaks(avg, freq):

    peaks, _ = find_peaks(avg, height=0.77, distance = 10)
    validPeaks = []
    for i in range(1,len(peaks)):
        # This tries to exclude local market tops by checking the closeness from one top to other 
        #to avoid triggering the strategy, if they are too close, the first top is a local top, so it is not included as valid peak
        if (abs(peaks[i] - peaks[i-1]) > 265 and freq == 'Daily'):
            validPeaks.append(peaks[i-1])
        elif(abs(peaks[i] - peaks[i-1]) > 45 and freq == 'Weekly'):
            validPeaks.append(peaks[i-1])
                              
    return validPeaks


# Sets the signal for transaction type based on risk level
def setTransactionType(avg, totalBalance, totalBTC, sellOrder, totalBTCToSell):
    signal = " "

    if ((0.6 <= avg <= 0.7) and (totalBTC > 0) and sellOrder == 0):
                 
        signal = "Sell"   
        sellOrder = 1
        totalBTCToSell = totalBTC
     
    elif ((0.7 <= avg < 0.8) and (totalBTC > 0) and sellOrder <= 1):         
        if totalBTCToSell == 0:
            totalBTCToSell = totalBTC
        signal = "Sell"   
        sellOrder = 2
    elif ((0.8 <= avg < 0.9) and (totalBTC > 0) and sellOrder <= 2):         
        signal = "Sell"   
        sellOrder = 3 
    elif ((avg >= 0.9) and (totalBTC > 0) and sellOrder <= 3):      
        signal = "Sell"   
        sellOrder = 4
        #st.write("Test for:",sellOrder)                    
    elif ((avg < 0.5) and (totalBalance > 0)):
        signal = "Buy"
        sellOrder = 0  

    else:
        signal ="No Trx"    

    return signal, sellOrder, totalBTCToSell




def getInput():
    
    ### Initialisation variables ###
    now = datetime.now()
    
    ### Getting Input ###
    start_date = st.sidebar.text_input("Start Date", "2020-04-17")
    end_date = st.sidebar.text_input("End Date", now.date())
    model = st.sidebar.selectbox(
        "Select model to test", ("BitcoinRaven Old Model", "BitcoinRaven New Model", "BitcoinRaven Model Modified", "Jay's Model", "Ben's BTC Model", "Bringer of Light's Model", "UDPI's Long Model", "UDPI's Short Model", "UDPI's Medium Model", "MVRV Z", "Ben's ETH Model", "UDPI's Medium ETH", "UDPI's Short ETH", "UDPI's Long ETH", "UDPI's Short SOL","UDPI's Medium SOL","UDPI's Long SOL", "UDPI's Medium KSM", "UDPI's Short KSM", "UDPI's Long KSM")
    )
    freqDCA = st.sidebar.selectbox(
        "Select DCA frequency", ("Weekly", "Daily", "Monthly")
    )
    
    # Capital to invest    
    initToken = st.sidebar.number_input("Initial BTC",min_value=0,value=0)
    DCA = st.sidebar.number_input("DCA to invest monthly",min_value=0,value=1000)
    initCapital = st.sidebar.number_input("Initial Capital to invest",min_value=0,value=0)
    
    # Textboxes for sell parameters
    tokenUnits = st.sidebar.number_input("Divide current Total BTC in portions before transaction",min_value=0,value=100)
    y1 = st.sidebar.number_input("Portions to sell at 0.6-0.7 risk",min_value=0,max_value=tokenUnits,value=15)
    y2 = st.sidebar.number_input("Portions to sell at 0.7-0.8 risk",min_value=0,max_value=tokenUnits,value=20)
    y3 = st.sidebar.number_input("Portions to sell at 0.8-0.9 risk",min_value=0,max_value=tokenUnits,value=25)
    y4 = st.sidebar.number_input("Portions to sell at > 0.9 risk",min_value=0,max_value=tokenUnits,value=40)
    
    if (y1+y2+y3+y4) > tokenUnits:
        raise("Percentage assigned to sell is bigger than total percent")
    # Textboxes for buy parameters
    oneXAmount = st.sidebar.number_input("Set value as 1x for DCA",min_value=0.00,value=100.00, format="%.2f")
    x1 = st.sidebar.number_input("X amount to buy at 0.4-0.5 risk",min_value=0.00,max_value=150.00,value=1.00, format="%.2f")
    x2 = st.sidebar.number_input("X amount to buy at 0.3-0.4 risk",min_value=0.00,max_value=150.00,value=3.00, format="%.2f")
    x3 = st.sidebar.number_input("X amount to buy at 0.2-0.3 risk",min_value=0.00,max_value=550.00,value=4.00, format="%.2f")
    x4 = st.sidebar.number_input("X amount to buy at 0.1-0.2 risk",min_value=0.00,max_value=5000.00,value=8.00, format="%.2f")
    x5 = st.sidebar.number_input("X amount to buy < 0.1 risk",min_value=0.00,max_value=10000.00,value=12.00,format="%.2f")
    

    
    percentageProfit = st.sidebar.number_input("% from profits to buy",min_value=0,max_value=100,value=0)
    
    
    return start_date, end_date, model, freqDCA, initToken, DCA, initCapital, tokenUnits, oneXAmount, y1, y2, y3, y4, x1, x2, x3, x4, x5, percentageProfit


def freqSelected(freqDCA):
    
    if (freqDCA == "Daily"):
        return 'D'
    elif (freqDCA == "Weekly"):
        return 'W-SUN'
    elif (freqDCA == "Monthly"):
        return 'M'
    else:
        'None'
    
def DCAInvestfreq(freqDCA, DCA):
    
    if freqDCA == 'Monthly':
        return DCA
    elif (freqDCA == "Weekly"):
        return round((DCA / 4),2)
    else:
        return round((DCA / 28),2)

def statisticsTable(token, totalToken, totalBalance, totalProfit, totalValue, avg, price, totalInvested, tokenHodl, totalBalanceHodl, hodl):

    lst = [[f"Total {token}:", round((totalToken),3)], [f"Total Balance:",round(totalBalance,2)], [f"Total Profit:",round(totalProfit,2)], [f"Total Portfolio:",round(totalValue,2)], 
    [f"Risk:",round(avg,2)], [f"Last {token} price:", round(price,2)], [f"Total Invested: ", round(totalInvested,2)], 
    [f"Total {token} if just hodl and not selling:", round((tokenHodl),3)],[f"Total Balance if just hodl and not selling: ", round(totalBalanceHodl,2)], 
    [f"Portfolio value if just hodl and not selling:", round(hodl,2)] ]
    
    return lst
 
        
def BTCmodelSelected(model):
    
   
    if (model == "BitcoinRaven Old Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\OldMriskNew.csv", usecols=["Date", "Value", "avg"])    
    elif (model == "BitcoinRaven New Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\Mrisk.csv", usecols=["Date", "Value", "avg"])
    elif (model == "BitcoinRaven Model Modified"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\MriskChanged.csv", usecols=["Date", "Value", "avg"])
    elif (model == "Jay's Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\JayRiskMetricBTCAdapted.csv", usecols=["Date", "Value", "avg"]).rename(columns={"Risk": "avg","Price":"Value"})
    elif (model == "Ben's BTC Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\BenRiskMetricBTCAdapted.csv", usecols=["Date", "Value", "avg"])
    elif (model == "Ben's ETH Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\BenRiskMetricETHAdapted.csv", usecols=["Date", "Value", "avg"])
    elif (model == "Bringer of Light's Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\BringerRiskMetricBTCAdapted.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Long Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiBTCAdaptedLong.csv", usecols=["Date", "Value", "avg"])
    elif (model == "MVRV Z"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\BTC_MVRVZ.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Short Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiBTCAdaptedShort.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Medium Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiBTCAdaptedMedium.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Long ETH"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiETHAdaptedLong.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Medium ETH"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiETHAdaptedMedium.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Short ETH"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiETHAdaptedShort.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Medium SOL"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiSOLAdaptedMedium.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Long KSM"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiKUSAMAAdaptedLong.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Medium KSM"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiKUSAMAAdaptedMedium.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Short KSM"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiKUSAMAAdaptedShort.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Short SOL"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiSOLAdaptedShort.csv", usecols=["Date", "Value", "avg"])
    elif (model == "UDPI's Long SOL"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\UdpiSOLAdaptedLong.csv", usecols=["Date", "Value", "avg"])
    else:
        'None'
         

def sell(transactionAmount, price, totalBTC, totalProfit, percentageProfit):
    if transactionAmount > totalBTC:
        transactionAmount = totalBTC
    BTCTradedPrice = transactionAmount * price
    profitToReinvest = profitToInvest(BTCTradedPrice, percentageProfit)  
    totalProfit = totalProfit + (BTCTradedPrice - profitToReinvest)
    totalBTC = totalBTC - transactionAmount
    return totalProfit, totalBTC, profitToReinvest

def buy(transactionAmount,price, totalBalance, totalBTC):
    if transactionAmount > totalBalance:
        transactionAmount = totalBalance
    BTCTraded = transactionAmount / price
    totalBalance = totalBalance - transactionAmount       
    totalBTC = totalBTC + BTCTraded
    return totalBalance, totalBTC

def sellToken(avg, price, totalBalance, totalProfit, totalBTC, totalBTCToSell, tokenUnits, y1, y2, y3, y4, percentageProfit, profitToBuy):
       
    # Modify to set selling amount
    transactionAmount = totalBTCToSell / tokenUnits
    if 0.6 <= avg < 0.7:
        transactionAmount = transactionAmount * y1
        totalProfit,totalBTC, profitToBuy = sell(transactionAmount, price, totalBTC, totalProfit, percentageProfit)            
    elif 0.7 <= avg < 0.8:
        transactionAmount = transactionAmount * y2
        totalProfit, totalBTC, profitToBuy = sell(transactionAmount, price, totalBTC, totalProfit, percentageProfit)
    elif 0.8 <= avg < 0.9:
        transactionAmount = transactionAmount * y3
        totalProfit, totalBTC, profitToBuy = sell(transactionAmount, price, totalBTC, totalProfit, percentageProfit)
    elif avg >= 0.9:
        transactionAmount = transactionAmount * y4
        totalProfit, totalBTC, profitToBuy = sell(transactionAmount, price, totalBTC, totalProfit, percentageProfit)
    
    
    return round(totalProfit,2), totalBTC, round(profitToBuy,2)
    
    
def buyToken(avg, price, totalBalance, totalBTC, oneXAmount, x1, x2, x3, x4, x5):
             
    transactionAmount = oneXAmount
            
    if 0.4 < avg <= 0.5:
        transactionAmount = transactionAmount * x1
        totalBalance, totalBTC = buy(transactionAmount, price, totalBalance, totalBTC)
        
    elif 0.3 < avg <= 0.4:
        transactionAmount = transactionAmount * x2
        totalBalance, totalBTC = buy(transactionAmount, price, totalBalance, totalBTC)
                
    elif 0.2 < avg <= 0.3:
        transactionAmount = transactionAmount * x3
        totalBalance, totalBTC = buy(transactionAmount, price, totalBalance, totalBTC)
    elif 0.1 < avg <= 0.2:
        transactionAmount = transactionAmount * x4
        totalBalance, totalBTC = buy(transactionAmount, price, totalBalance, totalBTC)
    elif avg <= 0.1:
        transactionAmount = transactionAmount * x5
        totalBalance, totalBTC = buy(transactionAmount, price, totalBalance, totalBTC)

    return round(totalBalance,2), totalBTC

    
def profitToInvest(totalProfit, percentageProfit):
    result =  (totalProfit/100) * percentageProfit
    return result
################### Getting variables values ###########################

now = datetime.now()


start, end, model, freqDCA, initToken, DCA, initCap, tokenUnits, oneXAmount, y1, y2, y3, y4, x1, x2, x3, x4, x5, percentageProfit = getInput()


date_time = now.strftime("%d/%m/%Y, %H:%M:%S")



################### Displaying Streamlit headers ###########################

st.write(
    """
 # Risk Metric Backtesting
 
 **Select different models and values to test.**
 """
 )
    
st.write("Test for:", model, " at: ", date_time)


################### Dataframe Setup ###########################
df = BTCmodelSelected(model)

df["Date"] = pd.to_datetime(df["Date"])

# Date range
df = df[df.Date > pd.to_datetime(start)]
df = df[df.Date < pd.to_datetime(end)]

# DCA frequency set M, W, D
df = df.set_index("Date").resample(freqSelected(freqDCA)).last() 

################### Initiallisation of Columns ###########################

# Rounds price value to 2 decimal places
df["Value"] = round(df["Value"],2) 

# Rounds risk value to 3 decimal places
df["avg"] = round(df["avg"],3)

# Dollar Cost Average to invest periodically
df["DCA"] = 0
df["DCA"] = DCAInvestfreq(freqDCA, DCA)

df["OrderType"] = ""

df["BalanceBeforeTrx"] =""
df["BalanceBeforeTrx"].iloc[0] = 0

df["transactionAmount"] =""
df["transactionAmount"].iloc[0] = 0

df["% TrxOfTotal $"] = ""
df["% TrxOfTotal $"].iloc[0] = 0

# initial capital in dollars
df["totalBalance"] = ""
df["totalBalance"].iloc[0] = initCap

df["TotalProfit"] = ""
df["TotalProfit"].iloc[0] = 0

df["ProfitToBuy"] = ""
df["ProfitToBuy"].iloc[0] = 0

df["TokenBeforeTrx"] =""
df["TokenBeforeTrx"].iloc[0] = 0

df["tokenTraded"] = ""
df["tokenTraded"].iloc[0] = 0


# initial capital in token
df["totalBTC"] = ""
df["totalBTC"].iloc[0] = initToken

df["% TrxOfTotal Token"] = ""
df["% TrxOfTotal Token"].iloc[0] = 0

# total combined between total balance of dollars plus total current value of tokens
df["TotalValue"] = ""
df["TotalValue"].iloc[0] = ((df['Value'].iloc[0]) * (df['totalBTC'].iloc[0])) + df['totalBalance'].iloc[0]

df["TotalInvested"] = ""
df["TotalInvested"] = df["totalBalance"].iloc[0]

df['TotalBalanceHodl'] = ""
df['TotalBalanceHodl'].iloc[0] = initCap


df["Hodl"] = (df["TotalBalanceHodl"].iloc[0] / df['Value'].iloc[0]) * df["Value"].iloc[0]

df['BTCHodl'] = df["TotalBalanceHodl"].iloc[0] / df['Value'].iloc[0] + initToken

################### Dataframe Population ###########################
df.reset_index(inplace=True)

for i in range(1, df.shape[0]):

    
    signal, sellOrder, totalBTCToSell = setTransactionType(avg=df["avg"][i], totalBalance=df["totalBalance"][i-1], totalBTC=df["totalBTC"][i-1], sellOrder = sellOrder, totalBTCToSell = totalBTCToSell)
    df["OrderType"][i] = signal
    

    if signal == "Buy":
        df["totalBalance"][i] = buyToken(avg=df["avg"][i], price=df["Value"][i], totalBalance=df["totalBalance"][i-1]+df["DCA"][i-1], totalBTC=df["totalBTC"][i-1], oneXAmount = oneXAmount, x1=x1, x2=x2, x3=x3, x4=x4, x5=x5)[0]
        df["totalBTC"][i] = buyToken(avg=df["avg"][i], price=df["Value"][i], totalBalance=df["totalBalance"][i-1]+df["DCA"][i-1], totalBTC=df["totalBTC"][i-1], oneXAmount = oneXAmount, x1=x1, x2=x2, x3=x3, x4=x4, x5=x5)[1]
        df["TotalProfit"][i] = df["TotalProfit"][i-1]
        df['TotalBalanceHodl'][i] = buyToken(avg=df["avg"][i], price=df["Value"][i], totalBalance=df["TotalBalanceHodl"][i-1]+df["DCA"][i-1], totalBTC=df['BTCHodl'][i-1], oneXAmount = oneXAmount, x1=x1, x2=x2, x3=x3, x4=x4, x5=x5)[0]
        df['BTCHodl'][i] = buyToken(avg=df["avg"][i], price=df["Value"][i], totalBalance=df["TotalBalanceHodl"][i-1]+df["DCA"][i-1], totalBTC=df['BTCHodl'][i-1], oneXAmount = oneXAmount, x1=x1, x2=x2, x3=x3, x4=x4, x5=x5)[1]
        df["ProfitToBuy"][i] = df["ProfitToBuy"][i-1]
        df["TotalInvested"][i] = df["TotalInvested"][i-1] + df["DCA"][i]
        df["transactionAmount"][i] = (df["totalBalance"][i] - df["DCA"][i-1]) - df["totalBalance"][i-1]
        
    elif signal == "Sell":
        df["totalBalance"][i] = df["totalBalance"][i-1] + sellToken(avg=df["avg"][i], price=df["Value"][i], totalBalance=df["totalBalance"][i-1]+df["DCA"][i-1], totalProfit=df["TotalProfit"][i-1], totalBTC=df["totalBTC"][i-1], totalBTCToSell=totalBTCToSell, tokenUnits = tokenUnits, y1 = y1, y2 = y2, y3 = y3, y4 = y4, percentageProfit = percentageProfit, profitToBuy=profitToBuy)[2]
        df["TotalProfit"][i] = sellToken(avg=df["avg"][i], price=df["Value"][i],totalBalance=df["totalBalance"][i-1]+df["DCA"][i-1], totalProfit=df["TotalProfit"][i-1], totalBTC=df["totalBTC"][i-1], totalBTCToSell=totalBTCToSell, tokenUnits = tokenUnits, y1 = y1, y2 = y2, y3 = y3, y4 = y4, percentageProfit = percentageProfit,profitToBuy=profitToBuy)[0]
        df["totalBTC"][i] = sellToken(avg=df["avg"][i], price=df["Value"][i],totalBalance=df["totalBalance"][i-1]+df["DCA"][i-1], totalProfit=df["TotalProfit"][i-1], totalBTC=df["totalBTC"][i-1], totalBTCToSell=totalBTCToSell, tokenUnits = tokenUnits, y1 = y1, y2 = y2, y3 = y3, y4 = y4, percentageProfit = percentageProfit, profitToBuy=profitToBuy)[1]
        df['TotalBalanceHodl'][i] = df['TotalBalanceHodl'][i-1] + df['DCA'][i-1]
        df['BTCHodl'][i] = df['BTCHodl'][i-1]
        df["ProfitToBuy"][i] = df["ProfitToBuy"][i-1] + sellToken(avg=df["avg"][i], price=df["Value"][i], totalBalance=df["totalBalance"][i-1]+df["DCA"][i-1], totalProfit=df["TotalProfit"][i-1], totalBTC=df["totalBTC"][i-1], totalBTCToSell=totalBTCToSell, tokenUnits = tokenUnits, y1 = y1, y2 = y2, y3 = y3, y4 = y4, percentageProfit = percentageProfit,profitToBuy=profitToBuy)[2]       
        df["TotalInvested"][i] = df["TotalInvested"][i-1] + df["DCA"][i] 
        df["transactionAmount"][i] = (df["totalBalance"][i] - df["DCA"][i-1]) - df["totalBalance"][i-1]
    elif signal == "No Trx":

        df["totalBalance"][i] = round(df["totalBalance"][i-1]+df["DCA"][i], 2)
        df["TotalProfit"][i] = df["TotalProfit"][i-1]
        df["totalBTC"][i] = df["totalBTC"][i-1]
        df['TotalBalanceHodl'][i] = df['TotalBalanceHodl'][i-1] + df['DCA'][i-1]
        df['BTCHodl'][i] = df['BTCHodl'][i-1]
        df["ProfitToBuy"][i] = df["ProfitToBuy"][i-1]
        df["TotalInvested"][i] = df["TotalInvested"][i-1] + df["DCA"][i]
        df["transactionAmount"][i] = 0
    

    
    df["BalanceBeforeTrx"][i] = round(df["totalBalance"][i-1]+df["DCA"][i], 2)  
    df["% TrxOfTotal $"][i] = round(df["transactionAmount"][i] / (df["totalBalance"][i-1] + df["DCA"][i-1]) * 100,2)
    
       
    df["tokenTraded"][i] = df["totalBTC"][i] - df["totalBTC"][i-1] 
    df["TokenBeforeTrx"][i] = df["totalBTC"][i-1] 
    
    try:
        df["% TrxOfTotal Token"][i] = round((df["tokenTraded"][i] / df["totalBTC"][i - 1]) * 100, 2)
    except ZeroDivisionError:
        pass
    
    
    df["TotalValue"][i] = round(((df['Value'][i])*(df['totalBTC'][i])) + df['totalBalance'][i] + df['TotalProfit'][i],2)
    df["Hodl"][i] = round((df['BTCHodl'][i] * df["Value"][i]) + df['TotalBalanceHodl'][i],2)

lst = statisticsTable('BTC', df['totalBTC'].iloc[-1], df['totalBalance'].iloc[-1], df['TotalProfit'].iloc[-1], df['TotalValue'].iloc[-1], df['avg'].iloc[-1], df['Value'].iloc[-1], df['TotalInvested'].iloc[-1], df['BTCHodl'].iloc[-1], df['TotalBalanceHodl'].iloc[-1], df['Hodl'].iloc[-1])
            
dfResult = pd.DataFrame(lst, columns = ['Statistics', 'Values' ])

# Create df with just Trasanctions made
dfTransactions = df.loc[df["OrderType"] != 'No Trx']

# Convert df to xlsx File
df.to_excel(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\BacktestTransactions.xlsx")
    

################### Plot ###########################

df = df.set_index("Date")
fig = go.Figure()
xaxis = df.index
fig.add_trace(go.Scatter(x=xaxis, 
                         y=df['totalBTC'], 
                         name="Total BTC",
                         yaxis="y2",
                         line=dict(color="black")
                         ))
                         
fig.add_trace(go.Scatter(x=xaxis,
                         y=df['totalBalance'], 
                         name="Total Balance",
                         yaxis="y4",
                         line=dict(color="gold")
                         ))
                         
fig.add_trace(go.Scatter(x=xaxis, 
                         y=df['TotalProfit'], 
                         name="Profit Sales",
                         line=dict(color="brown")
                         ))
                         
fig.add_trace(go.Scatter(x=xaxis, 
                         y=df['TotalValue'], 
                         name="Total",
                         line=dict(color="green")
                         ))
                         
fig.add_trace(go.Scatter(x=xaxis, 
                         y=df['Hodl'], 
                         name="Hodl Value",
                         line=dict(color="yellow")
                         ))

fig.add_trace(go.Scatter(x=xaxis, 
                         y=df['BTCHodl'], 
                         name="BTC Hodl",
                         yaxis="y2",
                         line=dict(color="blue")
                         ))                         
                         
fig.add_trace(go.Scatter(x=xaxis, 
                         y=df['avg'],                                                  
                         name="Risk",
                         yaxis="y3",
                         line=dict(color="red")                                                 
                         ))

fig.update_layout(
    xaxis=dict(
        domain=[0.02, 0.9]
    ),
    yaxis=dict(
        title="Total Balance",
        titlefont=dict(
            color="black"
        ),
        tickfont=dict(
            color="black"
        )
    ),
    yaxis2=dict(
        title="Total BTC",
        titlefont=dict(
            color="black"
        ),
        tickfont=dict(
            color="black"
        ),
        anchor="y2",
        overlaying="y",
        side="right",
        position=0.94
        
    ),

    yaxis3=dict(
        title="Risk",
        titlefont=dict(
            color="red"
        ),
        tickfont=dict(
            color="red"
        ),
        anchor="y3",
        overlaying="y",
        side="right",

    ),
    yaxis4=dict(
        title="DCA Balance",
        titlefont=dict(
            color="gold"
        ),
        tickfont=dict(
            color="gold"
        ),
        anchor="y4",
        overlaying="y",
        side="right",
        position=0.98

    )     
)    

# Update layout properties
fig.update_layout(
    legend_y=0.95,
    margin_t=0,
    margin_l=0,
    height=500,
    width=910
)


st.header(model + " Test Chart: " + f"{df.index.date[0]}" + f" / {df.index.date[-1]}\n")
st.plotly_chart(fig)

################### Statistics and Dataset ###########################

st.subheader("Results at date: " + f"{df.index.date[-1]}\n")
st.table(dfResult)

st.subheader("Detailed Transaction Dataset\n")
AgGrid(df.reset_index(), height=500)
