import os
import datetime
import numpy as np
import numpy.ma as ma
from typing import Union
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timedelta as td
import pandas as pd
import fsspec
import requests
import warnings
from pysteps import motion


@dataclass
class NWCData:
    data: np.array
    mask: ma.masked_array
    time: np.array


def generate_nowcast_array(analysis_info: dict):
    nwc_data = NWCData(np.asarray(analysis_info["data"]),
                       ma.asarray(analysis_info["mask"]),
                       np.asarray(analysis_info["time"]))
    return nwc_data


def create_dict(data):
    dict = {"data": [data.data[0]], "mask": [data.mask_nodata[0]], "time": [data.dtime[0]]}
    return dict


def add_to_dict(dict, data):
    dict["data"].append(data.data[0])
    dict["mask"].append(data.mask_nodata[0])
    dict["time"].append(data.dtime[0])
    return dict


def validate_and_sort_filenames(filenames, start_time):
    wrong_file = False
    for i in range(len(filenames) - 1):
        f = os.path.split(filenames[i])[-1]
        ff = os.path.split(filenames[i + 1])[-1]
        date_obj = dt.strptime(f.split("-")[0], "%Y%m%d%H%M")
        date_obj_next = dt.strptime(ff.split("-")[0], "%Y%m%d%H%M")
        if (date_obj_next - date_obj).total_seconds() != 900:
            warnings.warn(f"File {filenames[i]} or {filenames[i + 1]} has wrong timestamp!")
            wrong_file = True
            continue
    sorted_filenames = [filename for filename in sorted(filenames, reverse=False)]
    if wrong_file:
        wrong_files = pick_files_by_datetime(filenames, start_time)
        if sorted_filenames == wrong_files:
            for check_f in sorted_filenames:
                if start_time in os.path.split(check_f)[-1]:
                    wrong_file = False
    return sorted_filenames, wrong_file


def pick_files_by_datetime(files: list, datetime_zero: str):
    datetime_zero = dt.strptime(datetime_zero, "%Y%m%d%H%M")
    datetimes = [datetime_zero - td(minutes=int(x)) for x in np.arange(0, 60, 15)]
    initial_files = [f for f in files for d in datetimes if d.strftime("%Y%m%d%H%M") in os.path.split(f)[-1]]
    initial_files.sort(key=lambda x: x.split('/')[-1])
    return initial_files


def generate_nowcast_times(starttime: str, time_freq: int = 15, end_time: int = 60):
    nowcast_times_str = [starttime]
    analysis_datetime = dt.strptime(starttime, '%Y%m%d%H%M')
    for x in np.arange(time_freq, end_time, time_freq):
        nwc_datetime = analysis_datetime - td(minutes=int(x))
        nowcast_times_str.append(dt.strftime(nwc_datetime, '%Y%m%d%H%M'))
    return nowcast_times_str


def generate_backup_data_path(path: str) -> str:
    stripped = os.path.split(path)[0]
    new_path = stripped + "/interpolated_rprate.grib2"
    return new_path


def fetch_data_file(file_path: Union[str, None], nwc_time: str, param: str):
    param_file = ""
    if not file_path:
        if param == 'rprate':
            param_file = 'interpolated_rprate.grib2'
        file_path = f"s3://routines-data.lake.fmi.fi/hrnwc/development/{nwc_time}/{param_file}"
    return file_path


def round_current_time_in_quarter():
    def round_dt(time):
        delta = time.minute % 15
        time = dt(time.year, time.month, time.day, time.hour, time.minute - delta)
        return time - td(minutes=30)
    now = dt.utcnow()
    now = round_dt(now)
    return now.strftime("%Y%m%d%H%M")


def pick_analysis_data_from_array(data_object):
    data_0h = data_object.data[0, :, :]
    time_0h = data_object.dtime[0]
    masked_data_0h = data_object.mask_nodata[0, :, :]
    return data_0h, masked_data_0h, time_0h


def convert_nan_to_zeros(data):
    nan_data = data.data
    for i in range(len(nan_data)):
        nan_val = np.where(np.isnan(nan_data[i]))
        nan_data[i][nan_val] = 0.0
    data.data = nan_data
    return data


def mask_missing_data(data: np.array, mask_nodata: np.array) -> np.array:
    data[~np.isfinite(mask_nodata)] = np.nan
    data[data == 9999] = np.nan
    return data


def calculate_wind_field(data, nodata):
    data[~np.isfinite(nodata)] = np.nan
    data[data == 9999] = np.nan
    oflow_method = motion.get_method("LK")
    V = oflow_method(data[:3, :, :])
    return V


def read_file_from_s3(data_file):
    uri = "simplecache::{}".format(data_file)
    endpoint_url = os.environ.get('S3_HOSTNAME', 'https://routines-data-prod.lake.fmi.fi')
    return fsspec.open_local(uri, s3={'anon': True, 'client_kwargs': {'endpoint_url': endpoint_url}})


def read_flash_txt_to_array(file_path):
    lines = pd.read_csv(file_path, sep=" ")
    return lines


def read_flash_obs(obstime, time_window):
    obstime = datetime.datetime.strptime(obstime, "%Y%m%d%H%M")
    timestr = obstime.strftime("%Y-%m-%dT%H:%M:%S")
    start_time = obstime - pd.DateOffset(minutes=time_window)
    older_obs = start_time - pd.DateOffset(minutes=time_window)
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
