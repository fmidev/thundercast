import sys
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
    try:
        # create POT_0h analysis grid from observation.
        # If no observations, use model data only
        pot_data = Analysis(args.mnwc_tstm_file, args.start_time, args.obs_time_window)

        # booleans for some or all missing files
        file_not_found = False
        no_input_files = False

        # Read data for generating a wind field
        for i, data_file in enumerate(initial_files):
            if no_input_files:
                print(f"Not enough input datafiles to process Thundercast!")
                sys.exit(1)
            if file_not_found:
                print(f"Windfield calculation Backup file {rp_file} used!")
                break

            try:
                data = ReadData(data_file)
                if i == 0:
                    analysis_info = tl.create_dict(data)
                elif i > 0:
                    analysis_info = tl.add_to_dict(analysis_info, data)

            except FileNotFoundError as f:
                print("One or more of rprate-files are missing, use latest file if exist")
                file_not_found = True
                nowcast_dates = tl.generate_nowcast_times(args.start_time)
                for i, (data_file, date) in enumerate(zip(initial_files, reversed(nowcast_dates))):
                    rp_file = tl.generate_backup_data_path(data_file, date)
                    try:
                        data = ReadData(rp_file, time_steps=3)
                        analysis_info = {"data": data.data, "mask": data.mask_nodata, "time": data.dtime}
                        nwc_data = tl.generate_nowcast_array(analysis_info)
                        break
                    except FileNotFoundError as ff:
                        print(f"{data_file} not found")
                        if i == len(initial_files) - 1:
                            no_input_files = True
                        pass
        if not file_not_found:
            nwc_data = tl.generate_nowcast_array(analysis_info)
        exrtapolated_fcst = ExtrapolatedNWC(nwc_data.data,  nwc_data.mask,
                                            pot_data=pot_data.output)
        exrtapolated_fcst = tl.convert_nan_to_zeros(exrtapolated_fcst)
        WriteData(exrtapolated_fcst, pot_data.template, args.output,
                  's3' if args.output.startswith('s3://') else 'local')
    except KeyError as e:
        # if not model file, this will crash
        MNWC_fcst = ReadData(args.mnwc_tstm_file, use_as_template=True, time_steps=16)
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
