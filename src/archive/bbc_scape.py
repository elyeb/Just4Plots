"""
Get the top 10 read news stories from BBC for the past week and create an arrow
plot of the rankings.

https://www.bbc.com/news
https://web.archive.org/web/20250000000000*/https://www.bbc.com/news
"""
import bs4, requests, sys, codecs, urllib.request, re
import pandas as pd

website_list = ['https://www.bbc.com/news',]