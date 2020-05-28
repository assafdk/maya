import tase
from datetime import datetime

tase.get_historical_data(start_date=datetime(2020,1,1),end_date=datetime(2020,5,27))
year = 2019
while year > 2000:
    tase.get_historical_data(start_date=datetime(year,1,1),end_date=datetime(year,12,31))
    year -= 1