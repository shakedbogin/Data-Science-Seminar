#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import os
import time
from random import randint
import xml.etree.ElementTree as et 
import feedparser
import webbrowser


# ### We didn't use these methods to gather the funds cik, but it is a good way to collect cik numbers (that submit 13f filings) for future analysis

# In[2]:


#latest, and updates every few minutes...around 150 cik -  https://sec.report/Form/13F-HR.rss

i = 0
cik_list3 = []
RSS = feedparser.parse('https://sec.report/Form/13F-HR.rss')
feed_entries = RSS.entries

for entry in feed_entries:
    title = entry.guid
    try: 
        doc = title.split("/")[4]      
        CIK = doc.split("-")[0]
        cik_list3.append(CIK)
        print(CIK)
    except:
        i += 1
        print(i)
        pass


# In[3]:


cik_set = set(cik_list3)
len(cik_set)


# In[5]:


#in search shows thousands, but we can scrape only 80 at a time
XMLlink = 'https://www.sec.gov/cgi-bin/srch-edgar?text=form-type%3D%2213F-HR%22%20AND%20Period%3D%2220201231%22&start=1&count=80&first=2020&last=2021&output=atom'

cik_list = []
RSS = feedparser.parse(XMLlink)
feed_entries = RSS.entries

for entry in feed_entries:
    link = entry.link
    cik = link.split("/")[6]
    cik_list.append(cik)


# In[7]:


# len(cik_list)


# ![image.png](attachment:image.png)

# In[4]:


#latest, and updates every few minutes...around 150 cik -  https://sec.report/Form/13F-HR.rss
i = 0
cik_list2 = []
RSS = feedparser.parse('https://sec.report/Form/13F-HR.rss')
feed_entries = RSS.entries

for entry in feed_entries:
    title = entry.description
    try: 
        name = re.search('-\s(.+)\s\(\d+\)\s\(Filer\)', title).group(1)
        CIK = re.search('\((\d+)\)\s\(Filer\)', title)[1]
        cik_list2.append(CIK)
        print(CIK,name)
    except:
        i += 1
        print(i)
        pass
    
    
    

