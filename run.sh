#!/bin/bash
# Run script for Potential of thunder nowcasting forecasting

PYTHON=python3
START_TIME=202305090430
FILE0=s3://hrnwc/development/202305090430/interpolated_rprate.grib2
FILE1=s3://hrnwc/development/202305090415/interpolated_rprate.grib2
FILE2=s3://hrnwc/development/202305090400/interpolated_rprate.grib2
FILE3=s3://hrnwc/development/202305090345/interpolated_rprate.grib2
SOURCE_FILE=s3://hrnwc/development/202305090430/mnwc_tstm.grib2
OUTPUT=s3://hrnwc/development/202305090430/pot.grib2

#Generating nowcasted forecast for potential of thunder
$PYTHON ./pot_extrapolation_fcst.py --start_time $START_TIME --wind_field_param rprate --obs_time_window 20 --output $OUTPUT --file_source s3 --rprate_0_file $FILE0 --rprate_1_file $FILE1 --rprate_2_file $FILE2 --rprate_3_file $FILE3 --mnwc_tstm_file $SOURCE_FILE

# Generating visualizations for each forecasted timesteps
#$PYTHON ./plotting.py --data_file $OUTPUT --analysis --analysis_time $START_TIME --rprate_1_file $FILE1 --rprate_2_file $FILE2 --rprate_3_file $FILE3

# Params from running code from S3 or local file source
: '
# Thundercast run S3
--start_time 202305021430
--wind_field_param rprate
--obs_time_window 20
--output s3://hrnwc/development/202305021430/pot.grib2
--file_source s3
--rprate_0_file s3://hrnwc/development/202305021430/interpolated_rprate.grib2
--rprate_1_file s3://hrnwc/development/202305021415/interpolated_rprate.grib2
--rprate_2_file s3://hrnwc/development/202305021400/interpolated_rprate.grib2
--rprate_3_file s3://hrnwc/development/202305021345/interpolated_rprate.grib2
--mnwc_tstm_file s3://hrnwc/development/202305021430/mnwc_tstm.grib2

#Plotting run S3
--data_file s3://hrnwc/development/202305021430/pot.grib2
--analysis
--analysis_time 202305021430
--rprate_1_file s3://hrnwc/development/202305021415/interpolated_rprate.grib2
--rprate_2_file s3://hrnwc/development/202305021400/interpolated_rprate.grib2
--rprate_3_file s3://hrnwc/development/202305021345/interpolated_rprate.grib2



# Thundercast run local
--start_time 202305021430
--wind_field_param rprate
--obs_time_window 20
--output /test_data/202305021430_pot.grib2
--file_source local
--rprate_0_file /test_data/rprate/202301161030/interpolated_rprate.grib2
--rprate_1_file /test_data/rprate/202301161015/interpolated_rprate.grib2
--rprate_2_file /test_data/rprate/202301161000/interpolated_rprate.grib2
--rprate_3_file /test_data/rprate/202301160945/interpolated_rprate.grib2
--mnwc_tstm_file /test_data/mnwc_tstm.grib2


#Plotting run local
--data_file /test_data/202305021430_pot.grib2
--obs_time_window 20
--analysis
--analysis_time 202305021430
--rprate_1_file /test_data/rprate/202301161015/interpolated_rprate.grib2
--rprate_2_file /test_data/rprate/202301161000/interpolated_rprate.grib2
--rprate_3_file /test_data/rprate/202301160945/interpolated_rprate.grib2
'