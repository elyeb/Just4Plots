## Load results and campaign finance data and answer: 
# - how correlated were donations (with and without PACs) with winning?
# - which pacs won/lost?

rm(list = ls())
library(data.table)
library(ggplot2)
library(scales)
library(stringr)
library(patchwork)
library(dplyr)
library(plotly)
options(scipen = 999)


## Paths
data_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/election_results/primary_2025/')

plot_path <- paste0(getwd(),'/Documents/Just4Plots/outputs/plots/lobbying/')

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
                   "David Robert Shelvey (David R. Shelvey)"="David R. Shelvey",
                   "Deborah K Edwards (Debbie Edwards)"="Debbie Edwards",
                   "Devin Myles Leshin (Devin Leshin)"="Devin Leshin",
                   "Diodato (Dio) Boucsieguez (Dio Boucsieguez)"="Dio Boucsieguez",
                   "Don L. Rivers (Don L Rivers)"="Don L Rivers",
                   "Dorothy Ellen Talbo (Ellen Talbo)"="Ellen Talbo",
                   "Dung Thi Tuyet Ho (Jane Ho)"="Jane Ho",
                   "Edward C. Lin (Eddie Lin)"="Eddie Lin",
                   "Edward C. Lin (Edward Lin)"="Eddie Lin"
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



## Get election results data

list.files(data_folder)

all_results <- data.table()

for (f in list.files(data_folder)){
  tmp <- fread(paste0(data_folder,f))
  all_results <- rbind(all_results,tmp,fill = TRUE)
}

# check for duplicated names
dups <- all_results[duplicated(Candidate)]
dups <- dups[!(Candidate %in% c("Approved","WRITE-IN","Rejected","Yes","No","YES","NO",
                                "Levy Yes","Levy No","Levy...Yes","Levy...No"))]
check_dups <- all_results[Candidate %in% dups$Candidate]

# Therre are names and races, e.g. Arun Sharma for NORTHSHORE SCHOOL DISTRICT NO. 417 Director District No. 1,
# that contain two entries for different counties (King and Snohomish). I need to assume that these are the
# same race, and the vote totals/percents are county-specific. I will group and retally totals
check_dups_county_agnostic <- check_dups[,.(Votes=sum(Votes)),by=.(Candidate,Party)]

# PercentageOfTotalVotes=Votes/sum(Votes)
# Work in progress. For now just keep first entry
check_dups <- check_dups %>%
  distinct(Candidate, .keep_all = TRUE)

all_results_not_dups <- all_results[!(Candidate %in% check_dups$Candidate)]
all_results <- rbind(all_results_not_dups,check_dups)

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

# first apply manually-corrrected names
contr_df[,filer_name:=trimws(filer_name)]
contr_df[filer_name %in% names(name_remap)]$filer_name <- unlist(name_remap[contr_df[filer_name %in% names(name_remap),filer_name]])
# Extract rest with function
contr_df[, filer_name_clean :=unlist(extract_clean_name(filer_name))]


# group by races and candidates
contr_grouped <- contr_df[,.(total= sum(amount)),by=.(filer_name_clean,election_year,office,position,jurisdiction,jurisdiction_county)]
setorderv(contr_grouped, cols = c("jurisdiction_county", "office","position","total"), order = c(1L,1L,1L,-1L)) # Sorts by Value descending, then ID ascending

# PACS
ind_df <- fread(paste0(money_folder,"pdc_ind_exp_2025.csv"))
ind_df <- as.data.table(ind_df)
colnames(ind_df)

remap_pac_names <- {
  "DEMOCRATIC WOODINVILLE SPONSORED BY JEFFREY LYON"="DEMOCRATIC WOODINVILLE SPONSORED BY JEFF LYON"
}
ind_df[sponsor_name=="DEMOCRATIC WOODINVILLE SPONSORED BY JEFFREY LYON",sponsor_name:="DEMOCRATIC WOODINVILLE SPONSORED BY JEFF LYON"]

# Filter to meaningful rows
ind_df <- ind_df[candidate_name!=""]
ind_pac_cand <- ind_df[,.(candidate_name,portion_of_amount,for_or_against,candidate_office,candidate_jurisdiction,sponsor_name)]
ind_pac_cand <- ind_pac_cand[,.(total=sum(portion_of_amount)),by=.(candidate_name,for_or_against,candidate_office,candidate_jurisdiction,sponsor_name)]
setorderv(ind_pac_cand, cols = c("for_or_against", "total"), order = c(1L,-1L)) # Sorts by Value descending, then ID ascending
ind_pac_cand <- unique(ind_pac_cand)

contr_names <- data.table(name=unique(contr_grouped$filer_name))
pac_cand_names <- data.table(name=unique(ind_pac_cand$candidate_name))
pac_names <- data.table(name=unique(ind_pac_cand$sponsor_name))
  

# Try merging contribution totals on results
setnames(contr_grouped,old="filer_name_clean",new="Candidate")
all_results <- merge(all_results,contr_grouped,by="Candidate",all.x = T)
all_results <- unique(all_results)
setorderv(all_results, cols = c("County", "office","position","PercentageOfTotalVotes"), order = c(1L,1L,1L,-1L)) 

# mark as winner T/F candidates who got largest percent of votes in race
all_results[,win_total:=max(PercentageOfTotalVotes),by=Race]
all_results[,win:=PercentageOfTotalVotes==win_total]
all_results$win_total <- NULL

all_results_subset <- all_results[!is.na(total)]

# get percent of all raised
all_results_subset <- data.table(all_results_subset)
all_results_subset[,percent_raised_race:=total/sum(total),by=Race]
all_results_subset[,percent_raised_race:=100*percent_raised_race]


cor(all_results_subset$PercentageOfTotalVotes, all_results_subset$percent_raised_race,
    method = "spearman"
) # 0.5089106

# make a scatter plot
ggplot(all_results_subset,aes(x=percent_raised_race,y=PercentageOfTotalVotes))+
  geom_point()+
  geom_smooth(method = "lm")

# interesting cases
win_no_money <- all_results_subset[(PercentageOfTotalVotes>50)&(percent_raised_race<10)]
lose_with_money <- all_results_subset[(PercentageOfTotalVotes<25)&(percent_raised_race>75)]

all_results_subset[,votes_v_money := PercentageOfTotalVotes-percent_raised_race]
king <- all_results_subset[County=="King"]

## - which PACS won/lost?
all_results_win_loss <- all_results[,.(Candidate,win,PercentageOfTotalVotes,total)]
setnames(all_results_win_loss,old=c("Candidate","win","PercentageOfTotalVotes","total"),new=c("candidate_name","win","vote_percent","campaign_contributions"))
all_results_win_loss <- unique(all_results_win_loss)

ind_pac_cand <- merge(ind_pac_cand,all_results_win_loss,by="candidate_name",all.x = T)
ind_pac_cand <- unique(ind_pac_cand)
ind_pac_cand <- ind_pac_cand[!is.na(win)]

# summarize wins and total by pac
# table(ind_pac_cand$sponsor_name,ind_pac_cand$win)
ind_pac_results <- ind_pac_cand[
  , .(
    total_spent = sum(total, na.rm = TRUE),
    candidates_won_count   = sum(win == TRUE),
    candidates_lost_count  = sum(win == FALSE)
  ),
  by = .(sponsor_name,for_or_against)
]

setorderv(ind_pac_results, cols = c("sponsor_name","for_or_against"), order = c(1L,1L))

ind_pac_wl <- ind_pac_results

define_win <- function(for_or_against, won_count, lost_count) {
  # if for_or_against is a factor, safer to coerce to character
  ifelse(as.character(for_or_against) == "For", won_count, lost_count)
}
define_loss <- function(for_or_against, won_count, lost_count) {
  ifelse(as.character(for_or_against) == "Against", won_count, lost_count)
}

# assign in place
ind_pac_wl[, pac_won := define_win(for_or_against, candidates_won_count, candidates_lost_count)]
ind_pac_wl[, pac_lost := define_loss(for_or_against, candidates_won_count, candidates_lost_count)]

# aggregate
ind_pac_wl_agg <- ind_pac_wl[,.(pac_won=sum(pac_won),pac_lost=sum(pac_lost),total_spent=sum(total_spent)),by=.(sponsor_name)]
ind_pac_wl_agg[,percent_won := pac_won/(pac_won+pac_lost)] 
ind_pac_wl_agg[,percent_won_over_spend := percent_won/total_spent] 
ind_pac_wl_agg[,win_minus_loss := pac_won-pac_lost] 
ind_pac_wl_agg[,win_minus_loss_times_spend := win_minus_loss*total_spent] 


cor(ind_pac_wl_agg$total_spent,ind_pac_wl_agg$win_minus_loss,
    method = "spearman"
) #-0.01701551

# make a scatter plot
ggplot(ind_pac_wl_agg,aes(x=total_spent,y=win_minus_loss))+
  geom_point()+
  geom_smooth(method = "lm")

# win_minus_loss_times_spend seems like a good way to rank the PAC's election performance, though
# the number itself doesn't mean a whole lot.
plot_df <- ind_pac_wl_agg[,.(sponsor_name,win_minus_loss_times_spend,pac_won,pac_lost,win_minus_loss,total_spent)]
setnames(plot_df,old=c("pac_won","pac_lost","win_minus_loss"),new=c("races_won","races_lost","net_wins"))

# Order sponsor_name by win_minus_loss_times_spend
plot_df[, sponsor_name := factor(
  sponsor_name,
  levels = plot_df[order(win_minus_loss_times_spend), sponsor_name]
)]

# Identify most and least according to win_minus_loss_times_spend
most <- plot_df[which.max(win_minus_loss_times_spend)]
least <- plot_df[which.min(win_minus_loss_times_spend)]

# -------------------
# Diverging Bar Chart
# -------------------
p1 <- ggplot(plot_df, aes(x = sponsor_name, y = net_wins, fill = net_wins > 0,text=total_spent)) +
  geom_bar(stat = "identity") +
  scale_fill_manual(values = c("TRUE" = "blue", "FALSE" = "red"),
                    labels = c("Loss net", "Win net")) +
  labs(
    x = "Sponsor Name",
    y = "Net Wins (Wins - Losses)",
    title = "Net Wins by Sponsor",
    subtitle = "Ranked by Wins minus Losses times Total Spent",
    fill = "Result"
  ) +
  coord_flip() +
  theme_minimal()
p1
ggplotly(p1, tooltip = "text")
# -------------------
# Scatter Plot 
# -------------------=
p2 <- ggplot(
  plot_df,
  aes(
    x = total_spent,
    y = net_wins,
    size = total_spent,
    text = sponsor_name,
    color = net_wins > 0
  )
) +
  geom_point(alpha = 0.7) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "gray40") +
  scale_color_manual(values = c("FALSE" = "gray", "TRUE" = "purple"), guide = FALSE) +
  labs(
    x = "Total Spent",
    y = "Net Races Won",
    title = "Wins minus Losses by Total Spent",
    subtitle = "Point size = Total Spent"
  ) +
  scale_x_continuous(labels = scales::comma) +
  scale_size(range = c(6, 20)) +  # increase dot size range
  theme_minimal(base_size = 18) +  # bigger base font size
  theme(
    axis.line = element_line(color = "black", size = 1.2),
    panel.grid = element_blank(),
    legend.position = "none",
    axis.title = element_text(size = 20),
    axis.text = element_text(size = 16),
    plot.title = element_text(size = 26, face = "bold"),
    plot.subtitle = element_text(size = 20)
  )

interactive_plot <- plotly::ggplotly(p2, tooltip = "text")
interactive_plot
htmlwidgets::saveWidget(interactive_plot, paste0(plot_path,"2025_primary_pac_win_loss.html"))

