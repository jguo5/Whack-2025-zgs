#Jackleen Guo
#WHACK 2025
#Dataset cleaniing
#11-22-2025

library(dplyr)
library(tidyverse)

politicalData <- read.csv("C:\\Users\\iwuba\\Downloads\\WHACK2025\\NRI_Table_Counties.csv")
riskIndexData <- read.csv("C:\\Users\\iwuba\\Downloads\\WHACK2025\\YCOM_2024_publicdata.csv")
riskPerceptionData <- read.csv("C:\\Users\\iwuba\\Downloads\\WHACK2025\\countypres_2000-2024.csv")


#----------------risk index cleaning
riskIndexProcessed <- riskIndexData %>%
  filter(GeoType == "county") 

parts <- strsplit(riskIndexProcessed$GeoName, ",")

riskIndexProcessed$county_name <- sapply(parts, function(x) trimws(x[1]))
riskIndexProcessed$state <- sapply(parts, function(x) trimws(x[2]))

county_types <- c(
  "Borough",
  "Planning Region",
  "Census Area",
  "Municipality",
  "District",
  "Island",
  "Municipio",
  "Parish",
  "City",
  "City and Borough",
  "County"
)

county_types <- county_types[order(nchar(county_types), decreasing = TRUE)]

pattern <- paste0("(", str_c(county_types, collapse = "|"), ")$")

riskIndexProcessed <- riskIndexProcessed %>%
  mutate(
    county_type = str_extract(county_name, pattern),
    county_name = str_trim(str_remove(county_name, pattern))
  ) 

riskIndexProcessed <- riskIndexProcessed[, c(
  names(riskIndexProcessed)[1:3],                 # first three columns
  "county_name", "state", "county_type",               # the columns you want to insert
  setdiff(names(riskIndexProcessed), c(names(riskIndexProcessed)[1:3], "county_name", "state"))  # all remaining
)]

riskIndexProcessed <- riskIndexProcessed %>%
  rename(county_fips = GeoID ) %>%
  select(
    county_fips, 4:ncol(.)
  )

#---------------------Risk perception cleaning
riskPerceptionProcessed <- riskPerceptionData %>%
  mutate(
    county_name = str_to_title(str_to_lower(county_name)),
    state = str_to_title(str_to_lower(state))
    ) %>%
  select(
    -state_po
  ) %>%
  mutate(county_fips = as.numeric(county_fips))


#--------------------Political data cleaning
politicalDataProcessed <- politicalData %>%
  select(COUNTY, COUNTYTYPE, STATE, 9:ncol(.))

colnames(politicalDataProcessed) <- str_to_lower(colnames(politicalDataProcessed))

politicalDataProcessed <- politicalDataProcessed %>%
  rename(county_name = county,  county_type = countytype, county_fips = stcofips, population_political = population)

#---------------------match risk perception with risk index and political by county_fips

riskIndexJoin <- riskIndexProcessed %>%
  select(county_fips, 5:ncol(.)) %>%
  mutate(county_fips = as.numeric(county_fips))

politicalJoin <- politicalDataProcessed %>%
  select(4:ncol(.)) %>%
  mutate(county_fips = as.numeric(county_fips))

totalPerceptionIndexPolitical <- riskPerceptionProcessed %>%
  full_join(riskIndexJoin, by = "county_fips") %>%
  full_join(politicalJoin, by = "county_fips")


csv_file_path <- "C:/Users/iwuba/Downloads/WHACK2025/total_perception_index_political_dataset.csv"
write_csv(totalPerceptionIndexPolitical, file = csv_file_path) 


print(paste("Saved csv file to:", csv_file_path))




