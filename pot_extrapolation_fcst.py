import tools as tl
from file_utils import ReadData
from extrapolation_nwc import ExtrapolatedNWC
from pot_analysis import Analysis
from plotting import plot_contourf_map_scandinavia_array


def main(wind_param: str, datetime_zero: str):
    # create POT_0h analysis from observation.
    initial_files = tl.fetch_wanted_date_files(wind_param, datetime_zero)
    pot_data = Analysis(initial_files[-1])
    analysis_info = {}
    for i, data_file in enumerate(initial_files):
        data = ReadData(data_file)
        data_0h, mask_data_0h, time_0h = tl.pick_analysis_data_from_array(data)
        if i == 0:
            analysis_info = {"data": [data_0h], "mask": [mask_data_0h], "time": [time_0h]}
        else:
            analysis_info["data"].append(data_0h)
            analysis_info["mask"].append(mask_data_0h)
            analysis_info["time"].append(time_0h)
    nwc_data = tl.generate_nowcast_array(analysis_info)
    analysis_data = nwc_data.data
    masked_data = nwc_data.mask
    exrtapolated_fcst = ExtrapolatedNWC(analysis_data, masked_data,
                                        pot_data=pot_data.output)
    exrtapolated_fcst = tl.convert_nan_to_zeros(exrtapolated_fcst)
    # Tässä kohtaa pitää ehkä tallettaa filuksi


    fig_out = f"/home/korpinen/Documents/STU_kehitys/ukkosen_tod/figures/"
    #plot_NWC_data(exrtapolated_fcst.data_f, 0.0, 1.0, fig_out, pot_date,
    #              nwc_data.time[-1], "Probability of thunder nwc 15min 1km", "nwc",
    #              wind=exrtapolated_fcst.V, lat=pot_data.latitudes, lon=pot_data.longitudes)
    plot_contourf_map_scandinavia_array(exrtapolated_fcst.data_f, pot_data, 0, 100,
                                        fig_out, pot_date, nwc_data.time[-1],
                                        "Probability of thunder nwc 15min 1km",
                                        wind=exrtapolated_fcst.V, analysis=True)


if __name__ == '__main__':
    param = "pot"
    wind_param = "rprate"
    pot_date = "202207131515"
    rp_date = "202301161030"
    main(wind_param, rp_date)

