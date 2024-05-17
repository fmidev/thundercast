#!/bin/bash
# Run script for Potential of thunder nowcasting forecasting

PYTHON=python3
START_TIME=$1

generate_time_str() {
	i=$((${#1}-2))
	j=$((${#1}-4))
	ii=$((${#1}-8))

	if [[ ${1:$i:2} -ne 00 ]];
  	then
    		((M15=$1-15))
  	fi
	if [[ ${1:$i:2} -eq 00 ]];
	then
		((M15=$1-55))
  	fi
	# If days changes smaller
	if [[ ${1:$j:4} -eq 0000 ]];
	then
		((M15=$1-7655))
  	fi
	# If month changes smaller 30 days
  	if [ ${1:$ii:8} -eq 05010000 ] || [ ${1:$ii:8} -eq 07010000 ] || [ ${1:$ii:8} -eq 08010000 ] || [ ${1:$ii:8} -eq 10010000 ] || [ ${1:$ii:8} -eq 12010000 ];
	then
		((M15=$1-707655))
  	fi
	# If month changes smaller 31 days
  	if [ ${1:$ii:8} -eq 02010000 ] || [ ${1:$ii:8} -eq 04010000 ] || [ ${1:$ii:8} -eq 06010000 ] || [ ${1:$ii:8} -eq 09010000 ] || [ ${1:$ii:8} -eq 11010000 ];
	then
		((M15=$1-697655))
  	fi
	# If month changes to February
  	if [ ${1:$ii:8} -eq 03010000 ];
	then
		((M15=$1-727655))
  	fi
	# If year changes smaller
  	if [ ${1:$ii:8} -eq 01010000 ];
	then
		((M15=$1-88697655))
  	fi
  echo $M15
}

MINUS15=$(generate_time_str $START_TIME)
MINUS30=$(generate_time_str $MINUS15)
MINUS45=$(generate_time_str $MINUS30)

echo $START_TIME
echo $MINUS15
echo $MINUS30
echo $MINUS45

# Check if "test_data" is in project, if not create
mkdir -p "$PWD"/test_data

FILE0=s3://hrnwc/preop/$START_TIME/$START_TIME-hrnwc-rprate.grib2
FILE1=s3://hrnwc/preop/$START_TIME/$MINUS15-hrnwc-rprate.grib2
FILE2=s3://hrnwc/preop/$START_TIME/$MINUS30-hrnwc-rprate.grib2
FILE3=s3://hrnwc/preop/$START_TIME/$MINUS45-hrnwc-rprate.grib2
SOURCE_FILE=s3://hrnwc/preop/$START_TIME/mnwc_tstm.grib2
OUTPUT="$PWD"/test_data/"$START_TIME"_interpolated_tstm.grib2

#Local file run
# Create needed directories and download data to your "test_data" directory. You can modify file path if needed
#FILE0=$PWD/test_data/$START_TIME/$START_TIME-hrnwc-rprate.grib2
#FILE1=$PWD/test_data/$START_TIME/$MINUS15-hrnwc-rprate.grib2
#FILE2=$PWD/test_data/$START_TIME/$MINUS30-hrnwc-rprate.grib2
#FILE3=$PWD/test_data/$START_TIME/$MINUS45-hrnwc-rprate.grib2
#SOURCE_FILE=$PWD/test_data/$START_TIME/mnwc_tstm.grib2
#OUTPUT=$PWD/test_data/"$START_TIME"_interpolated_tstm.grib2

#Generating nowcasted forecast for potential of thunder
$PYTHON ./generate_propability_of_thunder.py --start_time $START_TIME --wind_field_param rprate --obs_time_window 20 --output $OUTPUT --file_source local --rprate_0_file $FILE0 --rprate_1_file $FILE1 --rprate_2_file $FILE2 --rprate_3_file $FILE3 --mnwc_tstm_file $SOURCE_FILE

# Uncomment Python run call for doing visualizations
# Generating visualizations for each forecasted timesteps
#$PYTHON plotting.py --data_file $OUTPUT --obs_time_window 20 --analysis --analysis_time $START_TIME --rprate_1_file $FILE1 --rprate_2_file $FILE2 --rprate_3_file $FILE3