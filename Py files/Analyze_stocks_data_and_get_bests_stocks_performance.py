#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import os
import time
import pickle
import json
from bs4 import BeautifulSoup
import requests
# !pip install yfinance
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn


# In[4]:


cwd = os.getcwd()


# ## Create dataframe of all stocks data from the funds' data we scraped (by selected dates)

# In[12]:


def creat_all_stocks_data(cik_list,columns_input, agg_dict,start_date,end_date):
    
    all_stocks_df = pd.DataFrame(columns=columns_input)
    
    rows = []
    
    for cik in cik_list:
        try: 
            path = cwd+'/Data/{0}'.format(cik)
            stock_df_file = path + f'/{cik}_stocks_df.csv'    
            stock_df = pd.read_csv(stock_df_file, index_col=0)
            stock_df = stock_df[(stock_df.report_date>=start_date)&(stock_df.report_date<=end_date)].reset_index()
            df_stock_agg = stock_df.groupby(["nameOfIssuer","titleOfClass","cusip"],as_index=False).agg(agg_dict)
            rows.append(df_stock_agg)
        
        except:
            print(f'{cik} not in df_stock_agg')
            return False
            pass
        
        
        
    all_stocks_df = pd.concat(rows,ignore_index=True)
    all_stocks_df.to_csv('all_stocks_df.csv')
    return all_stocks_df


# In[ ]:


#Bring errors from Final CIK Scraping notebook:
error_list = ["1340807", "313028", "1140804", "1595082", "884566", "1377581", "860643", "813917", "1177206", "922898","1040197", "912938", "1521001", "1112325", "1006378", "807985", "902219"]

#Create the updated list of ciks
cik_df = pd.read_excel("CIK-list.xlsx")

cik_list = [str(x) for x in cik_df["CIK"] if str(x) not in error_list]


# In[14]:


len(cik_list)


# In[9]:


cols_dict = {"holding_duration":"mean",
 "holding_proportion":"mean",
 "portfolio_duration":"mean",
 "Profit":"mean",
 "yield_from_last_report":"mean",
 'yield_from_1_year':"max",
 'yield_from_3_year':"max",
 'yield_from_continuous_profit':"max",
 "bought_times":"sum"}


# In[10]:


cols = ["nameOfIssuer","titleOfClass","cusip","report_date"] + list(cols_dict.keys()) 


# In[11]:


cols


# In[17]:


get_ipython().run_cell_magic('time', '  ', 'main_stock_df = creat_all_stocks_data(cik_list,cols, cols_dict,"2017-12-30","2018-06-30")')


# In[19]:


main_stock_df


# ## Use Yahoo's data to show the performance of best stocks

# In[20]:


cols_dict_top_20 = {"holding_duration":"mean",
 "holding_proportion":"mean",
 "portfolio_duration":"mean",
 "Profit":"mean",
 "yield_from_last_report":"mean",
 'yield_from_1_year':"mean",
 'yield_from_3_year':"mean",
 'yield_from_continuous_profit':"mean",
 "bought_times":"mean"}


# In[21]:


def get_symbol(company):
    try:
        company_name = company.strip()
        url = "https://www.marketwatch.com/tools/quotes/lookup.asp?siteID=mktw&Lookup={}&Country=us&Type=All".format(company_name)
        result = requests.get(url)
        soup = BeautifulSoup(result.content.decode(),features='lxml').find_all('div',{"class":"results"},href=False)
        df = pd.read_html(str(soup))[0]
        return df['Symbol'][0]
    except:
        return "not_found"


# In[46]:


def create_top_20_dfs(df_all_stocks,best_of,agg_dict,start_date,end_date,top_y_graph=1000):
    """
    Build top 20 stocks df by selected column
    """
    best_of_col = best_of
   
    top_stocks = df_all_stocks.groupby(["nameOfIssuer","titleOfClass","cusip"],as_index=False).agg(agg_dict)
    top_stocks = top_stocks.sort_values(best_of_col, ascending = False).reset_index(drop=True)
    top_20_stocks = top_stocks[0:20].copy()
    top_20_stocks.to_csv(f'top_20_stocks_by_{best_of_col}.csv')
    
    """
    Add ticker symbol
    """
    
    top_20_stocks['ticker'] = top_20_stocks["nameOfIssuer"].apply(get_symbol)
    
    ticker_list = list(top_20_stocks['ticker']) 
#     ticker_list.append("^GSPC") #add s&p500
    graph_ticker_list = []
    
    # ticker_list
    for i in ticker_list:
        if i != "not_found":
            graph_ticker_list.append(i)
    """
    Use tickers for historical data from Yahoo
    """
    
    yf_df = pd.DataFrame()
    for i in graph_ticker_list:
        try:
            tickerSymbol = i
            if "." in tickerSymbol:
                tickerSymbol = tickerSymbol.replace('.', '-')
            #get data on this ticker
            tickerData = yf.Ticker(tickerSymbol)
            #get the historical prices for this ticker
            tickerDf = tickerData.history(period='1d', start=start_date, end=end_date).reset_index()
            tickerDf['ticker'] = tickerSymbol
            
            for i in range(1,len(tickerDf)):
                tickerDf.loc[i,'Close_Changed'] =  round((tickerDf.loc[i,'Close']-tickerDf.loc[i-1,'Close'])/tickerDf.loc[i-1,'Close'],4)
            
            yf_df = pd.concat([yf_df, tickerDf], ignore_index=True)

        except:
            pass
    
    yf_df = yf_df.fillna(0)
        
    """
    Plot stocks data
    """
    graph = yf_df.groupby(['Date', 'ticker'])['Close'].max().unstack().plot(figsize=[15,9],xlabel='Time period by day',ylabel='Close rate',ylim=(0,top_y_graph))#,title=f'Best stocks by {best_of_col}')

    plt.savefig(f'Best stocks by {best_of_col}.png')
    
    print("Top 20 stocks by ", best_of_col)
    print(graph_ticker_list)
    return top_20_stocks,yf_df, graph


# In[47]:


best_of_col_out = "bought_times"
top_stocks,yf_df,graph = create_top_20_dfs(main_stock_df,best_of_col_out,cols_dict_top_20,"2018-06-30","2021-04-01", 1500)


# In[44]:


top_stocks


# In[ ]:




