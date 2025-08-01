## Load candidates by race and answer: 
# - which pacs are spending money for and against candidates?
# - who receives most from real estate?
# - who has most labor contributions?
# - who receives most from amazon?

rm(list = ls())
library(data.table)
library(ggplot2)
library(scales)
library(stringr)
library(patchwork)

# donations_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/seattle_mayor/')
# donations_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/seattle_council_no_9/')
# donations_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/county_executive/')
# donations_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/city_attorney/')
donations_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/seattle_district_2_school_dir/')

# race <- "Seattle Mayor"
# race <- "Seattle City Council Position No. 9"
# race <- "County Executive"
# race <- "City Attorney"
race <- "Seattle District 2 School Director"


election_yr <- 2025

pac_file <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/pac_spending/independent-expenditures-sponsors-table.csv')
output_folder <- paste0(getwd(),'/Documents/Just4Plots/outputs/plots/lobbying/')

files <- list.files(donations_folder)
pac_df <- fread(pac_file)

# check naming conventions between donations data and pac data
pac_df[candidate_name %like% 'Wilson']

outfile <- gsub(" ","_",tolower(race))
outfile <- gsub("\\.","",tolower(outfile))

# Load and format data
cand_no <- 1
data <- data.table()
all_candidates <- c()

for (i in 1:length(files)){
  df_tmp <- fread(paste0(donations_folder,files[i]))
  df_tmp <- as.data.table(df_tmp)
  df_tmp[,candidate_no := cand_no] 
  cand_name <- gsub(".csv","",files[i])
  cand_name <- strsplit(cand_name,"_")[[1]]
  cand_name <- cand_name[3:length(cand_name)]
  cand_name <- paste(cand_name,collapse=" ")
  cand_name <- str_to_title(cand_name)
  df_tmp[,candidate_name := cand_name] 
  cand_no <- cand_no+1
  all_candidates <- c(all_candidates,cand_name)
  data <- rbind(data,df_tmp)
  
}

# keep all candidates on all plots
all_candidates <- sort(all_candidates)

# format pac money
pac_df[,candidate_name := str_to_title(candidate_name)]
pac_df[,candidate_name := gsub("'","",candidate_name)]
pac_df <- pac_df[(election_year==election_yr)]
pac_df[,candidate_name := trimws(candidate_name)]
pac_df <- pac_df[candidate_name %in% unique(data$candidate_name)]
pac_df <- pac_df[,.(portion_of_amount=sum(portion_of_amount)),by=.(candidate_name,sponsor_name,for_or_against)]


# Make function that creates bar charts 
make_contribution_plot <- function(data, keywords, title_suffix) {
  ## Example case
  # data = data
  # keywords = labor_keys
  # title_suffix = "Labor Unions"
  # Convert relevant fields to lowercase
  data[, c("contributor_employer_name", "contributor_occupation", "contributor_name") := 
         lapply(.SD, tolower), .SDcols = c("contributor_employer_name", "contributor_occupation", "contributor_name")]
  
  
  # Find matching contributions
  matched <- data.table()
  for (key in keywords) {
    tmp <- data[grepl(key, contributor_name) | 
                  grepl(key, contributor_employer_name) | 
                  grepl(key, contributor_occupation)]
    matched <- rbind(matched, tmp)
  }
  matched <- unique(matched)
  
  # restrict to >=0 contributions
  matched <- matched[contributor_amount>=0]
  
  # make sure all candidates show up in plots, even if 0
  missing_cands <- data.table(candidate_name=all_candidates,contributor_amount=rep(0,length(all_candidates)))
  matched <- rbind(matched,missing_cands,fill=TRUE)
  
  # Make bar chart
  plot <- ggplot(matched, aes(x = candidate_name, y = contributor_amount)) +
    geom_col() +
    scale_y_continuous(labels = dollar) +
    labs(
      x = "Candidate",
      y = "Contributions total",
      title = paste("Donor Employer or Occupation related to", title_suffix)
    ) +
    theme_bw()
  
  return(plot)
}

# Preliminary exploration
# How many contributors with contributions <$250 state their occupation?
colnames(data)
data[contributor_occupation=="",.N]

data[(contributor_amount<250)&(contributor_occupation!=""),.N] # 236

table(data[(contributor_amount<250)&(contributor_occupation!="")]$contributor_occupation)

## - which PACs are spending for and against each candidate?
pac_plot <- ggplot(pac_df,aes(x=candidate_name,
                              y=portion_of_amount,
                              fill=sponsor_name))+
  geom_col()+
  scale_y_continuous(labels = dollar) +
  facet_wrap(~ for_or_against) +
  theme_bw()+
  theme(axis.text.x = element_text(angle = 45, hjust = 1, vjust = 1))+
  labs(
    x = "Candidate",
    y = "Expenditure Amount",
    title = "Independent Expenditure for and against Candidates"
  )
pac_plot

## - who receives most from real estate? Keywords: realtor, estate, developer
real_estate_keys <- c('realtor', 'real','estate', 'developer')
re_plot <- make_contribution_plot(data,real_estate_keys,"Real Estate")

## - who has most labor contributions?
labor_keys <- c('seiu', 'local','union','labor','teamsters','uaw')
labor_plot <- make_contribution_plot(data,labor_keys,"Labor Unions")

## - who receives most from amazon?
az_keys <- c('amazon', 'amz')
az_plt <- make_contribution_plot(data,az_keys,"Amazon")

# Combine plots onto one page
combined <- pac_plot / re_plot / labor_plot / az_plt +
  plot_annotation(title = race)

print(combined)

# Save as PDF
ggsave(paste0(output_folder,outfile,".pdf"), combined, width = 8, height = 16)

# Save as PNG
# ggsave("combined_plot.png", combined, width = 10, height = 8, dpi = 300)
