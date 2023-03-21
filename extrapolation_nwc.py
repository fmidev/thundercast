import numpy as np
from pysteps import motion, nowcasts


class ExtrapolatedNWC:
    def __init__(self, data: np.array,
                 nodata: np.array,
                 n_leadtimes: int = 17,
                 pot_data=None):
        self.data = data
        self.nodata = nodata
        self.data_f = None
        self.V = None
        self.n_leadtimes = n_leadtimes
        self.pot = pot_data
        self.calculate_nwc()

    def calculate_nwc(self):
        # Estimate the motion field with Lucas-Kanade
        self.data[~np.isfinite(self.nodata)] = np.nan
        self.data[self.data == 9999] = np.nan
        oflow_method = motion.get_method("LK")
        self.V = oflow_method(self.data[:3, :, :])

        # Extrapolate the last radar observation
        extrapolate = nowcasts.get_method("extrapolation")
        if self.pot is not None:
            try:
                self.data_f = extrapolate(self.pot[-1, :, :], self.V, self.n_leadtimes)
            except:
                self.data_f = extrapolate(self.pot, self.V, self.n_leadtimes)
            self.data_f[self.data_f < 10] = 0.0
        else:
            self.data_f = extrapolate(self.data[-1, :, :], self.V, self.n_leadtimes)
