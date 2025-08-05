## Load contribution and independent expenditures data and answer: 
# - who raised most money for election year 2025 so far?
# - which candidates have PACs spent most for and against so far?


rm(list = ls())
library(data.table)
library(ggplot2)
library(scales)
library(stringr)
library(patchwork)

data_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/pdc_downloads/')

list.files(data_folder)

## Answer questions for contributions
contr_df <- fread(paste0(data_folder,"pdc_contributions_2025.csv"))
contr_df <- as.data.table(contr_df)
colnames(contr_df)

# filter to meaningful entries
contr_df <- contr_df[type=="Candidate"]
contr_df <- contr_df[cash_or_in_kind=="Cash"]
contr_df <- contr_df[amount>0]
contr_df <- contr_df[,.(filer_name,election_year,amount,office,position,jurisdiction,jurisdiction_county)]

# group by races and candidates
contr_grouped <- contr_df[,.(total= sum(amount)),by=.(filer_name,election_year,office,position,jurisdiction,jurisdiction_county)]

setorderv(contr_grouped, cols = c("jurisdiction_county", "office","position","total"), order = c(1L,1L,1L,-1L)) # Sorts by Value descending, then ID ascending

# Answer: COUNTY EXECUTIVE position has raised most money, led by Girmay Zahilay

# races of interest
king <- contr_grouped[jurisdiction_county=="KING"]
# Note, names of candidates are not standardized   

jef <- contr_grouped[jurisdiction_county=="JEFFERSON"]

## Answer questions for independent expenditures
ind_df <- fread(paste0(data_folder,"pdc_ind_exp_2025.csv"))
ind_df <- as.data.table(ind_df)
colnames(ind_df)

# Filter to meaningful rows
ind_df <- ind_df[candidate_name!=""]
ind_by_cand <- ind_df[,.(candidate_name,portion_of_amount,for_or_against,candidate_office,candidate_jurisdiction)]
ind_by_pac <- ind_df[,.(sponsor_name,portion_of_amount)]

ind_by_cand_grouped <- ind_by_cand[,.(total=sum(portion_of_amount)),by=.(candidate_name,for_or_against,candidate_office,candidate_jurisdiction)]
ind_by_pac <- ind_by_pac[,.(total=sum(portion_of_amount)),by=sponsor_name]

# Answer: NEW DIRECTION PAC

# out of interest
realtors <- ind_df[sponsor_name %like% "REALTORS"]
