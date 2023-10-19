import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import csv
import datetime
import math
import uvicorn

from datetime import date
from data_ingestion import covid_date_case_data
from statsmodels.tsa.arima.model import ARIMA
from fastapi import FastAPI
from typing import List

'''
Training Data:
- covid_date_case_data: Data from scraping worldometer website.
- covid_data_df: DataFrame of covid_date_case_data.
- updated_covid_data: sliced covid_data_df till the point worldometer stopped recording data.
- train: data values of updated_covid_data
'''
covid_data_df = pd.DataFrame(covid_date_case_data)
# As worldometer stopped recording and displaying data in April 2023, I will slice my data from that day and predict only the next 7 days in April
# Training data is used up until worldometer stopped adding data.
updated_covid_data = covid_data_df[:1158]
train = updated_covid_data.value

'''
Model Creating and Training:
- ARIMA model is used.
- model is trained on train data above
- n_periods: number of days to predict
- confidence: 95%
'''
model_arima = ARIMA(train, order= (1, 1, 1))
model_fit = model_arima.fit()

n_periods = 7 # Number of days to predict
fc = model_fit.predict(start= len(train), end= (len(train) + n_periods), exog=None, dynamic=False)
confint = model_fit.conf_int(alpha= 0.05)
index_of_fc = np.arange(len(train), len(train) + n_periods)
fc_series = pd.Series(fc, index=index_of_fc)
lower_series = pd.Series(confint[:][0], index=index_of_fc)
upper_series = pd.Series(confint[:][1], index=index_of_fc)

'''
Forecast Plotting and save to png:
- forecast_plot.png: forecast plotted. Data comes from predict() function for model.
- timeseries_predict.png: predictions plotted. Data comes from predicted_data that needs to be saved to csv_file
'''
# Forecasting timeseries plot and save to png
plt.plot(fc, label= 'prediction')
plt.plot(fc_series, label= 'forecast', linestyle= 'dashed')
plt.fill_between(fc_series.index, lower_series, upper_series, color='k', alpha= .15)
plt.title("Covid Forecasting")
plt.legend(loc= 'upper left', fontsize= 8)
plt.savefig("foreast_plot.png")
plt.clf() # clear plotting for prediction timeseries plotting

predicted_data = []

y = 0

for i in fc:
    # Reconstructing date for csv.
    date_start = date(2023, 4, 19)
    add_day = datetime.timedelta(days=y)
    new_date = date_start + add_day
    y += 1
    data = {
        'date': new_date.strftime("%Y-%m-%d"),
        # using math.ceil as scraped data was integer and not float32 or double or decimal. 
        # Also makes sense to me to use ceil() as 2.3 people would go to 3 people.
        'new_cases': math.ceil(i)
    }
    predicted_data.append(data)

# Plot and save predictions
dates = [entry['date'] for entry in predicted_data[1:]]
new_cases = [entry['new_cases'] for entry in predicted_data[1:]]
plt.plot(dates, new_cases, marker= 'o', linestyle= 'dotted', label= 'prediction')
plt.title("Covid Predictions")
plt.ylabel("Cases")
plt.xlabel("date")
plt.legend(loc= 'upper left', fontsize= 8)
plt.tight_layout()
plt.grid(True)
plt.xticks(rotation= 45)
plt.savefig("timeseries_predict.png")
#plt.show()

'''
Save predictions & dates to csv:
- data: prediction_data
- filename: predictions.csv
'''
csv_file = "predictions.csv"
csv_header = ['date','new_cases']
with open(csv_file, 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames= csv_header)
    writer.writeheader()
    writer.writerows(predicted_data[1:])
    
'''
Create endpoint for prediction data:
- Using FastAPI
- Using Uvicorn
'''


app = FastAPI()

@app.get('/predict')
async def predict() -> List[dict]:
    data = predicted_data[1:]
    return data

localhost = "127.0.0.1"
port = 8080
uvicorn.run(app, host= localhost, port= port)