import pandas as pd
import os


DATA_FOLDER = os.path.join(
    os.path.dirname(__file__), "../../data/lobbying/pdc_downloads/"
)
pdc_contributions_file = os.path.join(
    DATA_FOLDER, "pdc_contributions_2025_2025-11-05_name_cleaned_lat_long.csv"
)
ind_exp_output_file = os.path.join(
    DATA_FOLDER, "pdc_ind_exp_2025_2025-11-05_name_cleaned.csv"
)

contr_df = pd.read_csv(pdc_contributions_file)
ind_df = pd.read_csv(ind_exp_output_file)


# check names
contr_df[contr_df["filer_name"].str.contains("EDDIE")]["filer_name"].unique()
contr_df[contr_df["filer_name"].str.contains("DAVISON")]["filer_name"].unique()
