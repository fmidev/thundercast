import gridpp
import numpy as np
import sys
import requests
import datetime
import pandas as pd
from file_utils import ReadData


class Analysis:
    def __init__(self, origin_file):
        self.obs = None
        self.points = None
        self.output = None
        self.longitudes = None
        self.latitudes = None
        self.origin_file = origin_file
        self.generate_analysis_field()

    def generate_analysis_field(self):
        # grid, lons, lats, background, analysistime, forecasttime
        data = ReadData(self.origin_file, read_coordinates=True)
        self.generate_background_params(data)
        grid = self.read_grid(data)
        background = np.zeros(data.data[0].shape)
        # Read observations from smartmet server
        print("Reading observation data")
        flash_time = datetime.datetime(2022, 7, 13, 15, 15, 00)
        self.points, self.obs = self.read_obs(data.forecast_time, flash_time)
        self.output = self.interpolate(grid, background, 'flash')

    def read_grid(self, data):
        """Top function to read all gridded data"""
        topo = np.zeros(data.longitudes.shape)
        grid = gridpp.Grid(data.latitudes, data.longitudes, topo)
        return grid

    def read_obs(self, obstime, flash_time=None):
        """Read observations from smartmet server"""
        obs = self.read_flash_obs(obstime, flash_time)
        points = gridpp.Points(obs["latitude"].to_numpy(),
                               obs["longitude"].to_numpy(),
                               obs["elevation"].to_numpy(),)
        return points, obs

    def read_flash_obs(self, obstime, flash_time=None, timewindow=20):
        timestr = obstime.strftime("%Y-%m-%dT%H:%M:%S")
        start_time = obstime - pd.DateOffset(minutes=timewindow)
        if flash_time:
            timestr = flash_time.strftime("%Y-%m-%dT%H:%M:%S")
            start_time = flash_time - pd.DateOffset(minutes=timewindow)
        end_tstr = timestr
        start_tstr = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        url = "http://smartmet.fmi.fi/timeseries?producer={}&tz=gmt&starttime={}&endtime={}&param=flash_id,longitude,latitude,utctime,altitude,peak_current&format=json".format(
            "flash", start_tstr, end_tstr)
        resp = requests.get(url)
        trad_obs = resp.json()

        obs = pd.DataFrame(trad_obs)
        obs.rename(columns={"flash_id": "station_id",
                            "peak_current": "flash",
                            "altitude": "elevation"}, inplace=True)
        obs = obs.assign(flash=100.0)
        obs = obs.assign(elevation=0.0)

        count = len(trad_obs)
        if count == 0:
            print("Unable to proceed")
            sys.exit(1)
        return obs

    def interpolate(self, grid, background, param):
        """Perform optimal interpolation"""
        # Interpolate background data to observation points
        pobs = gridpp.nearest(grid, self.points, background)
        pobs = pobs.astype(np.float)
        structure = gridpp.BarnesStructure(10000, 200)
        max_points = 20
        obs_to_background_variance_ratio = np.full(self.points.size(), 0.01)
        print("Performing optimal interpolation")
        output = gridpp.optimal_interpolation(grid, background, self.points,
                                              self.obs[param].to_numpy(),
                                              obs_to_background_variance_ratio,
                                              pobs, structure, max_points,)
        output[output > 100] = 100
        output[output < 10] = 10
        return output
    
    def generate_background_params(self, data):
        self.latitudes = data.latitudes
        self.longitudes = data.longitudes
        