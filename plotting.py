import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
from mpl_toolkits.basemap import Basemap
import cartopy
from datetime import datetime as dt
from datetime import timedelta as td
import tools as tl


def plot_imshow_map_scandinavia(grib_file, vmin, vmax, outfile, date, title):
    """Use for plotting when projection is Polster/Polar_stereografic

    Only for Scandinavian domain. For other domains coordinates must be changed.
    For xarray to work with grib-files, cfgrib must be installed
    """
    ds = xr.load_dataset(grib_file)
    cmap = 'RdYlGn_r' # RdBl_r  'Blues' 'Jet' 'RdYlGn_r'
    for v in ds:
        data = ds[v].data
        lat_ts, lat0, lon0 = 52, 63, 19
        for i in range(len(data)):
            m = Basemap(width=1900000, height=2100000,
                        resolution='l', projection='laea',
                        lat_ts=lat_ts, lat_0=lat0, lon_0=lon0)
            m.drawcountries(linewidth=1.0)
            m.drawcoastlines(1.0)

            d = data[i]
            d[d <= 0.01] = np.nan
            cm = m.imshow(d, cmap=cmap, vmin=vmin, vmax=vmax, origin="lower", zorder=1)
            plt.title(f"{title}, {date} forecast {i}h")
            plt.colorbar(cm, fraction=0.046, pad=0.04, orientation="horizontal")
            idx = outfile.index("h.")
            forecast_outfile = outfile[:idx] + f"{i}" + outfile[idx:]
            plt.savefig(forecast_outfile, bbox_inches='tight', pad_inches=0.2, dpi=800)
            plt.close()


def plot_contourf_map_scandinavia_file(grib_file, vmin, vmax, outfile, date,
                                       w_time, title, wind=None, analysis=False):
    """Use for plotting when projection is Lambert etc.

    For xarray to work with grib-files, cfgrib must be installed
    """
    ds = xr.load_dataset(grib_file)
    lon, lat = tl.read_obs()
    fig_date = w_time
    for v in ds:
        data = ds[v].data
        lats, lons = ds['latitude'].data, ds['longitude'].data
        lons[lons > 180] = lons[lons > 180] - 360
        proj = cartopy.crs.LambertConformal(central_latitude=int(np.mean(lats)),
                                            central_longitude=int(np.mean(lons)),
                                            standard_parallels=(25, 25))
        for i in range(len(data)):
            minute = 0
            if i > 0:
                minute = 15 * i
                fig_date = fig_date + td(minutes=int(15))
            d = data[i]
            ax = generate_fig(proj)
            if i == 0:
                ax = generate_fig(proj)
                cm = ax.pcolormesh(lons, lats, d, transform=cartopy.crs.PlateCarree(),
                                   shading='auto', vmin=vmin, vmax=vmax, cmap='Blues')
                if analysis:
                    ax.scatter(lon, lat, zorder=1, alpha=0.1, c='r', s=5,
                               transform=cartopy.crs.PlateCarree())
                if wind is not None:
                    ax.quiver(lons[::100, ::100], lats[::100, ::100], wind[0][::100, ::100],
                              wind[-1][::100, ::100], transform=cartopy.crs.PlateCarree())
            else:
                cm = ax.pcolormesh(lons, lats, d, transform=cartopy.crs.PlateCarree(),
                                   shading='auto', vmin=vmin, vmax=vmax, cmap='Blues')
                if wind is not None:
                    ax.quiver(lons[::100, ::100], lats[::100, ::100], wind[0][::100, ::100],
                              wind[-1][::100, ::100], transform=cartopy.crs.PlateCarree())
            plt.title(f"{title} {dt.strftime(fig_date, '%Y-%m-%d %H:%M')}, "
                      f"(POT date: {dt.strptime(date, '%Y%m%d%H%M').strftime('%Y-%m-%d %H:%M')} + {minute}min)")
            plt.colorbar(cm, fraction=0.046, pad=0.04, orientation="horizontal")
            forecast_outfile = outfile + f"{type}_pot_{i}min_{dt.strftime(fig_date, '%Y%m%d%H%M')}.png"
            save_fig(ax, title, date, forecast_outfile)


def plot_contourf_map_scandinavia_array(data, obs_data, vmin, vmax, outfile, date,
                                        w_time, title, wind=None, analysis=False):
    """Use for plotting when projection is Lambert etc.

    For xarray to work with grib-files, cfgrib must be installed
    """
    obs = obs_data.obs
    lon = obs['longitude']
    lat = obs['latitude']
    lons = obs_data.longitudes
    lats = obs_data.latitudes
    fig_date = w_time
    for i in range(len(data[0]) - 1):
        minute = 0
        if i > 0:
            minute = 15 * i
            fig_date = fig_date + td(minutes=int(15))
        d = data[i]
        lons[lons > 180] = lons[lons > 180] - 360
        proj = cartopy.crs.LambertConformal(central_latitude=int(np.mean(lats)),
                                            central_longitude=int(np.mean(lons)),
                                            standard_parallels=(25, 25))
        ax = generate_fig(proj)
        if i == 0:
            cm = ax.pcolormesh(lons, lats, d, transform=cartopy.crs.PlateCarree(),
                               shading='auto', vmin=vmin, vmax=vmax, cmap='Blues')
            if analysis:
                ax.scatter(lon, lat, zorder=1, alpha=0.1, c='r', s=5,
                           transform=cartopy.crs.PlateCarree())
            if wind is not None:
                ax.quiver(lons[::100, ::100], lats[::100, ::100], wind[0][::100, ::100],
                          wind[-1][::100, ::100], transform=cartopy.crs.PlateCarree())
        else:
            cm = ax.pcolormesh(lons, lats, d, transform=cartopy.crs.PlateCarree(),
                               shading='auto', vmin=vmin, vmax=vmax, cmap='Blues')
            if wind is not None:
                ax.quiver(lons[::100, ::100], lats[::100, ::100], wind[0][::100, ::100],
                          wind[-1][::100, ::100], transform=cartopy.crs.PlateCarree())
        plt.title(f"{title} {dt.strftime(fig_date, '%Y-%m-%d %H:%M')}, "
                  f"(POT date: {dt.strptime(date, '%Y%m%d%H%M').strftime('%Y-%m-%d %H:%M')} + {minute}min)")
        plt.colorbar(cm, fraction=0.046, pad=0.04, orientation="horizontal")
        forecast_outfile = outfile + f"nwc_pot_{i}_{dt.strftime(fig_date, '%Y%m%d%H%M')}.png"
        save_fig(ax, title, date, cm, forecast_outfile)


def plot_NWC_data_imshow_polster(data, obs_data, vmin, vmax, outfile, date,
                                 w_time, title, type, wind=None):
    cmap = 'Blues'  # RdBl_r  'Blues' 'Jet' 'RdYlGn_r'
    obs = obs_data.obs
    lons = obs['longitude']
    lats = obs['latitude']
    lon = obs_data.longitudes
    lat = obs_data.latitudes
    fig_date = w_time
    for i in range(len(data)):
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
        d = data[i, :, :]
        x, y = m(lon, lat)
        cm = m.pcolormesh(x, y, d, cmap=cmap, vmin=vmin, vmax=vmax)
        m.quiver(lon[::100, ::100], lat[::100, ::100], wind[0][::100, ::100],
                 wind[-1][::100, ::100], latlon=True)
        if i == 0:
            m.scatter(lons, lats, zorder=1, alpha=0.2, c='r', s=10, latlon=True)
        plt.title(f"{title} {dt.strftime(fig_date, '%Y-%m-%d %H:%M')}, "
                  f"(POT date: {dt.strptime(date, '%Y%m%d%H%M').strftime('%Y-%m-%d %H:%M')} + {minute}min)")
        plt.colorbar(cm, fraction=0.046, pad=0.04, orientation="horizontal")
        forecast_outfile = outfile + f"{type}_pot_{i}h_{dt.strftime(fig_date, '%Y%m%d%H%M')}.png"
        plt.savefig(forecast_outfile, dpi=800, bbox_inches='tight', pad_inches=0.2)
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


def save_fig(ax, title, date, outfile):
    plt.title(f"{title}, {date} forecast")
    forecast_outfile = outfile + f"{title}.png"
    plt.savefig(forecast_outfile, bbox_inches='tight', pad_inches=0.2, dpi=800)
    plt.close()
