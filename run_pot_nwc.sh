#!/bin/bash
# Run script for Potential of thunder nowcasting forecasting

PYTHON=python3
START_TIME=$1

generate_time_str() {
  i=$((${#1}-2))
	if [[ ${1:$i:2} -eq 00 ]];
	then
	  ((M15=$1-55))
  fi

  if [[ ${1:$i:2} -ne 00 ]];
  then
    ((M15=$1-15))
  fi
  echo "$M15"
}

MINUS15=$(generate_time_str $START_TIME)
MINUS30=$(generate_time_str $MINUS15)
MINUS45=$(generate_time_str $MINUS30)
MINUS60=$(generate_time_str $MINUS45)

FILE0=s3://hrnwc/development/$START_TIME/interpolated_rprate.grib2
FILE1=s3://hrnwc/development/$MINUS15/interpolated_rprate.grib2
FILE2=s3://hrnwc/development/$MINUS30/interpolated_rprate.grib2
FILE3=s3://hrnwc/development/$MINUS45/interpolated_rprate.grib2
SOURCE_FILE=s3://hrnwc/development/$MINUS60/mnwc_tstm.grib2
OUTPUT="$PWD"/test_data/"$START_TIME"_pot.grib2

#Generating nowcasted forecast for potential of thunder
$PYTHON ./generate_propability_of_thunder.py --start_time $START_TIME --wind_field_param rprate --obs_time_window 20 --output $OUTPUT --file_source s3 --rprate_0_file $FILE0 --rprate_1_file $FILE1 --rprate_2_file $FILE2 --rprate_3_file $FILE3 --mnwc_tstm_file $SOURCE_FILE

# Generating visualizations for each forecasted timesteps
#$PYTHON ./plotting.py --data_file $OUTPUT --analysis --analysis_time $START_TIME --rprate_1_file $FILE1 --rprate_2_file $FILE2 --rprate_3_file $FILE3