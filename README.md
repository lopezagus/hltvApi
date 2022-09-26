# HLTV Api

Given the lack of public APIs to query Professional CS:GO data from played matches and events, web scraping is an alternative to gather realiable data. 

hltv.org has become the best source for e-sports enthusiasts to find CS:GO related information.

This project aims to provide an intuitive user interface to query specific data from HLTV webpage and save it into friendly data structures to be worked on. Depending on the request, dictionaries and DataFrames will be used to return the data. Future code will allow for requested data to be saved on 'csv' files and in databases.

At this moment, the API is fully functional and can be used to retrieve the nearly 61000 matches registered on HLTV webpage. However, to prevent overloading the website, I added a small 15 second sleep time every 15 requests to scrape the site in a friendly way.
