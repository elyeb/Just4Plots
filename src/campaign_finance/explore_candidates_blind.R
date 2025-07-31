## Mask candidates names from contributions data and answer: 
# - who receives most from real estate?
# - who has most labor contributions?
# - who receives most from amazon?

rm(list = ls())
library(data.table)
library(ggplot2)
library(scales)

data_folder <- paste0(getwd(),'/Documents/Just4Plots/data/lobbying/')
files <- list.files(data_folder)

cand_no <- 1

data <- data.table()
for (i in 1:length(files)){
  df_tmp <- fread(paste0(data_folder,files[i]))
  df_tmp <- as.data.table(df_tmp)
  df_tmp[,candidate_no := cand_no] 
  cand_no <- cand_no+1
  data <- rbind(data,df_tmp)
}

# How many contributors with contributions <$250 state their occupation?
colnames(data)
data[contributor_occupation=="",.N]

data[(contributor_amount<250)&(contributor_occupation!=""),.N] # 236

table(data[(contributor_amount<250)&(contributor_occupation!="")]$contributor_occupation)

## - who receives most from real estate? Keywords: realtor, estate, developer
# convert fields to lowercase
data[, c("contributor_employer_name", "contributor_occupation","contributor_name") := lapply(.SD, tolower), 
     .SDcols = c("contributor_employer_name", "contributor_occupation","contributor_name")]


real_estate_keys <- c('realtor', 'real','estate', 'developer')

re_contributions <- data.table()
for (key in real_estate_keys){
  re_tmp <-  data[grepl(key, contributor_employer_name)|grepl(key, contributor_occupation)]
  re_contributions <- rbind(re_contributions,re_tmp)
}
re_contributions <- unique(re_contributions)

table(re_contributions$contributor_employer_name)
table(re_contributions$contributor_occupation) 

# make a bar chart 
data[,candidate_no := as.integer(candidate_no)]
re_contributions[,candidate_no := as.factor(candidate_no)]
re_plot <- ggplot(re_contributions,aes(x=candidate_no,y=contributor_amount))+
  geom_col()+
  scale_y_continuous(labels = dollar)+
  scale_x_discrete()+
  labs(x = "Candidate No.", 
       y = "Contributor amount",
       title = "Donor Employer or Occupation related to Real Estate",)+
  theme_bw()
print(re_plot)

## - who has most labor contributions?
labor_keys <- c('seiu', 'local','union','labor','teamsters')

lu_contributions <- data.table()
for (key in labor_keys){
  lu_tmp <-  data[grepl(key, contributor_name)|grepl(key, contributor_employer_name)|grepl(key, contributor_occupation)]
  lu_contributions <- rbind(lu_contributions,lu_tmp)
}
lu_contributions <- unique(lu_contributions)

table(lu_contributions$contributor_name)
table(lu_contributions$contributor_employer_name)
table(lu_contributions$contributor_occupation) 

# make a bar chart 
lu_contributions[,candidate_no := as.factor(candidate_no)]
re_plot <- ggplot(lu_contributions,aes(x=candidate_no,y=contributor_amount))+
  geom_col()+
  scale_y_continuous(labels = dollar)+
  scale_x_discrete()+
  labs(x = "Candidate No.", 
       y = "Contributor amount",
       title = "Donors Related to Labor Unions",)+
  theme_bw()
print(re_plot)

# - who receives most from amazon?
az_keys <- c('amazon', 'amz')

az_contributions <- data.table()
for (key in az_keys){
  az_tmp <-  data[grepl(key, contributor_name)|grepl(key, contributor_employer_name)|grepl(key, contributor_occupation)]
  az_contributions <- rbind(az_contributions,az_tmp)
}
az_contributions <- unique(az_contributions)

table(az_contributions$contributor_name)
table(az_contributions$contributor_employer_name)
table(az_contributions$contributor_occupation) 

# make a bar chart 
az_contributions[,candidate_no := as.factor(candidate_no)]
re_plot <- ggplot(az_contributions,aes(x=candidate_no,y=contributor_amount))+
  geom_col()+
  scale_y_continuous(labels = dollar)+
  scale_x_discrete()+
  labs(x = "Candidate No.", 
       y = "Contributor amount",
       title = "Donors Related to Amazon",)+
  theme_bw()
print(re_plot)
