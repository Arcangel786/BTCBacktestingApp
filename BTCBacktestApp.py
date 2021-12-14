
import datetime
from st_aggrid import AgGrid
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, datetime

import warnings
warnings.filterwarnings('ignore')


now = datetime.now()


################### Declaration of Functions ###########################

def getInput():
    
    start_date = st.sidebar.text_input("Start Date", "2013-04-17")
    end_date = st.sidebar.text_input("End Date", now.date())
    model = st.sidebar.selectbox(
        "Select model to test", ("BitcoinRaven Old Model", "BitcoinRaven New Model", "Jay's Model", "Ben's Model")
    )
    freqDCA = st.sidebar.selectbox(
        "Select DCA frequency", ("Weekly", "Daily", "Monthly")
    )
    DCA = st.sidebar.number_input("DCA to invest periodically",min_value=0,value=200)
    initCapital = st.sidebar.number_input("Initial Capital to invest",min_value=0,value=35000)
    tokenUnits = st.sidebar.number_input("Divide current Total BTC in portions before transaction",min_value=0,value=100)
    y1 = st.sidebar.number_input("Portions to sell at 0.6-0.7 risk",min_value=0,max_value=tokenUnits,value=1)
    y2 = st.sidebar.number_input("Portions to sell at 0.7-0.8 risk",min_value=0,max_value=tokenUnits,value=2)
    y3 = st.sidebar.number_input("Portions to sell at 0.8-0.9 risk",min_value=0,max_value=tokenUnits,value=6)
    y4 = st.sidebar.number_input("Portions to sell at > 0.9 risk",min_value=0,max_value=tokenUnits,value=50)
    balanceUnits = st.sidebar.number_input("Divide Total balance in portions before transaction",min_value=0,value=10)
    x1 = st.sidebar.number_input("Portions to buy at 0.3-0.5 risk",min_value=0,max_value=balanceUnits,value=1)
    x2 = st.sidebar.number_input("Portions to buy at 0.2-0.3 risk",min_value=0,max_value=balanceUnits,value=3)
    x3 = st.sidebar.number_input("Portions to buy at 0.1-0.2 risk",min_value=0,max_value=balanceUnits,value=6)
    x4 = st.sidebar.number_input("Portions to buy > 0.1 risk",min_value=0,max_value=balanceUnits,value=10)

    return start_date, end_date, model, freqDCA, DCA, initCapital, tokenUnits, balanceUnits, y1, y2, y3, y4, x1, x2, x3, x4


def freqSelected(freqDCA):
    
    if (freqDCA == "Daily"):
        return 'D'
    elif (freqDCA == "Weekly"):
        return 'W'
    elif (freqDCA == "Monthly"):
        return 'M'
    else:
        'None'
    

def modelSelected(model):
    
    if (model == "BitcoinRaven Old Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\OldMrisk.csv", usecols=["Date", "Value", "avg"])    
    elif (model == "BitcoinRaven New Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\Mrisk.csv", usecols=["Date", "Value", "avg"])
    elif (model == "Jay's Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\JayRiskMetricBTCAdapted.csv", usecols=["Date", "Value", "avg"]).rename(columns={"Risk": "avg","Price":"Value"})
    elif (model == "Ben's Model"):
        return pd.read_csv(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\BenRiskMetricBTCAdapted.csv", usecols=["Date", "Value", "avg"])
    else:
        'None'
         

def sell(transactionAmount, price, totalBalance, totalBTC):
    BTCTraded = transactionAmount * price
    totalBalance = totalBalance + BTCTraded
    totalBTC = totalBTC - transactionAmount
    return totalBalance, totalBTC

def buy(transactionAmount,price, totalBalance, totalBTC):
    BTCTraded = transactionAmount / price
    totalBalance = totalBalance - transactionAmount
    totalBTC = totalBTC + BTCTraded
    return totalBalance, totalBTC

def Ratio(avg, signal, price, totalBalance, totalBTC, tokenUnits, balanceUnits, y1, y2, y3, y4, x1, x2, x3, x4):

    if signal == "Sell":       
        if totalBTC != 0:
            # Modify to set selling amount
            transactionAmount = totalBTC / tokenUnits
            if 0.6 < avg <= 0.7:
                transactionAmount = transactionAmount * y1
                totalBalance,totalBTC = sell(transactionAmount, price, totalBalance, totalBTC)            
            elif 0.7 < avg <= 0.8:
                transactionAmount = transactionAmount * y2
                totalBalance, totalBTC = sell(transactionAmount, price, totalBalance, totalBTC)
            elif 0.8 < avg <= 0.9:
                transactionAmount = transactionAmount * y3
                totalBalance, totalBTC = sell(transactionAmount, price, totalBalance, totalBTC)
            elif avg > 0.9:
                transactionAmount = transactionAmount * y4
                totalBalance, totalBTC = sell(transactionAmount, price, totalBalance, totalBTC)

    elif signal == "Buy":
        if totalBalance != 0:
            transactionAmount = totalBalance / balanceUnits
            
            if 0.3 < avg <= 0.5:
                transactionAmount = transactionAmount * x1
                totalBalance, totalBTC = buy(transactionAmount, price, totalBalance, totalBTC)
                
            elif 0.2 < avg <= 0.3:
                transactionAmount = transactionAmount * x2
                totalBalance, totalBTC = buy(transactionAmount, price, totalBalance, totalBTC)
            elif 0.17 < avg <= 0.2:
                transactionAmount = transactionAmount * x3
                totalBalance, totalBTC = buy(transactionAmount, price, totalBalance, totalBTC)
            elif avg <= 0.17:
                
                transactionAmount = transactionAmount * x4
                totalBalance, totalBTC = buy(transactionAmount, price, totalBalance, totalBTC)
                
    elif signal == "No Trx":
        pass
    
    elif signal == "BottomBuy":    
        if totalBalance != 0:
            # Modify to set buying amount
            transactionAmount = totalBalance  
            totalBalance, totalBTC = buy(transactionAmount, price, totalBalance, totalBTC)
    
    return totalBalance, totalBTC


################### Getting variables values ###########################

start, end, model, freqDCA, DCA, initCap, tokenUnits, balanceUnits, y1, y2, y3, y4, x1, x2, x3, x4 = getInput()
date_time = now.strftime("%d/%m/%Y, %H:%M:%S")


################### Displaying Streamlit headers ###########################

st.write(
    """
 # Risk Metric Backtesting
 
 **Select different models and Values to test.**
 """
 )
    
st.sidebar.header('User Input')
st.write("Test for:", model, " at: ", date_time)


################### Dataframe Setup ###########################
df = modelSelected(model)

df["Date"] = pd.to_datetime(df["Date"])

# Date range
df = df[df.Date > pd.to_datetime(start)]
df = df[df.Date < pd.to_datetime(end)]

# DCA frequency set M, W, D
df = df.set_index("Date").resample(freqSelected(freqDCA)).mean() 



################### Initiallisation Columns ###########################

# Rounds price value to 2 decimal places
df["Value"] = round(df["Value"],2) 

# Rounds risk value to 3 decimal places
df["avg"] = round(df["avg"],3)

# Dollar Cost Average to invest periodically
df["DCA"] =""
df["DCA"] = DCA

df["OrderType"] = ""

df["BalanceBeforeTrx"] =""
df["BalanceBeforeTrx"].iloc[0] = 0

df["transactionAmount"] =""
df["transactionAmount"].iloc[0] = 0

# initial capital in dollars
df["totalBalance"] =""
df["totalBalance"].iloc[0] = initCap

df["% TrxOfTotal $"] = ""
df["% TrxOfTotal $"].iloc[0] = 0

df["TokenBeforeTrx"] =""
df["TokenBeforeTrx"].iloc[0] = 0

df["tokenTraded"] = ""
df["tokenTraded"].iloc[0] = 0

# initial capital in token
df["totalBTC"] =""
df["totalBTC"].iloc[0] = 0

df["% TrxOfTotal Token"] = ""
df["% TrxOfTotal Token"].iloc[0] = 0

# total combined between total balance of dollars plus total current value of tokens
df["TotalValue"] = ""
df["TotalValue"].iloc[0] = ((df['Value'].iloc[0]) * (df['totalBTC'].iloc[0])) + df['totalBalance'].iloc[0]

df["TotalInvested"] = ""
df["TotalInvested"] = df["totalBalance"].iloc[0]

df["Hodl"] = (df["totalBalance"].iloc[0] / df['Value'].iloc[0]) * df['Value']


################### Dataframe Population ###########################
flag = 0
for i in range(1, df.shape[0]):
    if df["avg"][i] < 0.17 and flag == 0:        
        signal = "BottomBuy"
        flag = 1        
    elif df["avg"][i] < 0.5 and flag == 1:
            signal = "Buy"
    elif df["avg"][i] > 0.7:
        signal = "Sell"
    else:
        signal ="No Trx"

    df["totalBalance"][i] = round(Ratio(avg=df["avg"][i], signal=signal, price=df["Value"][i], totalBalance=df["totalBalance"][i-1]+df["DCA"][i-1], totalBTC=df["totalBTC"][i-1], tokenUnits = tokenUnits, balanceUnits = balanceUnits, y1 = y1, y2 = y2, y3 = y3, y4 = y4, x1=x1, x2=x2, x3=x3, x4=x4)[0], 2)
    df["transactionAmount"][i] = round((df["totalBalance"][i] - df["DCA"][i-1]) - df["totalBalance"][i-1], 2)   
    df["BalanceBeforeTrx"][i] = round(df["totalBalance"][i] + abs(df["transactionAmount"][i]), 2)  
    df["% TrxOfTotal $"][i] = round((df["transactionAmount"][i] / (df["totalBalance"][i-1] + df["DCA"][i-1])) * 100, 2)
    df["totalBTC"][i] = Ratio(avg=df["avg"][i], signal=signal, price=df["Value"][i], totalBalance=df["totalBalance"][i-1]+df["DCA"][i-1], totalBTC=df["totalBTC"][i-1], tokenUnits = tokenUnits, balanceUnits = balanceUnits, y1 = y1, y2 = y2, y3 = y3, y4 = y4, x1=x1, x2=x2, x3=x3, x4=x4)[1]
    df["tokenTraded"][i] = df["totalBTC"][i] - df["totalBTC"][i-1]    
    df["TokenBeforeTrx"][i] = df["totalBTC"][i] + abs(df["tokenTraded"][i])
    
    try:
        df["% TrxOfTotal Token"][i] = round((df["tokenTraded"][i] / df["totalBTC"][i - 1]) * 100, 2)
    except ZeroDivisionError:
        pass
    
    df["TotalValue"][i] = round(((df['Value'][i])*(df['totalBTC'][i])) + df['totalBalance'][i],2)
    df["TotalInvested"][i] = df["TotalInvested"][i-1] + df["DCA"][i]
    df["OrderType"][i] = signal


lst = [[f"Total BTC:", round((df['totalBTC'].iloc[-1]),3)], [f"Total Balance:",round(df['totalBalance'].iloc[-1],2)], [f"Total Portfolio:",round(df['TotalValue'].iloc[-1],2)], 
            [f"Risk:",round(df['avg'].iloc[-1],2)], [f"Last BTC price:", round(df['Value'].iloc[-1],2)]]
dfResult = pd.DataFrame(lst, columns = ['Statistics', 'Values' ])

# Create df with just Trasanctions made
dfTransactions = df.loc[df["OrderType"] != 'No Trx']

# Convert df to xlsx File
#df.to_excel(r"C:\Users\ideal\Desktop\Data Analysis with Python\Backtesting\Datasets\BacktestTransactions.xlsx")
    
################### Plot ###########################

fig = make_subplots(specs=[[{"secondary_y": True}]])
xaxis = df.index
fig.add_trace(go.Scatter(x=xaxis, y=df['totalBTC'], name="Total BTC", line=dict(color="black")), secondary_y=True)
fig.add_trace(go.Scatter(x=xaxis, y=df['totalBalance'], name="Total Balance", line=dict(color="gold")))
fig.add_trace(go.Scatter(x=xaxis, y=df['TotalValue'], name="Total", line=dict(color="green")))
fig.add_trace(go.Scatter(x=xaxis, y=df['Hodl'], name="Hodl", line=dict(color="yellow")))

fig.update_xaxes(title="Date", row=1, col=1)
fig.update_yaxes(title="Total Balance", showgrid=False)
fig.update_yaxes(title="Total BTC", showgrid=True, secondary_y=True)
fig.update_layout(template="plotly_dark")

st.header(model + " Test Chart \n")
st.plotly_chart(fig)

################### Statistics and Dataset ###########################

st.header("Results at date: " + f"{df.index.date[-1]}\n")
st.table(dfResult)


st.header("Detailed Transaction Dataset\n")
AgGrid(df.reset_index(), height=500)