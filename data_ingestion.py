import requests
import re

from bs4 import BeautifulSoup
from datetime import datetime

# URL to scrape the data from.
url = "https://www.worldometers.info/coronavirus/country/south-africa/"

# HTTP Get reqeust to the URL.
response = requests.get(url)

# Only continue if a 200 response is returned.
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    # Get Date values from website
    date_script_tag = soup.find('script', string=re.compile(r'Highcharts.chart\('))

    if date_script_tag:
        # Extract the JavaScript code
        date_code = date_script_tag.string

        # Use regular expressions to extract the 'categories' data
        date_match = re.search(r'categories: \[(.*?)\]', date_code)

        if date_match:
            date_data = date_match.group(1)
            #print(date_data)

            # Split the categories data into a list
            web_date_data = date_data.split('","')

            # Trim whitespace and quotes from each category
            date_vals = [date.strip(" '\"") for date in web_date_data]
        else:
            print("Date data not found in JavaScript code.")
    else:
        print("Script tag containing JavaScript code not found.")

    # Get daily covid cases data from website
    pattern_cases = re.compile(r'series: \[\{[^}]*name:\s*\'Daily Cases\'[^}]*data:\s*\[([^]]*)\]', re.DOTALL)
    script_tag_cases = soup.find('script', string=pattern_cases)
    
    if script_tag_cases:
        script_content_cases = script_tag_cases.text
    
        # Extract the 'data' values
        data_match_cases = re.search(r'data:\s*\[([^]]*)\]', script_content_cases)
    
        if data_match_cases:
            data_values_cases = data_match_cases.group(1).strip().split(',')
            case_vals = [int(x) if x.strip().lower() != 'null' else 0 for x in data_match_cases.group(1).split(',')]
        else:
            print("Data not found within 'series'.")
    else:
        print("Script tag with 'series' property not found.")
    
    # Combine dates & new cases to one list in the form {date:x, value:y} for each date and corresponding case value.
    covid_date_case_data = []
    
    # Remove commas in date vals previous (month day, year) ; new (YYYY-mm-dd)
    new_date_vals = []
    for i in range(len(date_vals)):
        new_date_string = date_vals[i].replace(',','')
        new_date_val = datetime.strptime(new_date_string, "%b %d %Y")
        new_date = new_date_val.strftime("%Y-%m-%d")
        new_date_vals.append(new_date)
    for i in range(len(date_vals)):
        data_point = {
            'value': case_vals[i],
            'date': new_date_vals[i]
        }

        covid_date_case_data.append(data_point)

    #print(covid_date_case_data)
    #print()
else:
    print("Failed to retrieve the webpage. Status code:", response.status_code)