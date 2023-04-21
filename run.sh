#!/bin/bash
# Run script for Potential of thunder nowcasting calculations.
# PARAMETER INPUTS: $1 is the HOD (hour of the day), $2 is yes/no (plot_diagnostics)

PYTHON=$1

$PYTHON ./pot_extrapolation_fcst.py --start_time 202301161030 --pot_time 202207131515 --param pot --wind_field_param rprate --obs_time_window 20 --output $PWD/test_data/test_write_pot_1.grib2 --file_source local --input_file $PWD/test_data/mnwc_tstm.grib2