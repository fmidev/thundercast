import gridpp
import numpy as np
import requests
import pandas as pd
from datetime import datetime as dt
from file_utils import ReadData


class Analysis:
    def __init__(self, origin_file, obs_time, time_window):
        self.obs = None
        self.points = None
        self.output = None
        self.longitudes = None
        self.latitudes = None
        self.template = None
        self.origin_file = origin_file
        self.obs_time = obs_time
        self.time_window = time_window
        self.generate_analysis_field()

    def generate_analysis_field(self):
        data = ReadData(self.origin_file, read_coordinates=True, use_as_template=True)
        self.template = data.template
        self.generate_background_params(data)
        grid = self.read_grid(data)
        #background = np.zeros(data.data[0].shape)
        background = self.get_background_data(data)
        # Read observations from smartmet server
        print("Reading observation data")
        self.points, self.obs = self.read_obs()
        self.output = self.interpolate(grid, background, 'flash')

    @staticmethod
    def get_background_data(data):
        background = data.data[0]
        background[background > 100] = 100
        background[background < 10] = 0
        return background

    def read_grid(self, data):
        """Top function to read all gridded data"""
        topo = np.zeros(data.longitudes.shape)
        grid = gridpp.Grid(data.latitudes, data.longitudes, topo)
        return grid

    def read_obs(self):
        """Read observations from smartmet server"""
        obs = self.read_flash_obs()
        points = gridpp.Points(obs["latitude"].to_numpy(),
                               obs["longitude"].to_numpy(),
                               obs["elevation"].to_numpy(),)
        return points, obs

    def read_flash_obs(self):
        analysis_time = dt.strptime(self.obs_time, '%Y%m%d%H%M')
        timestr = analysis_time.strftime("%Y-%m-%dT%H:%M:%S")
        start_time = analysis_time - pd.DateOffset(minutes=self.time_window)
        older_obs = start_time - pd.DateOffset(minutes=self.time_window)
        end_tstr = timestr
        start_tstr = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        older_tstr = older_obs.strftime("%Y-%m-%dT%H:%M:%S")
        url = "http://smartmet.fmi.fi/timeseries?producer={}&tz=gmt&starttime={}&endtime={}&param=flash_id,longitude,latitude,utctime,altitude,peak_current&format=json".format(
            "flash", start_tstr, end_tstr)
        resp = requests.get(url)
        trad_obs = resp.json()
        obs = pd.DataFrame(trad_obs)
        obs.rename(columns={"flash_id": "station_id",
                            "peak_current": "flash",
                            "altitude": "elevation"}, inplace=True)
        if len(obs) == 0:
            obs = obs.assign(latitude=np.nan)
            obs = obs.assign(longitude=np.nan)
        obs = obs.assign(flash=100.0)
        obs = obs.assign(elevation=0.0)

        url_old = "http://smartmet.fmi.fi/timeseries?producer={}&tz=gmt&starttime={}&endtime={}&param=flash_id,longitude,latitude,utctime,altitude,peak_current&format=json".format(
            "flash", older_tstr, start_tstr)
        resp_old = requests.get(url_old)
        trad_obs_old = resp_old.json()
        obs_old = pd.DataFrame(trad_obs_old)
        obs_old.rename(columns={"flash_id": "station_id",
                            "peak_current": "flash",
                            "altitude": "elevation"}, inplace=True)
        if len(obs_old) == 0:
            obs_old = obs_old.assign(latitude=np.nan)
            obs_old = obs_old.assign(longitude=np.nan)
        obs_old = obs_old.assign(flash=40.0)
        obs_old = obs_old.assign(elevation=0.0)
        result = pd.concat([obs, obs_old])

        count = len(trad_obs)
        count_old = len(trad_obs_old)
        if count == 0:
            print("No near real time observations")
        if count_old == 0:
            print("No observations at all from select times")
        return result

    def interpolate(self, grid, background, param):
        """Perform optimal interpolation"""
        # Interpolate background data to observation points
        pobs = gridpp.nearest(grid, self.points, background)
        structure = gridpp.BarnesStructure(20500, 200)
        max_points = 20
        obs_to_background_variance_ratio = np.full(self.points.size(), 0.1)
        print("Performing optimal interpolation")
        output = gridpp.optimal_interpolation(grid, background, self.points,
                                              self.obs[param].to_numpy(),
                                              obs_to_background_variance_ratio,
                                              pobs, structure, max_points,)
        output[output > 100] = 100
        output[output < 10] = 0
        return output
    
    def generate_background_params(self, data):
        self.latitudes = data.latitudes
        self.longitudes = data.longitudes
        