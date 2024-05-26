from pytrends.request import TrendReq

# Connect to Google
pytrends = TrendReq(hl="en-US", tz=360)

# Define the keywords
kw_list = ["Python"]

# Build the payload
pytrends.build_payload(kw_list, cat=0, timeframe="today 1-m", geo="", gprop="")

# Get interest over time
interest_over_time_df = pytrends.interest_over_time()

print(interest_over_time_df.head())
# Output the whole dataframe as text
print(interest_over_time_df.to_string())
