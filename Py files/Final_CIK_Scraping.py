#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
# import requests
from bs4 import BeautifulSoup
import re
import os
import time
from random import randint
import xml.etree.ElementTree as et 
import feedparser
import webbrowser
import glob
from collections import defaultdict
from requests_html import HTMLSession
import random
import numpy as np

headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"}
sleep_time = random.randint(1, 11)


# In[2]:


# !pip install requests-html
def check_file_exists(cik, file):
    if(os.path.exists(file)):
        return True
    return False


# In[3]:


cwd = os.getcwd()


# # Open repository by Company CIK & make details df

# In[4]:


'''
Method that get the cik infomation/data from the SEC website and write them to excel details file per cik
'''

def get_files_details(cik):
    print(f"Started Updating df_details for {cik}")
    requests = HTMLSession()

    page = f'https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK={cik}&type=13F-HR&owner=exclude&count=20' #from 2017

    #request the link to the main page of the HF company and find all files urls
    response1 = requests.get(page,headers=headers)
    soup1 = BeautifulSoup(response1.content.decode(),features='xml')
    HF_urls = soup1.findAll("a",href=True)
    file_urls = [x['href'] for x in HF_urls if 'Archives' in x['href']]
    
    #Check if there are files to download
    if len(file_urls)==0: 
        return False
    
    #Preapare a directory with the name of the cik of the HF company
    directory = f"{cik}"    # Directory
    parent_dir = r"Data"    # Parent Directory path
    path = os.path.join(parent_dir, directory)
    
    #Check if the folder exists if not create it
    if not os.path.exists(path):
        os.makedirs(path)
    
    #Prepare the file header
    df_cols = ["CIK", "main_doc_web_link", "table_doc_web_link", "main_name", "table_name", "Status_main", "Status_table"]
    rows = []

    #prepare the file details path
    df_details_file = f'{path}'+ "\\" + f'{cik}_df_details.csv'
    
    #check if df_details exists
    if os.path.exists(df_details_file):
        #if exists read it
        df_details = pd.read_csv(df_details_file, dtype ={"Status_main":'int', "Status_table":'int'},index_col=0)
    else:
        #create empty one
        df_details = pd.DataFrame(columns = df_cols)

          
    #loop through files links
    for link in file_urls:
        #create a url link
        file_url = 'https://www.sec.gov' + f'{link}'
        
        #request the files
        response2 = requests.get(file_url,headers=headers)       
        soup2 = BeautifulSoup(response2.content.decode(),features='xml')
        urls_xmls = soup2.findAll("a",href=True)

        #get file id name
        xml_primary_doc_name = [x['href'].split("/")[5] for x in urls_xmls if 'Archives' in x['href']][1]
        
        #treate with the primary doc link
        xml_primary_doc_link = [x['href'] for x in urls_xmls if 'Archives' in x['href']][1] 
        main_file = r'{0}\{1}\{2}_main.xml'.format(cwd,path, xml_primary_doc_name)

        #treate with the main table link
        xml_main_table_link = [x['href'] for x in urls_xmls if 'Archives' in x['href']][3]

        #get the cik info to add to df_details file
        main_doc_web_link = f"https://www.sec.gov/{xml_primary_doc_link}"
        table_doc_web_link = f"https://www.sec.gov/{xml_main_table_link}"
        main_name = f"{xml_primary_doc_name}_main.xml" 
        table_name = f"{xml_primary_doc_name}_table.xml" 

        #If filings was exists at df_details skip it else add it df_details
        if main_name in df_details.main_name:
            pass
        
        #new data will be added to df_details
        rows.append({"CIK": cik, "main_doc_web_link": main_doc_web_link, "table_doc_web_link": table_doc_web_link, 
                        "main_name":main_name, "table_name":table_name, "Status_main":1, "Status_table":1})
        
    #update the df_details with the data
    df_details = pd.DataFrame(rows, columns = df_cols)
    
    #export the df_details to file
    df_details.to_csv(f'{path}'+ "\\" + f'{cik}_df_details.csv')
    print(f"Done df_details for {cik}")
   
    return True


# # Download files and check them

# In[5]:


'''
Method that downloads the files & check that they are not corrupted files,
by reading partial fields from the xml fields successfully after download it to the server/pc.
'''
def download_files_and_try_read(cik):
    print(f"Started download_files_and_try_read for {cik}")
    
    #Set the max number of download file tries
    Max_Tries = 5
    
    #Create path to cik files
    path = cwd+r'\Data\{0}'.format(cik)
    df_details_file = path + f'\\{cik}_df_details.csv'    
    
    #Check if the df_details file exists
    if os.path.exists(df_details_file) == False:
        print('df_details is missing')
        return False
    
    #if df_details file exists read it
    df_details = pd.read_csv(df_details_file, dtype ={"Status_main":'int', "Status_table":'int'},index_col=0)
    
    #loop over all the information that exists at the df_details file
    for i in range(0,len(df_details)):
        '''
        main file
        '''
        #treat with the main doc web link 
        if df_details.loc[i, "Status_main"] > 0:
            main_file_name = df_details['main_name'][i]
            main_file_link = df_details['main_doc_web_link'][i]
            main_file = path + "\\" + main_file_name
            
            a=df_details.loc[i, "Status_main"]
            while a < Max_Tries:
                try:
                    #if os.path.exists(main_file): no need to check and throw exception
                    #if the file not exist start first download
                    in_main_file = open(main_file,"r")
                    contents = in_main_file.read()
                    soup = BeautifulSoup(contents,'xml') 
                    #if the file exists read the xml nodes
                    period = soup.find("periodOfReport").get_text()
                    #if the file exists and it is in correct format, update the parameters to exit from the while loop
                    a = Max_Tries
                    #update the Status_main at the df details to 0 (Success & in Correct format file)
                    df_details.loc[i, "Status_main"] = 0
                    #print success message
                    #print("main file success ", main_file_name)                    
                except:
                    #if file not exist or the file downloaded corrupted try to download it again till you reach the max tries
                    if a < Max_Tries:
                        #open session
                        requests = HTMLSession()
                        #request the url
                        download_xml_main = requests.get(f'{main_file_link}')
                        #open a write socket to write the requested result to a file
                        with open(main_file, 'w+b') as file:
                            #write the data to the file
                            file.write(download_xml_main.content)
                    #if we reach the maximum tries and we still didn't success to download the file in correct format
                    if a==Max_Tries:
                        #write an error message
                        print(f"error reading main file {main_file_name}")
                    #update the tries data
                    a+=1
                    df_details.loc[i, "Status_main"] +=1
                    
        '''
        table file (the same logic like main file)
        '''
        if df_details.loc[i, "Status_table"] > 0:
            table_file_name = df_details['table_name'][i]
            table_file_link = df_details['table_doc_web_link'][i]
            table_file = path + "\\" + table_file_name
            b=df_details.loc[i, "Status_table"]
            while b < Max_Tries:
                try:
                    #check if file exists
                    #if os.path.exists(table_file):
                    in_table_file = open(table_file,"r")
                    table_content = in_table_file.read()
                    soup = BeautifulSoup(table_content,'xml')                                
                    nameOfIssuers = soup.find_all('nameOfIssuer')
                    #print(nameOfIssuers)
                    for j in nameOfIssuers:
                        nameOfIssuer = str.rstrip(j.get_text())
                        #print(nameOfIssuer)
                        #print("table file success ",table_file_name)
                    b=Max_Tries
                    df_details.loc[i, "Status_table"] = 0

                except:          
                    if b < Max_Tries:
                        requests = HTMLSession()
                        xml_main_table = requests.get(f'{table_file_link}') #
                        with open(table_file, 'w+b') as file:
                            file.write(xml_main_table.content)
                    
                    if b == Max_Tries:
                        print(f"error reading table file {table_file_name}")
                    
                    b+=1
                    df_details.loc[i, "Status_table"] += 1
    
    
    df_details.to_csv(df_details_file)
    sum_status = sum(df_details["Status_main"]) + sum(df_details["Status_table"])
    print(f"Done second download {cik}, sum_status is {sum_status}")

    return True


# # Build df by CIK

# In[6]:


'''
Method that read the data from the Xml files and create DF with the CIKs data
'''
def from_cik_files_to_df(cik):
    '''
    Read files by df_details
    '''
    path = cwd+r'\Data\{0}'.format(cik)
    df_details_file = path + f'\\{cik}_df_details.csv'
    df_details = pd.read_csv(df_details_file, dtype ={"Status_main":'int', "Status_table":'int'},index_col=0)
    
    df_cols = ["CIK", "vc_name", "vc_country", "periodOfReport", "nameOfIssuer", "titleOfClass", "cusip", "value", 
               "sshPrnamt"]
    rows = []
    
    #Re-validate that the files are readable
    sum_status = sum(df_details["Status_main"]) + sum(df_details["Status_table"])
    
    if sum_status ==0:
        #loop through each file that exist at df_details and collect the data
        for i in range(len(df_details)):
            
            '''
            main file
            '''
            main_file_name = df_details['main_name'][i]
            main_file_link = df_details['main_doc_web_link'][i]
            main_file = path + "\\" + main_file_name
            in_main_file = open(main_file,"r")

            contents = in_main_file.read()
            soup = BeautifulSoup(contents,'xml')
            CIK = soup.find("cik").get_text()
            vc_name = soup.find("name").get_text()
            vc_country = soup.find("stateOrCountry").get_text()
            periodOfReport = soup.find("periodOfReport").get_text()

            '''
            table file 
            '''
            table_file_name = df_details['table_name'][i]
            table_file = path + "\\" + table_file_name 
            in_table_file = open(table_file,"r")
            table_content = in_table_file.read().replace('\n','').replace(' ','')
            soup = BeautifulSoup(table_content,'xml')

            try:     
                nameOfIssuers = soup.find_all('nameOfIssuer')
                titleOfClasss = soup.find_all('titleOfClass')
                cusips = soup.find_all('cusip')
                values = soup.find_all('value')
                shrsOrPrnAmts = soup.find_all('shrsOrPrnAmt')
                sshPrnamts = soup.find_all('sshPrnamt')

                for i in range(len(nameOfIssuers)):  
                    nameOfIssuer = str.rstrip(nameOfIssuers[i].get_text())
                    titleOfClass = str.rstrip(titleOfClasss[i].get_text())
                    cusip = str.rstrip(cusips[i].get_text())
                    value = str.rstrip(values[i].get_text())
                    shrsOrPrnAmt = str.rstrip(shrsOrPrnAmts[i].get_text())
                    sshPrnamt = str.rstrip(sshPrnamts[i].get_text())
                    #Collect the data from the files
                    rows.append({"CIK": cik, "vc_name": vc_name, "vc_country": vc_country, "periodOfReport": periodOfReport,
                         "nameOfIssuer": nameOfIssuer, "titleOfClass": titleOfClass, "cusip": cusip, "value": value, 
                          "sshPrnamt":sshPrnamt, "shrsOrPrnAmt":shrsOrPrnAmt})

            except:
                print("problem with ",table_file_name)
                pass

        '''
        Save the data to df_HF.csv
        '''
        out_df = pd.DataFrame(rows, columns = df_cols)
        out_df[['value', 'sshPrnamt']] = out_df[['value', 'sshPrnamt']].astype('float')
        out_df.periodOfReport = pd.to_datetime(out_df.periodOfReport)
        out_df.to_csv(f'{path}\\{cik}_df_HF.csv')
        
        return True
    
    else:
        return False


# # Build DF by stocks from the data that was collected at the DF_HF

# In[7]:


def create_stocks_df(cik):
    if(check_if_stock_file_exists(cik)):
        return True
    path = cwd+f'\\Data\\{cik}'
    stock_cik_df = path + f'\\{cik}_stocks_df.csv'

    initial_df_file = path + f'\\{cik}_df_HF.csv'
    
    initial_df = pd.read_csv(initial_df_file, index_col=0)
    
    """
    create list of dates
    """
    periodOfReports = initial_df.periodOfReport.value_counts().sort_index().reset_index().rename(columns={'index': 'report_date',
                                                                                                          'periodOfReport': 'count_date'})
    
    """
    find unique stock names
    """
    nameOfIssuers = initial_df.nameOfIssuer.unique()
    
    """
    create stock df
    """
    
    stocks_df = pd.DataFrame()
    
    for name in nameOfIssuers:
        """
        slice df
        """
        small_df = initial_df.loc[initial_df.nameOfIssuer == name]
        titleOfClasses = small_df.titleOfClass.unique()
        
        for title in titleOfClasses:
            new_small_df = small_df.loc[small_df.titleOfClass == title]

            """
            add missing dates
            """
            small_df_with_dates = periodOfReports.merge(new_small_df, left_on='report_date',
                                                        right_on='periodOfReport', 
                                                        how='left').drop(['count_date', 'periodOfReport'], axis=1)

            """
            fill nan with 0
            """
            small_df_with_dates = small_df_with_dates.fillna(0)

            """
            fill repeat values
            """
            columns = ['CIK', 'vc_name', 'vc_country', 'nameOfIssuer', 'titleOfClass', 'cusip']
            fill_values_dict = {}
            for column in columns:
                for value in small_df_with_dates[column]:
                    if value != 0:
                        fill_values_dict[column] = value
            for column in columns:
                for i, value in enumerate(small_df_with_dates[column]):
                    if value == 0:
                        small_df_with_dates.loc[i, column] = fill_values_dict[column]

            """
            add the new columns
            """
            new_columns = ['PPS', 'holding_duration', 'holding_proportion', 'portfolio_duration', 'New', 'AddedTo', 
                           'Trimmed', 'SoldOut', 'Profit', 'yield_from_last_report', 'yield_from_1_year', 
                           'yield_from_3_year', 'yield_from_continuous_profit']
            for column in new_columns:
                small_df_with_dates[column] = 0

            for i in range(len(small_df_with_dates)):
                """
                PPS
                """
                if small_df_with_dates.loc[i, 'sshPrnamt'] != 0:
                    small_df_with_dates.loc[i, 'PPS'] = round((small_df_with_dates.loc[i, 'value'] * 1000) / small_df_with_dates.loc[i, 'sshPrnamt'], 2)

                """
                duration
                """
                if small_df_with_dates.loc[i, 'value'] == 0:
                    small_df_with_dates.loc[i, 'holding_duration'] = 0
                else:
                    q_duration = 1
                    j = i-1
                    while j > -1:
                        if small_df_with_dates.loc[j, 'value'] != 0:
                            q_duration += 1
                            j -= 1
                        else:
                            break
                    small_df_with_dates.loc[i, 'holding_duration'] = q_duration/4


            """
            stock holding changes
            """
            for i in range(1, len(small_df_with_dates)):
                if small_df_with_dates.loc[i, 'value'] != 0 and small_df_with_dates.loc[i-1, 'value'] == 0:
                    small_df_with_dates.loc[i, 'New'] = small_df_with_dates.loc[i, 'value']
                elif small_df_with_dates.loc[i-1, 'value'] != 0 and small_df_with_dates.loc[i, 'value'] == 0:
                    small_df_with_dates.loc[i, 'SoldOut'] = small_df_with_dates.loc[i-1, 'value']
                elif small_df_with_dates.loc[i, 'value'] != 0 and small_df_with_dates.loc[i-1, 'value'] != 0:
                    gap = small_df_with_dates.loc[i, 'sshPrnamt'] - small_df_with_dates.loc[i-1, 'sshPrnamt']
                    if gap < 0:
                        small_df_with_dates.loc[i, 'Trimmed'] = round((((small_df_with_dates.loc[i, 'PPS'] + small_df_with_dates.loc[i-1, 'PPS'])/2) * (gap * (-1)))/1000, 2)
                    elif gap > 0:
                        small_df_with_dates.loc[i, 'AddedTo'] = round((((small_df_with_dates.loc[i, 'PPS'] + small_df_with_dates.loc[i-1, 'PPS'])/2) * gap) /1000, 2)
                if small_df_with_dates.loc[i, 'value'] != 0:
                    small_df_with_dates.loc[i, 'Profit'] = round(small_df_with_dates.loc[i, 'value'] - small_df_with_dates.loc[i, 'New'] - small_df_with_dates.loc[i, 'AddedTo'] + small_df_with_dates.loc[i, 'SoldOut'] + small_df_with_dates.loc[i, 'Trimmed']- small_df_with_dates.loc[i-1, 'value'], 2)
                if small_df_with_dates.loc[i-1, 'value'] != 0:
                    small_df_with_dates.loc[i, 'yield_from_last_report'] = round(small_df_with_dates.loc[i, 'Profit'] / small_df_with_dates.loc[i-1, 'value'], 2)

            """
            stock Yield
            """
            year_profit = 0
            quarters = len(small_df_with_dates)-1 
            while quarters >= len(small_df_with_dates)-5:
                year_profit += small_df_with_dates.loc[quarters, 'Profit']
                quarters -= 1
            if small_df_with_dates.loc[len(small_df_with_dates)-1, 'Profit'] != 0 and small_df_with_dates.loc[len(small_df_with_dates)-5, 'Profit'] != 0:
                small_df_with_dates.loc[len(small_df_with_dates)-1, 'yield_from_1_year'] = round(year_profit/small_df_with_dates.loc[len(small_df_with_dates)-5, 'value'], 2)


            three_year_profit = 0
            calculate_continuous_profit = 0
            quarters = len(small_df_with_dates)-1
            if quarters > 13 and small_df_with_dates.loc[len(small_df_with_dates)-13, 'Profit'] != 0:
                while quarters >= len(small_df_with_dates)-13:
                    three_year_profit += small_df_with_dates.loc[quarters, 'Profit']
                    quarters -= 1
                if small_df_with_dates.loc[len(small_df_with_dates)-1, 'Profit'] != 0:
                    small_df_with_dates.loc[len(small_df_with_dates)-1, 'yield_from_3_year'] = round(three_year_profit/small_df_with_dates.loc[len(small_df_with_dates)-13, 'value'], 2)
            else:
                while quarters >= 0:
                    if small_df_with_dates.loc[quarters, 'Profit'] != 0:
                        calculate_continuous_profit += small_df_with_dates.loc[quarters, 'Profit']
                        quarters -= 1
                    else:
                        break
                if small_df_with_dates.loc[len(small_df_with_dates)-1, 'Profit'] != 0 and small_df_with_dates.loc[quarters+1, 'Profit'] != 0:
                    small_df_with_dates.loc[len(small_df_with_dates)-1, 'yield_from_continuous_profit'] = round(calculate_continuous_profit/small_df_with_dates.loc[quarters+1, 'value'], 2)

            """
            create stocks_df
            """
            stocks_df = pd.concat([stocks_df, small_df_with_dates], ignore_index=True)

    stocks_df['holding_proportion'] = round(stocks_df.value / stocks_df.groupby('report_date')['value'].transform('sum'), 4)
    stocks_df['portfolio_duration'] = round(stocks_df['holding_proportion']*stocks_df['holding_duration'],2)
    stocks_df['bought_times'] = np.where(stocks_df.New + stocks_df.AddedTo > 0, 1, 0)

    """
    stocks_df to file
    """
    stocks_df.to_csv(path + f'\\{cik}_stocks_df.csv')
    
    return True


# In[8]:


def check_if_stock_file_exists(cik):
    path = cwd+f'\\Data\\{cik}'
    stock_cik_df_path = path + f'\\{cik}_stocks_df.csv'
    if(os.path.exists(stock_cik_df_path)):
        return True
    return False


# In[9]:


cik_df = pd.read_excel("CIK-list.xlsx")
cik_list = [str(x) for x in cik_df["CIK"]]


# In[10]:


#list that points to ciks that have corrupted files or unfinneshed cik file download process
error_list=[]
CIK_Done=[]


# In[ ]:


'''
Both invokes below are for the same purpose to create the stocks files they also call the same function
This first one do all the job, the second one check if the stock file of the CIK is missing then do the job
we Can run one of them and will got the same results.
'''


# In[11]:


get_ipython().run_cell_magic('time', '', 'for CIK in cik_list: \n    print("Started working on ",CIK)\n    \n    try: \n        if get_files_details(CIK) is True:\n            if download_files_and_try_read(CIK) is True: \n                if from_cik_files_to_df(CIK) is True: \n                    print(f"formed successfully {CIK}_df_HF")\n                    \n                    if create_stocks_df(CIK) is True:\n                        print(f"formed successfully {CIK}_df_Stocks")\n                    else:\n                        print(f"failed to create {CIK}_df_Stocks")\n                        error_list.append(CIK)\n                        \n                else:\n                    print(CIK, "Couldn\'t create df_HF file")\n                    error_list.append(CIK)\n                    \n            else:\n                error_list.append(CIK)\n                print("Incorrupt files were detected at ",CIK)\n                print("#####################\\n ")\n        \n        else:\n            error_list.append(CIK)\n            print(CIK, "doesn\'t have 13F files")\n            \n        print("\\nFinished working on ",CIK)\n        print("#####################\\n ")\n\n    except:\n        print("couldn\'t work with ",CIK)\n        error_list.append(CIK)\n        print("#####################\\n ")\n        pass')


# In[11]:


get_ipython().run_cell_magic('time', '', 'error_list=[]\nCIK_Done=[]\nfor CIK in cik_list: \n    #print("Started working on missing stock files ",CIK)\n    \n    try: \n        if check_if_stock_file_exists(CIK) is False:\n            if get_files_details(CIK) is True:\n                if download_files_and_try_read(CIK) is True: \n                    if from_cik_files_to_df(CIK) is True: \n                        print(f"formed successfully {CIK}_df_HF")\n\n                        if create_stocks_df(CIK) is True:\n                            print(f"formed successfully {CIK}_df_Stocks")\n                        else:\n                            print(f"failed to create {CIK}_df_Stocks")\n                            error_list.append(CIK)\n\n                    else:\n                        print(CIK, "Couldn\'t create df_HF file")\n                        error_list.append(CIK)\n\n                else:\n                    error_list.append(CIK)\n                    print("Incorrupt files were detected at ",CIK)\n                    print("#####################\\n ")\n\n            else:\n                error_list.append(CIK)\n                print(CIK, "doesn\'t have 13F files")\n\n            print("\\nFinished working on ",CIK)\n            print("#####################\\n ")\n        else:\n            print("Stock DF was created Successfully", CIK)\n            CIK_Done.append(CIK)\n\n    except:\n        print("couldn\'t work with ",CIK)\n        error_list.append(CIK)\n        print("#####################\\n ")\n        pass')


# In[17]:


len(CIK_Done)


# In[12]:


#CIKs that couldn't create for them stock file
error_list


# In[18]:


error_list=["1340807","313028","1595082","860643","1112325"]


# In[12]:


error_list1=[]


# In[19]:


get_ipython().run_cell_magic('time', '', 'for CIK in error_list: \n    print("Started working on ",CIK)\n    \n    try: \n        if get_files_details(CIK) is True:\n            if download_files_and_try_read(CIK) is True: \n                if from_cik_files_to_df(CIK) is True: \n                    print(f"formed successfully {CIK}_df_HF")\n                    \n                    if create_stocks_df(CIK) is True:\n                        print(f"formed successfully {CIK}_df_Stocks")\n                    else:\n                        print(f"failed to create {CIK}_df_Stocks")\n                        error_list1.append(CIK)\n                        \n                else:\n                    print(CIK, "Couldn\'t create df_HF file")\n                    error_list1.append(CIK)\n                    \n            else:\n                error_list1.append(CIK)\n                print("Incorrupt files were detected at ",CIK)\n                print("#####################\\n ")\n        \n        else:\n            error_list1.append(CIK)\n            print(CIK, "doesn\'t have 13F files")\n            \n        print("\\nFinished working on ",CIK)\n        print("#####################\\n ")\n\n    except:\n        print("couldn\'t work with ",CIK)\n        error_list1.append(CIK)\n        print("#####################\\n ")\n        pass')


# In[ ]:




