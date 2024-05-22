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
    # Make sure order if from oldest to newest, check any wrong files
    initial_files = tl.validate_and_sort_filenames([args.rprate_3_file, args.rprate_2_file,
                                                                args.rprate_1_file, args.rprate_0_file])
    try:
        # create POT_0h analysis grid from observation.
        # If no observations, use model data only. If no model data, everything will break
        pot_data = Analysis(args.mnwc_tstm_file, args.start_time, args.obs_time_window)

        # Read data for generating a wind field
        if len(initial_files) == 4:
            for i, data_file in enumerate(initial_files):
                try:
                    data = ReadData(data_file)
                    if i == 0:
                        analysis_info = tl.create_dict(data)
                    elif i > 0:
                        analysis_info = tl.add_to_dict(analysis_info, data)

                except FileNotFoundError as f:
                    print("Some of rprate-files are missing, use latest file if exist")
                    # Generate path to a latest full precipitation rate file
                    rp_file = tl.generate_backup_data_path(initial_files[-1])
                    try:
                        data = ReadData(rp_file, time_steps=3)
                        analysis_info = {"data": data.data, "mask": data.mask_nodata, "time": data.dtime}
                        break
                    except FileNotFoundError as ff:
                        print(f"{rp_file} not found")
                        raise FileNotFoundError(f"No precipitation intensity file {rp_file} found!")
        else:
            print("Some of rprate-files are wrong or missing, use latest rp-file if exist")
            rp_file = tl.generate_backup_data_path(initial_files[-1])
            try:
                data = ReadData(rp_file, time_steps=3)
                analysis_info = {"data": data.data, "mask": data.mask_nodata, "time": data.dtime}
            except FileNotFoundError as ff:
                print(f"{rp_file} not found")
                raise FileNotFoundError(f"No precipitation intensity file {rp_file} found!")

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
