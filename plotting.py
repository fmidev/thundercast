import os
import numpy as np
import argparse
import matplotlib.pyplot as plt
from datetime import datetime as dt
from datetime import timedelta as td
from mpl_toolkits.basemap import Basemap
import cartopy
from file_utils import ReadDataPlotting, ReadData
import tools as tl


def main():
    pwd = os.getcwd()
    pwd = os.path.split(pwd)[0]
    fig_out = f"{pwd}/POT_developing/figures/"
    if os.path.isdir(fig_out) is False:
        os.mkdir(fig_out)

    args = parse_command_line()
    wind = None
    flash_obs = None
    if args.analysis is True:
        analysis_info = {}
        initial_files = [args.rprate_3_file,
                         args.rprate_2_file,
                         args.rprate_1_file]
        for i, data_file in enumerate(initial_files):
            data = ReadData(data_file)
            data_0h, mask_data_0h, time_0h = tl.pick_analysis_data_from_array(data)
            if i == 0:
                analysis_info = {"data": [data_0h], "mask": [mask_data_0h], "time": [time_0h]}
            else:
                analysis_info["data"].append(data_0h)
                analysis_info["mask"].append(mask_data_0h)
        nwc_data = tl.generate_nowcast_array(analysis_info)
        wind = tl.calculate_wind_field(nwc_data.data, nwc_data.mask)
        flash_obs = tl.read_flash_obs(args.analysis_time, args.obs_time_window)
    plot_contourf_map_scandinavia(args.data_file, fig_out, "Probability of thunder nwc 15min 1km",
                                  obs=flash_obs, wind=wind)


def parse_command_line():
    parser = argparse.ArgumentParser(argument_default=None)
    parser.add_argument("--data_file", action="store", type=str, required=True)
    parser.add_argument("--obs_time_window", action="store", type=int, required=True)
    parser.add_argument("--analysis", action="store_true", default=False)
    parser.add_argument("--analysis_time", action="store", type=str, required=False)
    parser.add_argument("--rprate_1_file", action="store", type=str, required=False)
    parser.add_argument("--rprate_2_file", action="store", type=str, required=False)
    parser.add_argument("--rprate_3_file", action="store", type=str, required=False)
    args = parser.parse_args()
    return args


def plot_contourf_map_scandinavia(data, outfile, title, obs=None,
                                       wind=None, vmin=0, vmax=100):
    """Use for plotting when projection is Lambert etc.

    For xarray to work with grib-files, cfgrib must be installed
    """
    if isinstance(data, str):
        data = ReadDataPlotting(data)
    lon = data.longitudes
    lat = data.latitudes
    fig_date = data.analysis_time
    for i, data_field in enumerate(data.data):
        minute = 0
        if i > 0:
            minute = 15 * i
            fig_date = fig_date + td(minutes=int(15))
        lon[lon > 180] = lon[lon > 180] - 360
        proj = cartopy.crs.LambertConformal(central_latitude=int(np.mean(lat)),
                                            central_longitude=int(np.mean(lon)),
                                            standard_parallels=(25, 25))
        ax = generate_fig(proj)
        if i == 0:
            cm = ax.pcolormesh(lon, lat, data_field, transform=cartopy.crs.PlateCarree(),
                               shading='auto', vmin=vmin, vmax=vmax, cmap='Blues')
            if obs is not None:
                lons = obs['longitude']
                lats = obs['latitude']
                ax.scatter(lons, lats, zorder=1, alpha=0.3, c='r', s=3,
                           transform=cartopy.crs.PlateCarree())
            if wind is not None:
                ax.quiver(lon[::100, ::100], lat[::100, ::100], wind[0][::100, ::100],
                          wind[-1][::100, ::100], transform=cartopy.crs.PlateCarree())
        else:
            cm = ax.pcolormesh(lon, lat, data_field, transform=cartopy.crs.PlateCarree(),
                               shading='auto', vmin=vmin, vmax=vmax, cmap='Blues')
            if wind is not None:
                ax.quiver(lon[::100, ::100], lat[::100, ::100], wind[0][::100, ::100],
                          wind[-1][::100, ::100], transform=cartopy.crs.PlateCarree())
        plt.title(f"{title} {dt.strftime(fig_date, '%Y-%m-%d %H:%M')},\n Analysistime {data.analysis_time}, forecast + {minute}min)")
        plt.colorbar(cm, fraction=0.046, pad=0.04, orientation="horizontal")
        forecast_outfile = outfile + f"POT_{i}_{dt.strftime(data.analysis_time, '%Y%m%d%H%M')}+{i*15}min.png"
        plt.savefig(forecast_outfile, bbox_inches='tight', pad_inches=0.2, dpi=300)
        plt.close()
        print(f"Done plotting fig {i+1}/17)")


def plot_NWC_data_imshow_polster(data, outfile, title, obs=None,
                                       wind=None, vmin=0, vmax=100):
    """Use for plotting when projection is Polster/Polar_stereografic

    Only for Scandinavian domain. For other domains coordinates must be changed.
    """
    if isinstance(data, str):
        data = ReadDataPlotting(data)
    cmap = 'Blues'  # RdBl_r  'Blues' 'Jet' 'RdYlGn_r'
    lon = data.longitudes
    lat = data.latitudes
    fig_date = data.analysis_time
    for i in range(len(data.data)):
        minute = 0
        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        if i > 0:
            minute = 15*i
            fig_date = fig_date + td(minutes=int(15))
        # '+proj=lcc +lat_0=0.0 +lat_1=63.3 +lat_2=63.3 +lon_0=15.0 +ellps=WGS84 +no_defs +x_0=0.0 +y_0=0.0'
        m = Basemap(width=1800000, height=2115000,
                    resolution='l', rsphere=(6378137.00,6356752.3142),
                    projection='lcc', ellps='WGS84',
                    lat_1=63.3, lat_2=63.3, lat_0=63.3, lon_0=20.0, ax=ax)
        m.drawcountries(linewidth=1.0)
        m.drawcoastlines(1.0)
        d = data.data[i, :, :]
        x, y = m(lon, lat)
        cm = m.pcolormesh(x, y, d, cmap=cmap, vmin=vmin, vmax=vmax)
        if wind is not None:
            m.quiver(lon[::100, ::100], lat[::100, ::100], wind[0][::100, ::100],
                     wind[-1][::100, ::100], latlon=True)
        if i == 0 and obs is not None:
            lons = obs['longitude']
            lats = obs['latitude']
            m.scatter(lons, lats, zorder=1, alpha=0.2, c='r', s=10, latlon=True)
        plt.title(f"{title} {dt.strftime(fig_date, '%Y-%m-%d %H:%M')},\n Analysistime {data.analysis_time}, forecast + {minute}min)")
        plt.colorbar(cm, fraction=0.046, pad=0.04, orientation="horizontal")
        forecast_outfile = outfile + f"POT_{i}_{dt.strftime(data.analysis_time, '%Y%m%d%H%M')}+{minute}min.png"
        plt.savefig(forecast_outfile, dpi=300, bbox_inches='tight', pad_inches=0.2)
        plt.close()


def generate_fig(proj):
    ax = plt.axes(projection=proj)
    ax.set_extent([0, 39, 51, 73])
    ax.gridlines()
    ax.add_feature(cartopy.feature.COASTLINE)
    ax.add_feature(cartopy.feature.BORDERS)
    ax.add_feature(cartopy.feature.OCEAN)
    ax.add_feature(cartopy.feature.LAND)
    return ax


if __name__ == '__main__':
    main()
