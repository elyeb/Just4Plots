## Load results and campaign finance data and answer: 
# - how correlated were donations (with and without PACs) with winning?
# - which pacs won/lost?

rm(list = ls())
library(data.table)
library(ggplot2)
library(scales)
library(stringr)
library(patchwork)

## Make Name standardization list for candidates and groups
name_remap <- list("Adonis E. Ducksworth (Adonis Ducksworth)"="Adonis Ducksworth",
                   "Alan Raynier Feliz Rubio (Alan Rubio)"="Alan Rubio",
                   "Alexander Newman (Alex Newman)"="Alex Newman",
                   "Almaderica Escamilla (Derica Escamilla)"="Derica Escamilla",
                   "Amber D Cantu (Amber Cantu)"="Amber Cantu",
                   "Brandon Alan-Douglas Vollmer (Brandon A. Vollmer)"="Brandon A. Vollmer",
                   "Brianna K.Thomas (Brianna K. Thomas)"="Brianna K. Thomas",
                   "BrieAnne Gray (BrieAnne C. Gray)"="BrieAnne Gray",
                   "Bruce A. Harrell (Bruce Harrell)"="Bruce Harrell",
                   "CAITLIN KONYA (Caitlin Konya)"="CAITLIN KONYA",
                   "Caleb Allen Fahey (Caleb Fahey)"="Caleb Fahey",
                   "Carmen A. Rivera (Carmen Rivera)"="Carmen Rivera",
                   "Carson N. M. Sanderson (Carson Sanderson)"="Carson Sanderson",
                   "Catherine Lynn Malik (Catie Malik)"="Catie Malik",
                   "Chad L. Magendanz (Chad Magendanz)"="Chad Magendanz",
                   "Chad M. Whetzel (Chad Whetzel)"="Chad Whetzel",
                   "Charles Ames (Chas Ames)"="Chas Ames",
                   "Charles Kifer (Chuck Kifer)"="Chuck Kifer",
                   "DANIEL KNOX, JR (Dan Knox)"="Dan Knox",
                   "Daniel M Williams (Dan Williams)"="Dan Williams",
                   "David Robert Shelvey (David R. Shelvey)","David R. Shelvey",
                   "Deborah K Edwards (Debbie Edwards)"="Debbie Edwards",
                   "Devin Myles Leshin (Devin Leshin)"="Devin Leshin",
                   "Diodato (Dio) Boucsieguez (Dio Boucsieguez)"="Dio Boucsieguez",
                   "Don L. Rivers (Don L Rivers)"="Don L Rivers",
                   "Dorothy Ellen Talbo (Ellen Talbo)",
                   "Dung Thi Tuyet Ho (Jane Ho)"="Jane Ho",
                   "Edward C. Lin (Eddie Lin)"="Eddie Lin",
                   "Edward C. Lin (Edward Lin)"="Eddie Lin",
                   
                   )
# pattern - everything with parentheses is the standard version in the parentheses. contributions is most messy.
extract_clean_name <- function(names) {
  sapply(names, function(name) {
    # Extract the outermost set of parentheses
    match <- regmatches(name, regexpr("\\([^()]+(?:\\([^()]*\\)[^()]*)*\\)", name))
    
    if (length(match) == 1) {
      # Remove the outer parentheses only
      sub("^\\((.*)\\)$", "\\1", match)
    } else {
      name
    }
  }, USE.NAMES = FALSE)
}

# the issue with this is that some names have more than 1. will try merging to speed up the process.
results_names$db <- "results"
contr_names <- merge(contr_names,results_names,by='name',all.x=T)
contr_names_unmatched <- contr_names[is.na(db)]
contr_names_unmatched <- contr_names_unmatched[grepl("\\(", name)]


## Get election results data
data_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/election_results/primary_2025/')

list.files(data_folder)

all_results <- data.table()

for (f in list.files(data_folder)){
  tmp <- fread(paste0(data_folder,f))
  all_results <- rbind(all_results,tmp,fill = TRUE)
}

results_names <- data.table(name=unique(all_results$Candidate))

## Get campaign contribution data and PAC data
money_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/pdc_downloads/')

# contributions
contr_df <- fread(paste0(money_folder,"pdc_contributions_2025.csv"))
contr_df <- as.data.table(contr_df)
colnames(contr_df)

# filter to meaningful entries
contr_df <- contr_df[type=="Candidate"]
contr_df <- contr_df[cash_or_in_kind=="Cash"]
contr_df <- contr_df[amount>0]
contr_df <- contr_df[,.(filer_name,election_year,amount,office,position,jurisdiction,jurisdiction_county)]
contr_df[, filer_name_clean :=unlist(extract_clean_name(filer_name))]


# group by races and candidates
contr_grouped <- contr_df[,.(total= sum(amount)),by=.(filer_name_clean,election_year,office,position,jurisdiction,jurisdiction_county)]
setorderv(contr_grouped, cols = c("jurisdiction_county", "office","position","total"), order = c(1L,1L,1L,-1L)) # Sorts by Value descending, then ID ascending

# PACS
ind_df <- fread(paste0(money_folder,"pdc_ind_exp_2025.csv"))
ind_df <- as.data.table(ind_df)
colnames(ind_df)

# Filter to meaningful rows
ind_df <- ind_df[candidate_name!=""]
ind_pac_cand <- ind_df[,.(candidate_name,portion_of_amount,for_or_against,candidate_office,candidate_jurisdiction,sponsor_name)]
ind_pac_cand <- ind_pac_cand[,.(total=sum(portion_of_amount)),by=.(candidate_name,for_or_against,candidate_office,candidate_jurisdiction,sponsor_name)]
setorderv(ind_pac_cand, cols = c("for_or_against", "total"), order = c(1L,-1L)) # Sorts by Value descending, then ID ascending

contr_names <- data.table(name=unique(contr_grouped$filer_name))
pac_cand_names <- data.table(name=unique(ind_pac_cand$candidate_name))
pac_names <- data.table(name=unique(ind_pac_cand$sponsor_name))
  

# Try merging contribution totals on results
setnames(contr_grouped,old="filer_name_clean",new="Candidate")
all_results <- merge(all_results,contr_grouped,by="Candidate",all.x = T)
all_results <- unique(all_results)
setorderv(all_results, cols = c("County", "office","position","PercentageOfTotalVotes"), order = c(1L,1L,1L,-1L)) 



all_results_subset <- all_results[!is.na(total)]

# get percent of all raised
all_results_subset <- data.table(all_results_subset)
all_results_subset[,percent_raised_race:=total/sum(total),by=Race]
all_results_subset[,percent_raised_race:=100*percent_raised_race]


cor(all_results_subset$PercentageOfTotalVotes, all_results_subset$percent_raised_race,
    method = "spearman"
) # 0.5187363

# make a scatter plot
ggplot(all_results_subset,aes(x=percent_raised_race,y=PercentageOfTotalVotes))+
  geom_point()+
  geom_smooth(method = "lm")

# interesting cases
win_no_money <- all_results_subset[(PercentageOfTotalVotes>50)&(percent_raised_race<10)]
lose_with_money <- all_results_subset[(PercentageOfTotalVotes<25)&(percent_raised_race>75)]

all_results_subset[,loser_delta := percent_raised_race-PercentageOfTotalVotes]
king <- all_results_subset[County=="King"]
