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

leap_year() {
	leap=$(date +"%Y")
	if [ `expr $leap % 400` -eq 0 ]
	then
		((M15=$1+10000))
	elif [ `expr $leap % 100` -eq 0 ]
	then
		((M15=$1))
	elif [ `expr $leap % 4` -eq 0 ]
	then
		((M15=$1+10000))
	else
		((M15=$1))
	fi
	echo $M15
}

MINUS15=$(generate_time_str $START_TIME)
MINUS15=$(leap_year $MINUS15)
MINUS30=$(generate_time_str $MINUS15)
MINUS15=$(leap_year $MINUS15)
MINUS45=$(generate_time_str $MINUS30)
MINUS15=$(leap_year $MINUS15)
MINUS60=$(generate_time_str $MINUS45)
MINUS15=$(leap_year $MINUS15)

FILE0=s3://hrnwc/preop/$START_TIME/interpolated_rprate.grib2
FILE1=s3://hrnwc/preop/$MINUS15/interpolated_rprate.grib2
FILE2=s3://hrnwc/preop/$MINUS30/interpolated_rprate.grib2
FILE3=s3://hrnwc/preop/$MINUS45/interpolated_rprate.grib2
SOURCE_FILE=s3://hrnwc/preop/$MINUS60/mnwc_tstm.grib2
OUTPUT="$PWD"/test_data/"$START_TIME"_interpolated_tstm.grib2

#Generating nowcasted forecast for potential of thunder
$PYTHON ./generate_propability_of_thunder.py --start_time $START_TIME --wind_field_param rprate --obs_time_window 20 --output $OUTPUT --file_source s3 --rprate_0_file $FILE0 --rprate_1_file $FILE1 --rprate_2_file $FILE2 --rprate_3_file $FILE3 --mnwc_tstm_file $SOURCE_FILE

# Generating visualizations for each forecasted timesteps
#$PYTHON ./plotting.py --data_file $OUTPUT --analysis --analysis_time $START_TIME --rprate_1_file $FILE1 --rprate_2_file $FILE2 --rprate_3_file $FILE3