## Tasks related to researching PACs in WA
# - how has the distribution of PAC spending changed over time (stacked bar chart)
# - which races get the most pac money?
# interest: what do the below pacs spend money on?
# - GREENWOOD NEIGHBORS COMMITTEE
# - KOCH INDUSTRIES INC
# - NOWYOUKNOW PAC
# - THAT'S JUST NOT RIGHT PAC
# - WASHINGTON STATE DENTAL POLITICAL ACTION COMMITTEE

rm(list = ls())
library(data.table)
library(ggplot2)
library(scales)
library(stringr)
library(patchwork)
library(dplyr)
library(plotly)
options(scipen = 999)

## Get campaign contribution data and PAC data
money_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/pdc_downloads/')

pac_files <- list.files(money_folder)
pac_files <- pac_files[grep("ind_exp", pac_files)]


# PACS
ind_df <- data.table()
for (f in pac_files){
  ind_df_tmp <- fread(paste0(money_folder,f))
  ind_df_tmp <- as.data.table(ind_df_tmp)
  ind_df <- rbind(ind_df,ind_df_tmp,fill=TRUE)
}

colnames(ind_df)
table(ind_df$)
ind_df[,sponsor_name:=trimws(sponsor_name)]

ind_df[sponsor_name=="DEMOCRATIC WOODINVILLE SPONSORED BY JEFFREY LYON",sponsor_name:="DEMOCRATIC WOODINVILLE SPONSORED BY JEFF LYON"]
ind_df[sponsor_name=="NEW DIRECTION PAC.",sponsor_name:="NEW DIRECTION PAC"]
ind_df[sponsor_name=="CHILDREN'S CAMPAIGN FUND",sponsor_name:="CHILDRENS CAMPAIGN FUND"]
ind_df[sponsor_name=="CONCERNED TAXPAYER ACCOUNTABILITY CENTER",sponsor_name:="CONCERNED TAXPAYERS ACCOUNTABILITY CENTER"]
ind_df[sponsor_name=="EASTSIDE PROGRESS PAC",sponsor_name:="EASTSIDE PROGRESS"]
ind_df[sponsor_name=="ENERGIZE WA PAC",sponsor_name:="ENERGIZE WASHINGTON"]
ind_df[sponsor_name=="EQUAL RIGHTS WA PAC",sponsor_name:="EQUAL RIGHT WASHINGTON PAC"]
ind_df[sponsor_name=="MAINSTREAM REPUB OF WA",sponsor_name:="MAINSTREAM REPUBLICANS OF WA"]
ind_df[sponsor_name=="MASTER BUILDERS ASSN OF KING & SNOHOMISH CO AFFORDABLE HOUSING COUNCIL",sponsor_name:="MASTER BUILDERS ASSC OF KING & SNO COUNTIES - AFFORDABLE HOUSING COUNCIL"]
ind_df[sponsor_name=="MASTER BUILDERS ASSN OF KING & SNOHOMISH COUNTIES",sponsor_name:="MASTER BUILDERS ASSC OF KING & SNO COUNTIES - AFFORDABLE HOUSING COUNCIL"]
ind_df[sponsor_name=="NATIONAL ASSN OF REALTORS FUND",sponsor_name:="NATIONAL ASSOCIATION OF REALTORS FUND"]
ind_df[sponsor_name=="NATIONAL ASSOC. OF REALTORS FUND",sponsor_name:="NATIONAL ASSOCIATION OF REALTORS FUND"]
ind_df[sponsor_name=="NATL ASSOCIATION OF REALTORS FUND",sponsor_name:="NATIONAL ASSOCIATION OF REALTORS FUND"]
ind_df[sponsor_name=="ONEAMERICA VOTES (OAV)",sponsor_name:="NATIONAL ASSOCIATION OF REALTORS FUND"]
ind_df[sponsor_name=="PLANNED PARENTHOOD VOTES WASHINGTON PAC",sponsor_name:="PLANNED PARENTHOOD VOTES! WASHINGTON"]
ind_df[sponsor_name=="REPUBLICAN STATE LEADERSHIP COMMITTEE -WASHINGTON PAC (RSLC-WASHINGTON PAC)",sponsor_name:="REPUBLICAN STATE LEADERSHIP COMMITTEE -WASHINGTON"]
ind_df[sponsor_name=="STAND FOR CHILDREN WASHINGTON PAC",sponsor_name:="STAND FOR CHILDREN WA PAC"]
ind_df[sponsor_name=="THE AFFORDABLE HOUSING COUNCIL OF THE OLYMPIA MASTER BUILDERS",sponsor_name:="THE AFFORDABLE HOUSING COUNCIL OF OLYMPIA MASTER BUILDERS"]
ind_df[sponsor_name=="WA ST COUNCIL OF CO & CITY EMPLOYEES",sponsor_name:="WA ST COUNCIL OF COUNTY & CITY EMPLOYEES"]
ind_df[sponsor_name=="WASHINGTON STATE DENTAL PAC",sponsor_name:="WASHINGTON STATE DENTAL POLITICAL ACTION COMMITTEE"]
ind_df[sponsor_name=="WORKING WASHINGTON PAC",sponsor_name:="WORKING WASHINGTON"]


# Filter to meaningful rows
ind_df <- ind_df[candidate_name!=""]
ind_pac_cand <- ind_df[,.(candidate_name,portion_of_amount,for_or_against,election_year,candidate_office,candidate_jurisdiction,sponsor_name)]
ind_pac_cand <- ind_pac_cand[,.(total=sum(portion_of_amount)),by=.(candidate_name,for_or_against,candidate_office,election_year,candidate_jurisdiction,sponsor_name)]
ind_pac <- ind_df[,.(total=sum(portion_of_amount)),by=.(election_year,sponsor_name)]

setorderv(ind_pac_cand, cols = c("for_or_against", "total"), order = c(1L,-1L)) # Sorts by Value descending, then ID ascending
ind_pac_cand <- unique(ind_pac_cand)

ind_pac <- ind_pac[total>0]
length(unique(ind_pac$sponsor_name))

# Plot top 5 by year, below total line chart
top_5 <- data.frame()
for (year in seq(2008,2025,1)){
  tmp <- ind_pac[election_year==year]
  setorderv(tmp,cols = "total",order = c(-1L))
  tmp <- head(tmp,5)
  top_5 <- rbind(top_5,tmp)
}

top_5[,sponsor_name:= as.factor(sponsor_name)]
setorderv(top_5,cols = "total",order = c(-1L))


# need 1 row per year per sponsor, even if 0
unique_sponsors <- unique(top_5$sponsor_name)
unique_years <- unique(top_5$election_year)
cross_join <- merge(unique_sponsors,unique_years)
colnames(cross_join) <- c("sponsor_name","election_year")

top_5[,election_year:= as.integer(election_year)]
top_5[,sponsor_name:= as.character(sponsor_name)]
cross_join <- as.data.table(cross_join)
cross_join[,sponsor_name:= as.character(sponsor_name)]
cross_join[,election_year:= as.integer(election_year)]
top_5_all <- merge(top_5,cross_join,by=c("election_year","sponsor_name"),all=T)
top_5_all[is.na(total)]$total <- 0

setorderv(top_5_all,cols = c("election_year","total"),order = c(1L,-1L))
top_5_all[,sponsor_name:= as.factor(sponsor_name)]


pac_time <- ggplot(top_5_all, aes(x = election_year, 
                      y = total, 
                      fill = sponsor_name,
                      text = sponsor_name)) +
  geom_area(position = "stack")+
  scale_y_continuous(labels = scales::comma)+
  theme_minimal()+
  theme(
    # axis.line = element_line(color = "black", size = 1.2),
    # panel.grid = element_blank(),
    legend.position = "none",
    # axis.title = element_text(size = 20),
    # axis.text = element_text(size = 16),
    # plot.title = element_text(size = 26, face = "bold"),
    # plot.subtitle = element_text(size = 20)
  )
interactive_plot <- plotly::ggplotly(pac_time, tooltip = "text")
interactive_plot
# -> not very informative graphic

## - which races get the most pac money?
by_race <- ind_df[,.(candidate_office,portion_of_amount)]
by_race[,candidate_office:=toupper(candidate_office)]
by_race <- by_race[,.(total=sum(portion_of_amount)),by=candidate_office]
setorderv(by_race,cols = "total",order = c(-1L))

by_race$candidate_office <- factor(by_race$candidate_office, levels = unique(by_race$candidate_office))

ggplot(by_race,aes(x=candidate_office,y=total))+
  geom_bar(stat = "identity")+
  scale_y_continuous(labels = scales::comma)+
  theme_minimal()+
  theme(
    # axis.line = element_line(color = "black", size = 1.2),
    # panel.grid = element_blank(),
    legend.position = "none",
    # axis.title = element_text(size = 20),
    # axis.text = element_text(size = 16),
    axis.text.x = element_text(angle = 45, hjust = 1),
    # plot.title = element_text(size = 26, face = "bold"),
    # plot.subtitle = element_text(size = 20)
  )

