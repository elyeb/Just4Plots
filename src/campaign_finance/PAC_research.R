## Tasks related to researching PACs in WA
# - how has the distribution of PAC spending changed over time (stacked bar chart)
# - which races get the most pac money?
# interest: what do the below pacs spend money on?
# - NATIONAL ASSOCIATION OF REALTORS FUND
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
library(ggalluvial)
library(networkD3)
options(scipen = 999)

## Get campaign contribution data and PAC data
money_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/pdc_downloads/')
subset_datasets_outfolder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/pdc_downloads/subsets/')

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
ind_df[,sponsor_name:=trimws(sponsor_name)]

# Standardize PAC sponsor names
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
ind_df[sponsor_name=="NATIONAL ASSOCIATION OF REALTORS",sponsor_name:="NATIONAL ASSOCIATION OF REALTORS FUND"]
ind_df[sponsor_name=="WASHINGTON REALTORS POLITICAL ACTION COMMITTEE",sponsor_name:="NATIONAL ASSOCIATION OF REALTORS FUND"]
ind_df[sponsor_name=="PLANNED PARENTHOOD VOTES WASHINGTON PAC",sponsor_name:="PLANNED PARENTHOOD VOTES! WASHINGTON"]
ind_df[sponsor_name=="REPUBLICAN STATE LEADERSHIP COMMITTEE -WASHINGTON PAC (RSLC-WASHINGTON PAC)",sponsor_name:="REPUBLICAN STATE LEADERSHIP COMMITTEE -WASHINGTON"]
ind_df[sponsor_name=="STAND FOR CHILDREN WASHINGTON PAC",sponsor_name:="STAND FOR CHILDREN WA PAC"]
ind_df[sponsor_name=="THE AFFORDABLE HOUSING COUNCIL OF THE OLYMPIA MASTER BUILDERS",sponsor_name:="THE AFFORDABLE HOUSING COUNCIL OF OLYMPIA MASTER BUILDERS"]
ind_df[sponsor_name=="WA ST COUNCIL OF CO & CITY EMPLOYEES",sponsor_name:="WA ST COUNCIL OF COUNTY & CITY EMPLOYEES"]
ind_df[sponsor_name=="WASHINGTON STATE DENTAL PAC",sponsor_name:="WASHINGTON STATE DENTAL POLITICAL ACTION COMMITTEE"]
ind_df[sponsor_name=="WORKING WASHINGTON PAC",sponsor_name:="WORKING WASHINGTON"]
ind_df[sponsor_name=="WASHINGTON ASSOCIATION OF REALTORS®",sponsor_name:="WASHINGTON REALTORS POLITICAL ACTION COMMITTEE"]

# Standardize PAC candidate names
ind_df[,candidate_name := trimws(toupper(candidate_name))]
ind_df[candidate_name=="AL FRENCH",candidate_name:="ALFRED AL FRENCH"]
ind_df[candidate_name=="T. PLESE  KIM",candidate_name:="KIM T. PLESE"]
ind_df[candidate_name=="NADINE NADINE MARIE WOODWARD",candidate_name:="MARIE WOODWARD NADINE NADINE"]


# Standardize PAC candidate offices and jurisdictions
ind_df[,candidate_office := trimws(toupper(candidate_office))]
ind_df[,candidate_jurisdiction := trimws(toupper(candidate_jurisdiction))]

# Get regular contributions to compare
# contributions
contr_df <- fread(paste0(money_folder,"pdc_contributions_2025.csv"))
contr_df <- as.data.table(contr_df)
colnames(contr_df)

contr_df[,filer_name:=trimws(toupper(filer_name))]
contr_df[,contributor_name:=trimws(toupper(contributor_name))]

# Standardize filer_name
contr_df[filer_name=="HARRELL BRUCE A (BRUCE HARRELL)",filer_name:="BRUCE HARRELL"]
contr_df[filer_name=="BRUCE A. HARRELL (BRUCE HARRELL)",filer_name:="BRUCE HARRELL"]
contr_df[filer_name=="KATHERINE BARRETT WILSON (KATIE WILSON)",filer_name:="KATIE WILSON"]


contr_to_pac <- contr_df[type=="Political Committee"]

# filter to meaningful entries
contr_df <- contr_df[type=="Candidate"]
contr_df <- contr_df[cash_or_in_kind=="Cash"]
contr_df <- contr_df[amount>0]
# contr_df <- contr_df[,.(filer_name,election_year,amount,office,position,jurisdiction,jurisdiction_county)]

# first apply manually-corrrected names


# Filter to meaningful rows
ind_df_candidates <- ind_df[candidate_name!=""]
ind_pac_cand <- ind_df_candidates[,.(candidate_name,portion_of_amount,for_or_against,election_year,candidate_office,candidate_jurisdiction,sponsor_name)]
ind_pac_cand <- ind_pac_cand[,.(total=sum(portion_of_amount)),by=.(candidate_name,for_or_against,candidate_office,election_year,candidate_jurisdiction,sponsor_name)]
ind_pac <- ind_df_candidates[,.(total=sum(portion_of_amount)),by=.(election_year,sponsor_name)]

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


## - which races get the most pac money?
by_race <- ind_df[,.(candidate_office,portion_of_amount)]
by_race[,candidate_office:=toupper(candidate_office)]
by_race <- by_race[,.(total=sum(portion_of_amount)),by=candidate_office]
setorderv(by_race,cols = "total",order = c(-1L))

by_race$candidate_office <- factor(by_race$candidate_office, levels = unique(by_race$candidate_office))



## Look into indv PACs
# - NATIONAL ASSOCIATION OF REALTORS FUND
df_realtors <- ind_df[sponsor_name=="NATIONAL ASSOCIATION OF REALTORS FUND"]
df_realtors_grouped <- df_realtors[candidate_name!="",.(sponsor_name,candidate_name,portion_of_amount,for_or_against,candidate_office,candidate_jurisdiction,election_year)]
df_realtors_grouped <- df_realtors_grouped[,.(total=sum(portion_of_amount)),by=.(sponsor_name,candidate_name,for_or_against,candidate_office,candidate_jurisdiction,election_year)]
setorderv(df_realtors_grouped,"election_year")
df_realtors_grouped[,candidate_office := paste(candidate_office,candidate_jurisdiction,election_year,sep=" - ")]
df_realtors_grouped <- df_realtors_grouped[,.(candidate_office= paste(for_or_against," ",": ",candidate_office,collapse="\n"),total=sum(total)),by=.(sponsor_name,candidate_name)]
df_realtors_grouped[,candidate_office := paste(candidate_name,candidate_office,sep=" ")]

df_realtors_grouped[, sponsor_name := as.factor(sponsor_name)]
df_realtors_grouped[, candidate_office :=
                      factor(candidate_office, levels = unique(candidate_office))]


## Let's focus on Bruce Harrell vs Katie Wilson instead, including all funding
sea_mayor_25 <- ind_df[(candidate_name!="")&
                         (candidate_office=="MAYOR")&
                         (election_year==2025)&
                         (candidate_name %in% c("BRUCE HARRELL","KATIE WILSON")),]

# Assume: against opponent is for candidate
candidates <- c("BRUCE HARRELL","KATIE WILSON")
sea_mayor_25[(for_or_against=="Against")&(candidate_name=="KATIE WILSON"),`:=`(for_or_against="For",candidate_name="BRUCE HARRELL")]
sea_mayor_25[(for_or_against=="Against")&(candidate_name=="BRUCE HARRELL"),`:=`(for_or_against="For",candidate_name="KATIE WILSON")]

# group
sea_mayor_25 <- sea_mayor_25[,.(total=sum(portion_of_amount)),by=.(sponsor_name,candidate_name,candidate_office,candidate_jurisdiction)]

# deal with contributions to pacs
relevant_pacs <- contr_to_pac[filer_name %in% unique(sea_mayor_25$sponsor_name)]  #[filer_name %in% "BRUCE HARRELL FOR SEATTLE'S FUTURE"]
relevant_pacs_grouped <- relevant_pacs[,.(total=sum(amount)),by=.(filer_name,contributor_name,contributor_address,contributor_city,contributor_state,description)]
setnames(relevant_pacs_grouped,old=c("filer_name","total"),new=c("sponsor_name","total_contributed"))
setnames(sea_mayor_25,old=c("total"),new=c("total_spent"))

direct_contributors <- contr_df[filer_name %in% candidates]
direct_contributors_grouped <- direct_contributors[,.(total_contributed=sum(amount)),by=.(filer_name,contributor_name,contributor_address,contributor_city,contributor_state,description)]

setnames(direct_contributors_grouped,old=c("filer_name"),new=c("candidate_name"))
direct_contributors_grouped[(contributor_name=="SMALL CONTRIBUTIONS")&(candidate_name=="BRUCE HARRELL"),contributor_name:="SMALL CONTRIBUTIONS-BRUCE HARRELL"]
direct_contributors_grouped[(contributor_name=="SMALL CONTRIBUTIONS")&(candidate_name=="KATIE WILSON"),contributor_name:="SMALL CONTRIBUTIONS-KATIE WILSON"]



# Question: how small do contributions have to be in order for them to get lumped in with SMALL CONTRIBUTIONS?
# Answer: $150 or less. Let's group into 150 or less, then between 151 and 1k, and over 1k donations get their own names
# updated approach: split out SMALL CONTRIBUTIONS so they don't all end up in the same block (number of contributors in descriptions), 
# but assign a category that appears in the saved data frames. 


direct_contributors_grouped[contributor_name=="SMALL CONTRIBUTIONS-BRUCE HARRELL",contributor_name:="SMALL CONTRIBUTIONS (<=$150)-BRUCE HARRELL"]
direct_contributors_grouped[contributor_name=="SMALL CONTRIBUTIONS-KATIE WILSON",contributor_name:="SMALL CONTRIBUTIONS (<=$150)-KATIE WILSON"]
# direct_contributors_grouped[(total_contributed<=150)&(candidate_name=="BRUCE HARRELL"),contributor_name:="SMALL CONTRIBUTIONS (<=$150)-BRUCE HARRELL"]
# direct_contributors_grouped[(total_contributed<=150)&(candidate_name=="KATIE WILSON"),contributor_name:="SMALL CONTRIBUTIONS (<=$150)-KATIE WILSON"]
# direct_contributors_grouped[(total_contributed>150)&(total_contributed<1000)&(candidate_name=="BRUCE HARRELL"),contributor_name:="MEDIUM CONTRIBUTIONS (<=$1000)-BRUCE HARRELL"]
# direct_contributors_grouped[(total_contributed>150)&(total_contributed<1000)&(candidate_name=="KATIE WILSON"),contributor_name:="MEDIUM CONTRIBUTIONS (<=$1000)-KATIE WILSON"]
direct_contributors_grouped <- direct_contributors_grouped[,.(total_contributed=sum(total_contributed)),by=.(candidate_name,contributor_name,description)]


relevant_pacs_grouped[(contributor_name=="SMALL CONTRIBUTIONS")&(sponsor_name=="BRUCE HARRELL FOR SEATTLE'S FUTURE"),contributor_name:="SMALL CONTRIBUTIONS (<=$150)-BRUCE HARRELL FOR SEATTLE'S FUTURE"]
relevant_pacs_grouped[(contributor_name=="SMALL CONTRIBUTIONS")&(sponsor_name=="FUSE VOTES"),contributor_name:="SMALL CONTRIBUTIONS (<=$150)-FUSE VOTES"]
# relevant_pacs_grouped[(total_contributed<=150)&(sponsor_name=="BRUCE HARRELL FOR SEATTLE'S FUTURE"),contributor_name:="SMALL CONTRIBUTIONS (<=$150)-BRUCE HARRELL FOR SEATTLE'S FUTURE"]
# relevant_pacs_grouped[(total_contributed<=150)&(sponsor_name=="FUSE VOTES"),contributor_name:="SMALL CONTRIBUTIONS (<=$150)-FUSE VOTES"]
# relevant_pacs_grouped[(total_contributed>150)&(total_contributed<1000)&(sponsor_name=="BRUCE HARRELL FOR SEATTLE'S FUTURE"),contributor_name:="MEDIUM CONTRIBUTIONS (<=$1000)-BRUCE HARRELL FOR SEATTLE'S FUTURE"]
# relevant_pacs_grouped[(total_contributed>150)&(total_contributed<1000)&(sponsor_name=="FUSE VOTES"),contributor_name:="MEDIUM CONTRIBUTIONS (<=$1000)-FUSE VOTES"]
relevant_pacs_grouped <- relevant_pacs_grouped[,.(total_contributed=sum(total_contributed)),by=.(sponsor_name,contributor_name,description)]


extract_first_number <- function(text_column) {
  # Ensure character
  text_column <- as.character(text_column)
  
  # Replace NA with ""
  text_column[is.na(text_column)] <- ""
  
  # Use stringr::str_extract for simplicity & reliability
  nums <- stringr::str_extract(text_column, "\\d+")
  
  # Replace NAs with "1" and convert to numeric
  nums[is.na(nums)] <- "1"
  as.numeric(nums)
}

# explode small contributions
relevant_pacs_grouped[
  , no_contributors := extract_first_number(description)
]

direct_contributors_grouped[
  , no_contributors := extract_first_number(description)
]

relevant_pacs_grouped[,total_contributed:=total_contributed/no_contributors]
relevant_pacs_grouped <- relevant_pacs_grouped[rep(seq_len(.N), times = no_contributors)]

direct_contributors_grouped[,total_contributed:=total_contributed/no_contributors]
direct_contributors_grouped <- direct_contributors_grouped[rep(seq_len(.N), times = no_contributors)]

relevant_pacs_grouped$description <- NULL
relevant_pacs_grouped$no_contributors <- NULL
direct_contributors_grouped$description <- NULL
direct_contributors_grouped$no_contributors <- NULL

# Categorize contribution size
relevant_pacs_grouped[total_contributed<=150,contribution_size:= 'SMALL (<=$150)']
relevant_pacs_grouped[(total_contributed>150)&(total_contributed<=1000),contribution_size:= 'MEDIUM (<=$1000)']
relevant_pacs_grouped[total_contributed>1000,contribution_size:= 'BIG (>$1000)']

direct_contributors_grouped[total_contributed<=150,contribution_size:= 'SMALL (<=$150)']
direct_contributors_grouped[(total_contributed>150)&(total_contributed<=1000),contribution_size:= 'MEDIUM (<=$1000)']
direct_contributors_grouped[total_contributed>1000,contribution_size:= 'BIG (>$1000)']

sea_mayor_25[total_spent<=150,contribution_size:= 'SMALL (<=$150)']
sea_mayor_25[(total_spent>150)&(total_spent<=1000),contribution_size:= 'MEDIUM (<=$1000)']
sea_mayor_25[total_spent>1000,contribution_size:= 'BIG (>$1000)']


# assign unique names to small contributors
relevant_pacs_grouped[contributor_name %like% "SMALL CONTRIBUTIONS",contributor_name:= paste0(contributor_name,.I)]
direct_contributors_grouped[contributor_name %like% "SMALL CONTRIBUTIONS",contributor_name:= paste0(contributor_name,.I)]


# Save subsets
write.csv(sea_mayor_25,paste0(subset_datasets_outfolder,"sea_mayor_25.csv"),row.names=FALSE)
write.csv(relevant_pacs_grouped,paste0(subset_datasets_outfolder,"relevant_pacs_grouped.csv"),row.names=FALSE)
write.csv(direct_contributors_grouped,paste0(subset_datasets_outfolder,"direct_contributors_grouped.csv"),row.names=FALSE)
