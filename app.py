# Import dependencies
import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect, desc
from sqlalchemy.sql import label

from flask import Flask, jsonify

import matplotlib.pyplot as plt

# Database setup
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
# Save reference to the tables
Measurement = Base.classes.measurements
Stations = Base.classes.stations

# Create our session (link) from Python to the DB
session = Session(bind = engine)

# Getting the table names for each table
inspector = inspect(engine)
inspector.get_table_names()

# Get a list of column names and types - measurements
columns = inspector.get_columns('measurements')
for c in columns:
    print(c['name'], c["type"])

# Get a list of column names and types - stations
columns = inspector.get_columns('stations')
for c in columns:
    print(c['name'], c["type"])  

engine.execute('SELECT * FROM stations LIMIT 5').fetchall() 

engine.execute('SELECT * FROM measurements LIMIT 5').fetchall() 

# Select prcp & date for the last 12 months
results = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= '2017-01-01')

# create empty dict to populate# create 
data = {'date': [], 'prcp': []}

# populate dict with rows from results
for row in results:
    data['date'].append(row.date)
    data['prcp'].append(row.prcp)

# create pandas df from dict
prcp17 = pd.DataFrame(data['prcp'], columns = ['prcp'], index = data['date'])
print(prcp17.head())

prcp17.head()


# Write a function called `calc_temps` that will accept start date and end date in the format '%Y-%m-%d' # Write  
# and return the minimum, average, and maximum temperatures for that range of dates

#Use the `calc_temps` function to calculate the min, avg, and max temperatures for your trip using the 
#matching dates from the previous year (i.e. use "2017-01-01" if your trip start date was "2018-01-01")

def calc_temps(start_date, end_date):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """
    
    return session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
print(calc_temps('2017-02-28', '2017-03-05'))

# Plot the min, avg, and max temperature from your previous query as a bar chart.
# Use the average temperature as the bar height.
# Use the peak-to-peak (tmax-tmin) value as the y error bar (yerr).
temperatures = (calc_temps('2017-02-28', '2017-03-05'))
labels = ['TMIN', 'TAVE', 'TMAX']
df = pd.DataFrame.from_records(temperatures, columns=labels)

temp_chart = df[['TAVE']].plot(kind='bar', title ="Temperatures in Hawaii", figsize=(5, 7), legend=True, fontsize=12, grid=True, color='lightblue')
temp_chart.set_xlabel("Temprature Avg", fontsize=12)
temp_chart.set_ylabel("Temperatures in Farenheit", fontsize=12)
# plt.show()

# Total number of stations
stations_results = session.query(func.count(Stations.station)).all()
print("There are " + str(stations_results[0]) + " stations.")

# Most active stations
active_results = session.query(Measurement.station,
    label('date', func.count(Measurement.date))).group_by(Measurement.station).all()
for result in active_results:
    print(result)

### List stations and obs counts in descending order
desc_order = session.query(Measurement.station, func.count(Measurement.tobs)).group_by(Measurement.station).order_by(func.count(Measurement.tobs).desc())
for result in desc_order:
    print(result)

### Which station has highest number of observations### Whic 
obsv_num = session.query(Measurement.station, func.count(Measurement.tobs)).group_by(Measurement.station).order_by(func.count(Measurement.tobs).desc()).first()
print(obsv_num) 

# Retrieve last 12 months of temp obs data (tobs)
temps = session.query(Measurement.station, Measurement.date, Measurement.tobs).\
    filter(Measurement.date > '2017-01-06').\
    order_by(Measurement.date).all()
temps

### Filter by station with highest number of observations
highest_obs = session.query(Measurement.station, Measurement.tobs).\
    filter(Measurement.date > '2017-01-01').\
    group_by(Measurement.station).\
    order_by(func.count(Measurement.tobs).desc()).all()
highest_obs

### Plot results as histogram with bins=12
df = pd.DataFrame(temps, columns=['Station', 'date', 'temp'])
df.set_index('Station', inplace=True)
df.head()

hist_plot = df['temp'].hist(bins=12, figsize=(15,10))
hist_plot.set_title('Temperature Observations', fontsize=20)
hist_plot.set_ylabel('Frequency', fontsize=20)
# plt.show()

# Flask Setup
app = Flask(__name__)

@app.route(("/"))
def welcome1():
    """Listing of the available API routes"""
    return(
        f"Available Routes: <br/>"
        f"/api/v1.0/precipitation <br/>"
        f"/api/v1.0/stations <br/>"
        f"/api/v1.0/tobs <br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>")

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Query for the dates and temps for the last year"""
    
    # Query the database for dates and tobs
    prcp_results = session.query(Measurement.date, Measurement.tobs).\
    filter(Measurement.date > '2017-01-01').all()
    
    # Create dictionary from row data and append to the list 'all_prcp'
    all_prcp = []
    for prcp in prcp_results:
        prcp_dict = {}
        prcp_dict["Date"] = Measurement.date
        prcp_dict["TOBS"] = Measurement.tobs
        all_prcp.append(prcp_dict)
    return jsonify(all_prcp)

@app.route("/api/v1.0/stations")
def stations():
    """Returns a list of stations from the dataset in JSON format"""
    
    station_results = session.query(Stations.station).all()
    
    # Convert the list of tuples into a normal list:
    all_stations = list(np.ravel(station_results))
    
    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    """Returns a list of temperature observations from the last year in JSON format """
    
    #Query database for tobs for last year
    tobs_results = session.query(Measurement.tobs).filter(Measurement.date > '2017-01-01').all()
    
    # Convert the list of tuples into normal list:
    all_tobs = list(np.ravel(tobs_results))
    
    return jsonify(all_tobs)

if __name__ == '__main__':
    app.run(debug=True)