# Layman's Research Projects

### **Date added** Jul 31, 2025 <br>
**More on campaing contriubtions and PAC spending in local races**  
Making bar charts to distinguish between candidates on the 2025 Seattle ballot (mainly only for candidates having raised over a few thousand dollars). For each race, try to answer: 
- which PACs are spending money for and against the candidates?
- who receives most from real estate (from employer/occupation info)?
- who has most labor contributions?
- who receives most from amazon?
![seattle_mayor.pdf](outputs/plots/lobbying/seattle_mayor.pdf)
![county_executive.pdf](outputs/plots/lobbying/county_executive.pdf)
![seattle_city_council_position_no_9.pdf](outputs/plots/lobbying/seattle_city_council_position_no_9.pdf)
![city_attorney.pdf](outputs/plots/lobbying/city_attorney.pdf)
![seattle_district_2_school_director.pdf](outputs/plots/lobbying/seattle_district_2_school_director.pdf)
- Plotting code: [here](src/candidate_contributions_bar_charts.R)
- Data from: https://www.pdc.wa.gov/political-disclosure-reporting-data

### **Date added** July 31, 2025 <br>
**Ferry plots daily**  
Pointing to an plot that should update daily via Github Actions
![all_routes_today.png](docs/all_routes_today.png)
- Scraping code for sellout times: [here](src/ferry_scrape.py)
- Download code for departure times data frames: [here](src/ferry_data_download.py)
- Plotting code: [here](src/ferry_plot.py)

### **Date added** Jul 21, 2025 <br>
**Distribution of contributions to similar candidates**  
Exploring ways to see differences in campaign contributions by candidates
for the King County Executive position in 2025. 
![donors_hist_Balducci_Zahilay.png](outputs/plots/lobbying/donors_hist_Balducci_Zahilay.png)
- Plotting code: [here](src/draft_campaign_finance_analysis.py)

### **Date added** May 16, 2025 <br>
**Main ferry plots for the weekend**  
Collecting more data. Not yet enough that box-and-whiskers are useful, but enough to get a sense of the overall pattern.  
![colman_ferry_fridays.png](outputs/plots/colman_ferry_fridays.png)
![colman_ferry_sundays.png](outputs/plots/colman_ferry_sundays.png)
![bainbridge_ferry_sundays.png](outputs/plots/bainbridge_ferry_sundays.png) 
- Scraping code for sellout times: [here](src/ferry_scrape.py)
- Download code for departure times data frames: [here](src/ferry_data_download.py)
- Plotting code: [here](src/ferry_plot.py)

### **Date added** May 2, 2025 <br>
**Main ferry plots for the weekend**  
![colman_ferry_saturday.png](outputs/plots/colman_ferry_saturday.png)  
![edmonds_ferry_saturday.png](outputs/plots/edmonds_ferry_saturday.png)
![bainbridge_ferry_sunday.png](outputs/plots/bainbridge_ferry_sunday.png)
![kingston_ferry_sunday.png](outputs/plots/kingston_ferry_sunday.png)
- Scraping code for sellout times: [here](src/ferry_scrape.py)
- Download code for departure times data frames: [here](src/ferry_data_download.py)
- Plotting code: [here](src/ferry_plot.py)

### **Date added** May 1, 2025 <br>
**CNN Coverage: Percent of Headlines that contain "Trump"**  
![cnn_keyword_search.png](outputs/plots/cnn_keyword_search.png)  
Another news trend, this time longer-term out of curiousity. 
- Scraping and plotting code: [here](src/cnn_analysis.py)

### **Date added** April 30, 2025 <br>
**Seattle to Bainbridge Ferry, April 26**  
![seattle_ferry_saturday.png](outputs/plots/seattle_ferry_saturday.png)  
I'm trying to plot the data from Washington State Ferries' sites and avoid weekend rush hours. 
- Scraping code for sellout times: [here](src/ferry_scrape.py)
- Download code for departure times data frames: [here](src/ferry_data_download.py)
- Plotting code: [here](src/ferry_plot.py)

### **Date added** April 22, 2025 <br>
**CNN Coverage: Tariffs vs Signalgate**  
![cnn_tariffs_signal.png](outputs/plots/cnn_tariffs_signal.png)  
I'm interested in easy ways to track how long a news cycle lasts, and whether one competes with another. Google Trends for news will show a similar pattern, but I understand that's just for user searches rather than news coverage. Here, the counts for each topic are just based on the headline summaries for CNN transcipt data, rather than the full transcripts. Would love to learn about similar sites for other news orgs. 
- Code [here](src/cnn_analysis.py)


### **Date added** April 19, 2025 <br>
**Average Gas vs Crude Oil Prices**  
Although the correlation is strong, the coloring here shows us that in later years the ratio of gas prices to oil prices is higher. This may also be due to some quality differences. 
![strikes_oecd.png](outputs/plots/oil_gas_scatter.png)  
- Code [here](src/oil_v_gas.py)

### **Date added** April 18, 2025 <br>
**Number of Strikes and Lockouts in OECD Countries**  
I've always been struck by the decline since the 1970s of strikes across so many countries around the same time. 
![strikes_oecd.png](outputs/plots/strikes_oecd.png)  
- Code [here](src/strikes.py)

### **Date added** April 15, 2025 <br>
**Washington State Map of DUI Filings by county and city.**  
Interested in what can be made with WA administrative data. 
![dui_2024.png](outputs/plots/dui_2024.png)
- Code [here](src/dui_data.py)


### **Date added** April 4, 2025 <br>
**Export to US as a share of GDP by country**
Southeast Asia was a suprise to me here. 
![imports_gdp_ratio_map.png](outputs/plots/imports_gdp_ratio_map.png)
- Code [here](src/map_tariffs_impact.py)