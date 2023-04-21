import argparse
import tools as tl
from file_utils import ReadData, WriteData
from extrapolation_nwc import ExtrapolatedNWC
from pot_analysis import Analysis
from plotting import plot_contourf_map_scandinavia_array


def main():
    """Probability of thunder nowcast a.k.a Thundercast

    This program creates POT analysis field from observations and interpolates those
    to model grid. Then calculates nowcast forecast using wind filed generated with Pysteps.
    Creates 4h forecast with 15 min outputs. Grid resolution is same as input model
    used for calculating wind fields.

    Generates wind field for nowcasting with Pysteps library using model
    precipitation rate simulations.
    From rr takes latest forecasts 0h and 3 previous forecasts 0h model fields.
    From observations pick up all lightning observations from select time window.
    With longer time since observed, smaller probability will observation get.
    Observations are then interpolated to  model grid using Gridpp library.

    """
    args = parse_command_line()
    #TODO: Lisää datan haku suoraan S3:lta
    initial_files = tl.fetch_wanted_date_files(args.wind_field_param, args.start_time)
    # create POT_0h analysis from observation.
    pot_data = Analysis(args.input_file, args.obs_time_window)
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
    WriteData(exrtapolated_fcst, pot_data.template, args.output, args.file_source)


def parse_command_line():
    #TODO: onko kaikki tarpeellisia antaa muuttujana?
    parser = argparse.ArgumentParser(argument_default=None)
    parser.add_argument("--start_time", action="store", type=str, required=True)
    parser.add_argument("--pot_time", action="store", type=str, required=True)
    parser.add_argument("--param", action="store", type=str, required=True)
    parser.add_argument("--wind_field_param", action="store", type=str, required=True)
    parser.add_argument("--obs_time_window", action="store", type=int, required=True)
    parser.add_argument("--output", action="store", type=str, required=True)
    parser.add_argument("--file_source", action="store", type=str, required=True)
    parser.add_argument("--input_file", action="store", type=str, required=False)
    parser.add_argument("--plot", action="store_true", default=False)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    #param = "pot"
    #wind_param = "rprate"
    #pot_date = "202207131515"
    #rp_date = "202301161030"
    main()

