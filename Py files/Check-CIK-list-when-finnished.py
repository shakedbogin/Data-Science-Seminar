#!/usr/bin/env python
# coding: utf-8

# In[6]:


import pandas as pd
import numpy as np
import os


# In[45]:


cik_df = pd.read_excel("CIK-list.xlsx")
cik_df


# In[46]:


cwd = os.getcwd()


# In[49]:


for i in range(0,len(cik_df['CIK'])):
    cik = str(cik_df.loc[i,'CIK'])
    path = cwd+r'\\Data\\{0}'.format(cik)
    df_details = path + f'\\{cik}_df_details.csv' 
    df_HF = path + f'\\{cik}_df_HF.csv'
    stock_df = path + f'\\{cik}_stocks_df.csv'

    if os.path.exists(df_details):
        df_details = pd.read_csv(df_details, index_col=0)
        sum_status = sum(df_details["Status_main"]) + sum(df_details["Status_table"])
        if sum_status == 0:
            cik_df.loc[i,'df_details'] = 1
        else:
            cik_df.loc[i,'df_details'] = 0
    else:
        cik_df.loc[i,'df_details'] = 0
       
    if os.path.exists(df_HF):
        df_HF = pd.read_csv(df_HF, index_col=0)
        if len(df_HF)>1:
            cik_df.loc[i,'df_HF'] = 1
            
        else:
            cik_df.loc[i,'df_HF'] = 0
    else:
        cik_df.loc[i,'df_HF'] = 0
        
    
    
    if os.path.exists(stock_df):
        cik_df.loc[i,'stock_df'] = 1
        
    else:
        cik_df.loc[i,'stock_df'] = 0


# In[43]:


cik_df


# In[48]:


cik_df.to_excel('check-cik.xlsx')


# In[ ]:




