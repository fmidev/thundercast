import os
import numpy as np
import numpy.ma as ma
from typing import Union
from dataclasses import dataclass
from datetime import datetime as dt
from datetime import timedelta as td
import pandas as pd
import fsspec


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


def pick_files_by_datetime(files: list, datetime_zero: str):
    datetime_zero = dt.strptime(datetime_zero, "%Y%m%d%H")
    datetimes = [datetime_zero - td(hours=int(x)) for x in range(5)]
    initial_files = [f for f in files for d in datetimes if d.strftime("%Y%m%d%H") in f]
    initial_files.sort()
    return initial_files


def fetch_wanted_date_files(param: str, datetime_zero: str, path: Union[str, None] = None):
    initial_files = []
    nwc_times = generate_nowcast_times(datetime_zero)
    for nwc_t in nwc_times:
        initial_files.append(fetch_data_file(path, nwc_t, param))
    return initial_files


def generate_nowcast_times(analysis_time: str, time_freq: int = 15, end_time: int = 60):
    nowcast_times_str = [analysis_time]
    analysis_datetime = dt.strptime(analysis_time, '%Y%m%d%H%M')
    for x in np.arange(time_freq, end_time, time_freq):
        nwc_datetime = analysis_datetime - td(minutes=int(x))
        nowcast_times_str.append(dt.strftime(nwc_datetime, '%Y%m%d%H%M'))
    nowcast_times_str.sort()
    return nowcast_times_str

# TODO: poisto kovakoodaukset
def fetch_data_file(file_path: Union[str, None], file_date: str, param: str):
    if not file_path:
        pwd = os.getcwd()
        pwd = os.path.split(pwd)[0]
        file_path = f"{pwd}/data/{param}_data/NWC_15/{file_date}/"
    data_file = os.listdir(file_path)
    return file_path + data_file[0]


def pick_analysis_data_from_array(data_object):
    data_0h = data_object.data[0, :, :]
    time_0h = data_object.dtime[0]
    masked_data_0h = data_object.mask_nodata[0, :, :]
    return data_0h, masked_data_0h, time_0h


def convert_nan_to_zeros(data):
    nan_data = data.data_f
    for i in range(len(nan_data)):
        nan_val = np.where(np.isnan(nan_data[i]))
        nan_data[i][nan_val] = 0.0
    data.data_f = nan_data
    return data


def read_file_from_s3(data_file):
    uri = "simplecache::{}".format(data_file)
    return fsspec.open_local(uri, s3={'anon': True, 'client_kwargs': {'endpoint_url': 'https://lake.fmi.fi'}})


def read_flash_txt_to_array(file_path):
    lines = pd.read_csv(file_path, sep=" ")
    return lines


# TODO: Siivoa pois virallisesta versiosta
def read_obs():
    """Read observations from smartmet server"""
    flash_file = f'/home/korpinen/Documents/STU_kehitys/ukkosen_tod/data/flash_data/202207131515_flashObs.txt'
    flash_data = read_flash_txt_to_array(flash_file)
    return flash_data["longitude"], flash_data["latitude"]
