#!/usr/bin/env python
# coding: utf-8

# In[44]:


import pandas as pd
import numpy as np
import os
import time
import pickle
import json
from bs4 import BeautifulSoup
import requests
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn
# !pip install yfinance


# In[45]:


cwd = os.getcwd()


# # Create dataframe of all HF filing summary

# In[63]:


def create_funds_df(cik):
    """
    Check if cik is already in the funds df - it will help us when adding ciks to the list.
    """
    if os.path.isfile('Data/funds_df.csv'):
        df_to_check_in = pd.read_csv('Data/funds_df.csv')
        ciks_in_df = list(df_to_check_in.CIK.astype('str').unique())
        if cik in ciks_in_df:
            return False
        
    """
    Find fund's df_HF and stocks_df files
    """
    path = cwd+f'/Data/{cik}'
    initial_df_file = path + f'/{cik}_df_HF.csv'
    initial_df = pd.read_csv(initial_df_file, index_col=0)
    stocks_df_file = path + f'/{cik}_stocks_df.csv'
    stocks_df = pd.read_csv(stocks_df_file, index_col=0)
    
    """
    create funds_df
    """
    funds_df = initial_df.groupby(['CIK', 'periodOfReport']).agg({'value': 'sum', 'nameOfIssuer': 'count'})
    funds_df = funds_df.reset_index()
    funds_df = funds_df.rename(columns={'value': 'AUM', 'nameOfIssuer': 'positionsNumber'})
    funds_df['AUM'] = funds_df['AUM'] 
    
    new_columns = ['count_new', 'sum_new', 'count_added_to', 'sum_added_to', 'count_trimmed', 'sum_trimmed',
                   'count_sold_out', 'sum_sold_out', 'bought', 'sold', 'holdings_replacement', 
                   'portfolio_turnover', 'portfolio_duration', 'top_10_holdings', 'yield_from_last_report', 
                   'yield_from_1_year', 'yield_from_3_year']
    for column in new_columns:
        funds_df[column] = 0
        
    """
    calculate portfolio_duration
    """
    protfolio_duration_by_Q = stocks_df.loc[stocks_df.portfolio_duration > 0].groupby(['CIK', 'report_date'])['portfolio_duration'].agg('mean')
    protfolio_duration_by_Q = protfolio_duration_by_Q.reset_index()
    protfolio_duration_by_Q = protfolio_duration_by_Q.rename(columns={'report_date': 'periodOfReport'})
    funds_df.portfolio_duration = round(protfolio_duration_by_Q.portfolio_duration[protfolio_duration_by_Q.periodOfReport == funds_df.periodOfReport], 3)
    
    
    """
    pivot(sum) on stocks_df by Q
    """
    stocks_df_by_Q = pd.pivot_table(stocks_df, index=['CIK', 'report_date'],
                                    values=['New', 'AddedTo', 'Trimmed', 'SoldOut'],
                                    aggfunc='sum')
    stocks_df_by_Q = stocks_df_by_Q.reset_index()
    stocks_df_by_Q = stocks_df_by_Q.rename(columns={'report_date': 'periodOfReport'})
    
    """
    from pivot(sum) to funds columns
    """
    funds_df.sum_new = stocks_df_by_Q.New[stocks_df_by_Q.periodOfReport == funds_df.periodOfReport]
    funds_df.sum_added_to = round(stocks_df_by_Q.AddedTo[stocks_df_by_Q.periodOfReport == funds_df.periodOfReport], 2)
    funds_df.sum_trimmed = round(stocks_df_by_Q.Trimmed[stocks_df_by_Q.periodOfReport == funds_df.periodOfReport], 2)
    funds_df.sum_sold_out = stocks_df_by_Q.SoldOut[stocks_df_by_Q.periodOfReport == funds_df.periodOfReport]
#     funds_df.portfolio_duration = round(stocks_df_by_Q.portfolio_duration[stocks_df_by_Q.periodOfReport == funds_df.periodOfReport], 2)

    
    """
    pivot(count) on stocks_df by Q
    """
    counts_table = pd.pivot_table(stocks_df, index=['CIK', 'report_date'], 
                                  values=['New', 'AddedTo', 'Trimmed', 'SoldOut'],
                                  aggfunc= lambda x: (x>0).sum())
    counts_table = counts_table.reset_index()
    counts_table = counts_table.rename(columns={'report_date': 'periodOfReport'})
    
    """
    from pivot(count) to funds columns
    """
    funds_df.count_added_to = counts_table.AddedTo[counts_table.periodOfReport == funds_df.periodOfReport]
    funds_df.count_trimmed = counts_table.Trimmed[counts_table.periodOfReport == funds_df.periodOfReport]
    funds_df.count_new = counts_table.New[counts_table.periodOfReport == funds_df.periodOfReport]
    funds_df.count_sold_out = counts_table.SoldOut[counts_table.periodOfReport == funds_df.periodOfReport]
    
    """
    calculate bought and sold
    """
    funds_df.bought = round(funds_df.sum_new + funds_df.sum_added_to, 2)
    funds_df.sold = round(funds_df.sum_sold_out + funds_df.sum_trimmed, 2)
    funds_df.holdings_replacement = funds_df[['bought','sold']].min(axis=1)
    
    """
    calculate portfolio_turnover
    """
    for i in range(1, len(funds_df)):
        if funds_df.loc[i, 'AUM'] + funds_df.loc[i-1, 'AUM'] > 0:
            funds_df.loc[i, 'portfolio_turnover'] = round(funds_df.loc[i, 'holdings_replacement'] / ((funds_df.loc[i, 'AUM'] + funds_df.loc[i-1, 'AUM'])/2), 2)
            
    """
    funds' Yield
    """ 
    for i in range(1, len(funds_df)):
        funds_df.loc[len(funds_df)-i, 'yield_from_last_report'] = round((funds_df.loc[len(funds_df)-i, 'AUM']-funds_df.loc[len(funds_df)-i, 'bought']+funds_df.loc[len(funds_df)-i, 'sold'])/funds_df.loc[len(funds_df)-i-1, 'AUM']-1, 2)


    for i in range(1, len(funds_df)):
        if len(funds_df)-i-4 > 0:
            funds_df.loc[len(funds_df)-i, 'yield_from_1_year'] = round((funds_df.loc[len(funds_df)-i, 'AUM']-funds_df.loc[len(funds_df)-i, 'bought']+funds_df.loc[len(funds_df)-i, 'sold'])/funds_df.loc[len(funds_df)-i-4, 'AUM']-1, 2)


    for i in range(1, len(funds_df)):
        if len(funds_df)-i-12 > 0:
            funds_df.loc[len(funds_df)-i, 'yield_from_3_year'] = round((funds_df.loc[len(funds_df)-i, 'AUM']-funds_df.loc[len(funds_df)-i, 'bought']+funds_df.loc[len(funds_df)-i, 'sold'])/funds_df.loc[len(funds_df)-i-12, 'AUM']-1, 2)

    """
    top 10 holdings
    """
    top10_holding = stocks_df.groupby('report_date')['holding_proportion'].nlargest(10).sum(level=0).to_frame().reset_index()
    funds_df.top_10_holdings = round(top10_holding['holding_proportion'][top10_holding.report_date == funds_df.periodOfReport], 2)  
    
    """
    funds_df to csv
    """
    funds_df['AUM'] = funds_df['AUM']/1000000 #In Milloins
    with open('Data/funds_df.csv', 'a') as f:
        funds_df.to_csv(f, mode='a', header=f.tell()==0, index=False)
        
    return True


# In[4]:


#Bring errors from Final CIK Scraping notebook:
error_list = ["1340807", "313028", "1140804", "1595082", "884566", "1377581", "860643", "813917", "1177206", "922898","1040197", "912938", "1521001", "1112325", "1006378", "807985", "902219"]

#Create the updated list of ciks
cik_df = pd.read_excel("CIK-list.xlsx")

cik_list = [str(x) for x in cik_df["CIK"] if str(x) not in (error_list)]


# In[5]:


len(cik_list)


# In[7]:


error_list_funds = []


# In[8]:


get_ipython().run_cell_magic('time', '', 'for cik in cik_list:\n    try:\n        if create_funds_df(cik) is True:\n            print(cik, "added to funds_df")\n        else:\n            print(f\'{cik} already in file\')\n         \n    except: \n        error_list_funds.append(cik)\n        print(f"couldn\'t add {cik} to funds_df")\n        pass')


# In[84]:


error_list_funds


# In[4]:


funds_df = pd.read_csv('Data/funds_df.csv')


# In[6]:


cols = list(funds_df.columns)
# cols


# In[205]:


cols_dict_top_20_funds = {"AUM":"mean",
 "positionsNumber":"mean",
 "portfolio_turnover":"mean",
 "portfolio_duration":"mean",
 "top_10_holdings":"mean",
 "yield_from_last_report":"mean",
 'yield_from_1_year':"mean",
 'yield_from_3_year':"mean"}


# In[206]:


def create_top_20_funds_dfs(df_all_funds,best_of,top_buttom,columns_input,agg_dict):
    
    cols_names = columns_input
    
    best_of_col = best_of
   
    top_funds = df_all_funds.groupby(["CIK"],as_index=False).agg(agg_dict)
    top_funds = top_funds.round(decimals=2)
    top_funds = top_funds.sort_values(best_of_col, ascending = top_buttom).reset_index(drop=True)
        

    top_funds.to_csv(f'top_funds_by_{best_of_col}.csv')
    print("Top 20 funds by ", best_of_col)
    return top_funds[0:10]


# In[207]:


best_of_column = "AUM"
top_buttom_best = False
top_funds = create_top_20_funds_dfs(funds_df,best_of_column,top_buttom_best,cols,cols_dict_top_20_funds)


# In[208]:


top_funds


# In[ ]:





# ## Use the functions from the best stocks notebook to collect stocks data and find best stocks by the best funds list

# In[213]:


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


# In[209]:


cols_dict = {"holding_duration":"mean",
 "holding_proportion":"mean",
 "portfolio_duration":"mean",
 "Profit":"mean",
 "yield_from_last_report":"mean",
 'yield_from_1_year':"max",
 'yield_from_3_year':"max",
 'yield_from_continuous_profit':"max",
 "bought_times":"sum"}


# In[210]:


cols = ["nameOfIssuer","titleOfClass","cusip","report_date"] + list(cols_dict.keys()) 


# In[211]:


cik_list_from_top_funds = list(top_funds["CIK"])


# In[212]:


cik_list_from_top_funds


# In[214]:


get_ipython().run_cell_magic('time', '', 'main_stock_df = creat_all_stocks_data(cik_list_from_top_funds,cols, cols_dict,"2017-12-30","2018-06-30")')


# In[215]:


main_stock_df


# ## Use Yahoo's data to show the performance of best stocks
# 

# In[217]:


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


# In[221]:


def create_top_20_dfs(df_all_stocks,best_of,agg_dict,start_date,end_date,top_y_graph=1000):
    """
    Build top 20 stocks df by selected column
    """
    best_of_col = best_of
   
    top_stocks = df_all_stocks.groupby(["nameOfIssuer","titleOfClass","cusip"],as_index=False).agg(agg_dict)
    top_stocks = top_stocks.sort_values(best_of_col, ascending = False).reset_index(drop=True)
    top_20_stocks = top_stocks[0:15].copy()
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
    
    print("Top 10 stocks by ", best_of_col)
    print(graph_ticker_list)
    return top_20_stocks,yf_df, graph


# In[216]:


cols_dict_top_20 = {"holding_duration":"mean",
 "holding_proportion":"mean",
 "portfolio_duration":"mean",
 "Profit":"mean",
 "yield_from_last_report":"mean",
 'yield_from_1_year':"mean",
 'yield_from_3_year':"mean",
 'yield_from_continuous_profit':"mean",
 "bought_times":"mean"}


# In[222]:


best_of_col_out = "bought_times"
top_stocks_by_top_funds,yf_df, graph = create_top_20_dfs(main_stock_df,best_of_col_out,cols_dict_top_20,"2018-06-30","2021-04-01", 600)


# In[223]:


top_stocks_by_top_funds


# In[ ]:




