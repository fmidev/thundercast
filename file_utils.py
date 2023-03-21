from eccodes import *
import sys
import time
import datetime
import numpy as np
import os
import fsspec
import pyproj

GRIB_MESSAGE_TEMPLATE = None
GRIB_MESSAGE_STEP = None


class ReadData:
    def __init__(self, data_file: str,
                added_hours: int = 0,
                read_coordinates: bool = False,
                use_as_template: bool = False):
        self.data_file = data_file
        self.mask_nodata = None
        self.data = None
        self.nodata = 9999
        self.latitudes = None
        self.longitudes = None
        self.dtime = None
        self.forecast_time = None
        self.analysis_time = None
        self.read(added_hours, read_coordinates, use_as_template)

    def read(self, added_hours, read_coordinates, use_as_template):
        print(f"Reading {self.data_file}")
        if self.data_file.endswith(".grib2"):
            self.read_grib(added_hours, read_coordinates, use_as_template)
        else:
            sys.exit("unsupported file type for file: %s" % (self.data_file))

    def read_file_from_s3(self):
        uri = "simplecache::{}".format(self.data_file)
        return fsspec.open_local(uri, s3={'anon': True, 'client_kwargs': {'endpoint_url': 'https://lake.fmi.fi'}})

    def read_grib(self, added_hours, read_coordinates, use_as_template):
        global GRIB_MESSAGE_TEMPLATE
        global GRIB_MESSAGE_STEP
        start = time.time()

        def read_leadtime(gh):
            tr = codes_get_long(gh, "indicatorOfUnitOfTimeRange")
            ft = codes_get_long(gh, "forecastTime")
            if tr == 1:
                return datetime.timedelta(hours=ft)
            if tr == 0:
                return datetime.timedelta(minutes=ft)
            raise Exception("Unknown indicatorOfUnitOfTimeRange: {:%d}".format(tr))

        data_ls = []
        latitudes_ls = []
        longitudes_ls = []
        dtime_ls = []
        wrk_data_file = self.data_file

        if self.data_file.startswith("s3://"):
            wrk_data_file = self.read_file_from_s3()

        with open(wrk_data_file) as fp:
            while True:
                gh = codes_grib_new_from_file(fp)
                if gh is None:
                    break

                ni = codes_get_long(gh, "Ni")
                nj = codes_get_long(gh, "Nj")
                data_date = codes_get_long(gh, "dataDate")
                data_time = codes_get_long(gh, "dataTime")
                lt = read_leadtime(gh)
                self.analysis_time = datetime.datetime.strptime("{:d}/{:04d}".format(data_date, data_time), "%Y%m%d/%H%M")
                self.forecast_time = datetime.datetime.strptime("{:d}/{:04d}".format(data_date, data_time), "%Y%m%d/%H%M") + lt
                dtime_ls.append(self.forecast_time)
                values = np.asarray(codes_get_values(gh))
                data_ls.append(values.reshape(nj, ni))
                if read_coordinates:
                    latitudes_ls.append(np.asarray(codes_get_array(gh, "latitudes").reshape(nj, ni)))
                    longitudes_ls.append(np.asarray(codes_get_array(gh, "longitudes").reshape(nj, ni)))

                if use_as_template:
                    if GRIB_MESSAGE_TEMPLATE is None:
                        GRIB_MESSAGE_TEMPLATE = codes_clone(gh)
                    if GRIB_MESSAGE_STEP is None and lt > datetime.timedelta(minutes=0):
                        GRIB_MESSAGE_STEP = lt
                if codes_get_long(gh, "numberOfMissing") == ni*nj:
                    print("File {} leadtime {} contains only missing data!".format(self.data_file, lt))
                    sys.exit(1)
                codes_release(gh)

                if len(dtime_ls) > 0:
                    fp.close()
                    del fp
                    del gh
                    break

        self.data = np.asarray(data_ls)
        if len(latitudes_ls) > 0:
            self.latitudes = np.asarray(latitudes_ls)
            self.longitudes = np.asarray(longitudes_ls)
            self.latitudes = self.latitudes[0, :, :]
            self.longitudes = self.longitudes[0, :, :]

        self.mask_nodata = np.ma.masked_where(self.data == self.nodata, self.data)
        if type(dtime_ls) == list:
            self.dtime = [(i+datetime.timedelta(hours=added_hours)) for i in dtime_ls]
        print("Read {} in {:.2f} seconds".format(self.data_file, time.time() - start))


class WriteData:
    def __init__(self,
                 interpolated_data: np.ndarray,
                 write_file: str,
                 grib_write_options: list,
                 t_diff: int):
        self.interpolated_data = interpolated_data
        self.t_diff = t_diff
        self.write(write_file, grib_write_options)

    def write(self, write_file, grib_write_options):
        if write_file.endswith(".grib2"):
            self.write_grib(write_file, grib_write_options)
        else:
            print("write: unsupported file type for file: %s" % (write_file))
            return
        print("wrote file '%s'" % write_file)

    def write_grib_message(self, fpout, write_options):
        assert (GRIB_MESSAGE_TEMPLATE is not None)

        # For 1km PPN+MNWC forecast adjust the output grib dataTime (analysis time) since the 1h leadtime is used instead of 0h. Metadata taken from MNWC
        if self.t_diff == None:
            self.t_diff = 0
        self.t_diff = int(self.t_diff)

        dataDate = int(codes_get_long(GRIB_MESSAGE_TEMPLATE, "dataDate"))
        dataTime = int(codes_get_long(GRIB_MESSAGE_TEMPLATE, "dataTime"))
        analysistime = datetime.datetime.strptime("{}{:04d}".format(dataDate, dataTime), "%Y%m%d%H%M")
        analysistime = analysistime + datetime.timedelta(hours=self.t_diff)
        codes_set_long(GRIB_MESSAGE_TEMPLATE, "dataDate", int(analysistime.strftime("%Y%m%d")))
        codes_set_long(GRIB_MESSAGE_TEMPLATE, "dataTime", int(analysistime.strftime("%H%M")))
        codes_set_long(GRIB_MESSAGE_TEMPLATE, "bitsPerValue", 24)
        codes_set_long(GRIB_MESSAGE_TEMPLATE, "generatingProcessIdentifier", 202)
        codes_set_long(GRIB_MESSAGE_TEMPLATE, "centre", 86)
        codes_set_long(GRIB_MESSAGE_TEMPLATE, "bitmapPresent", 1)

        base_lt = datetime.timedelta(hours=1)

        is_minutes = True if GRIB_MESSAGE_STEP == datetime.timedelta(minutes=15) else False

        if is_minutes:
            codes_set_long(GRIB_MESSAGE_TEMPLATE, "indicatorOfUnitOfTimeRange", 0)  # minute
            base_lt = datetime.timedelta(minutes=15)

        pdtn = codes_get_long(GRIB_MESSAGE_TEMPLATE, "productDefinitionTemplateNumber")

        if write_options is not None:
            for opt in write_options.split(','):
                k, v = opt.split('=')
                codes_set_long(GRIB_MESSAGE_TEMPLATE, k, int(v))

        for i in range(self.interpolated_data.shape[0]):

            lt = base_lt * i

            if pdtn == 8:
                lt -= base_lt

                tr = codes_get_long(GRIB_MESSAGE_TEMPLATE, "indicatorOfUnitForTimeRange")
                trlen = codes_get_long(GRIB_MESSAGE_TEMPLATE, "lengthOfTimeRange")

                assert ((tr == 1 and trlen == 1) or (tr == 0 and trlen == 60))
                lt_end = analysistime + datetime.timedelta(
                    hours=codes_get_long(GRIB_MESSAGE_TEMPLATE, "lengthOfTimeRange"))

                # these are not mandatory but some software uses them
                codes_set_long(GRIB_MESSAGE_TEMPLATE, "yearOfEndOfOverallTimeInterval", int(lt_end.strftime("%Y")))
                codes_set_long(GRIB_MESSAGE_TEMPLATE, "monthOfEndOfOverallTimeInterval", int(lt_end.strftime("%m")))
                codes_set_long(GRIB_MESSAGE_TEMPLATE, "dayOfEndOfOverallTimeInterval", int(lt_end.strftime("%d")))
                codes_set_long(GRIB_MESSAGE_TEMPLATE, "hourOfEndOfOverallTimeInterval", int(lt_end.strftime("%H")))
                codes_set_long(GRIB_MESSAGE_TEMPLATE, "minuteOfEndOfOverallTimeInterval", int(lt_end.strftime("%M")))
                codes_set_long(GRIB_MESSAGE_TEMPLATE, "secondOfEndOfOverallTimeInterval", int(lt_end.strftime("%S")))

            if is_minutes:
                codes_set_long(GRIB_MESSAGE_TEMPLATE, "forecastTime", lt.total_seconds() / 60)
            else:
                codes_set_long(GRIB_MESSAGE_TEMPLATE, "forecastTime", lt.total_seconds() / 3600)

            codes_set_values(GRIB_MESSAGE_TEMPLATE, self.interpolated_data[i, :, :].flatten())
            codes_write(GRIB_MESSAGE_TEMPLATE, fpout)

        codes_release(GRIB_MESSAGE_TEMPLATE)
        fpout.close()

    def write_grib(self, write_grib_file, write_options):
        try:
            os.remove(write_grib_file)
        except OSError as e:
            pass

        with open(str(write_grib_file), "wb") as fpout:
            self.write_grib_message(fpout, write_options)
