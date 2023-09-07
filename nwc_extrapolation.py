import numpy as np
from pysteps import nowcasts
import tools as tl


class ExtrapolatedNWC:
    def __init__(self, data: np.array,
                 nodata: np.array,
                 n_leadtimes: int = 17,
                 pot_data=None):
        self.data_input = data
        self.nodata = nodata
        self.data = None
        self.V = None
        self.n_leadtimes = n_leadtimes
        self.pot = pot_data
        self.calculate_nwc()

    def calculate_nwc(self):
        # Estimate the motion field with Lucas-Kanade
        self.V = tl.calculate_wind_field(self.data_input, self.nodata)
        # Extrapolate the last radar observation
        extrapolate = nowcasts.get_method("extrapolation")
        if self.pot is not None:
            try:
                self.data = extrapolate(self.pot[-1, :, :], self.V, self.n_leadtimes)
            except:
                self.data = extrapolate(self.pot, self.V, self.n_leadtimes)
            self.data[self.data < 10] = 0.0
        else:
            self.data = extrapolate(self.data_input[-1, :, :], self.V, self.n_leadtimes)
