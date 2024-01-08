import argparse
import tools as tl
from file_utils import ReadData, WriteData
from nwc_extrapolation import ExtrapolatedNWC
from flash_analysis import Analysis


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
    initial_files = [args.rprate_3_file,
                     args.rprate_2_file,
                     args.rprate_1_file,
                     args.rprate_0_file]

    # Make sure order if from oldest to newest
    initial_files = tl.pick_files_by_datetime(initial_files, args.start_time)
    file_not_found = False
    try:
        # create POT_0h analysis grid from observation.
        pot_data = Analysis(args.mnwc_tstm_file, args.start_time, args.obs_time_window)
        analysis_info = {}
        for i, data_file in enumerate(initial_files):
            if file_not_found:
                break
            try:
                data = ReadData(data_file)
                data_0h, mask_data_0h, time_0h = tl.pick_analysis_data_from_array(data)
                if i == 0:
                    analysis_info = {"data": [data_0h], "mask": [mask_data_0h], "time": [time_0h]}
                elif i > 0:
                    analysis_info["data"].append(data_0h)
                    analysis_info["mask"].append(mask_data_0h)
                    analysis_info["time"].append(time_0h)
                nwc_data = tl.generate_nowcast_array(analysis_info)
            except FileNotFoundError as f:
                print("One or more of rprate-files are missing, use only one latest available file")
                file_not_found = True
                nowcast_dates = tl.generate_nowcast_times(args.start_time)
                for data_file, date in zip(initial_files, nowcast_dates):
                    data_file = tl.generate_temporary_path(data_file, date)
                    try:
                        data = ReadData(data_file, time_steps=3)
                        analysis_info = {"data": data.data, "mask": data.mask_nodata, "time": data.dtime}
                        nwc_data = tl.generate_nowcast_array(analysis_info)
                        break
                    except FileNotFoundError as ff:
                        print(f"{data_file} not found")
                        pass
        # If all rprate files are missing, this will crash
        analysis_data = nwc_data.data
        masked_data = nwc_data.mask
        exrtapolated_fcst = ExtrapolatedNWC(analysis_data, masked_data,
                                            pot_data=pot_data.output)
        exrtapolated_fcst = tl.convert_nan_to_zeros(exrtapolated_fcst)
        WriteData(exrtapolated_fcst, pot_data.template, args.output,
                  's3' if args.output.startswith('s3://') else 'local')
    except KeyError as e:
        # if not model file, this will crash
        MNWC_fcst = ReadData(args.mnwc_tstm_file, use_as_template=True, time_steps=4)
        WriteData(MNWC_fcst, MNWC_fcst.template, args.output,
                  's3' if args.output.startswith('s3://') else 'local')


def parse_command_line():
    parser = argparse.ArgumentParser(argument_default=None)
    parser.add_argument("--start_time", action="store", type=str, required=True)
    parser.add_argument("--wind_field_param", action="store", type=str, required=True)
    parser.add_argument("--obs_time_window", action="store", type=int, required=True)
    parser.add_argument("--output", action="store", type=str, required=True)
    parser.add_argument("--file_source", action="store", type=str, required=True)
    parser.add_argument("--rprate_0_file", action="store", type=str, required=True)
    parser.add_argument("--rprate_1_file", action="store", type=str, required=True)
    parser.add_argument("--rprate_2_file", action="store", type=str, required=True)
    parser.add_argument("--rprate_3_file", action="store", type=str, required=True)
    parser.add_argument("--mnwc_tstm_file", action="store", type=str, required=True)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()

