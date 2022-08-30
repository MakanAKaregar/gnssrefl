import sys

import gnssrefl.gps as g
import argparse
import numpy as np


import gnssrefl.phase_functions as qp
from gnssrefl.utils import str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="doy", type=int)
    parser.add_argument("-snr", default=None, help="snr file ending", type=int)
    parser.add_argument("-fr", default=None, help="frequency (use all if you want both 1 and 20)", type=str)
    parser.add_argument("-doy_end", "-doy_end", default=None, type=int, help="doy end")
    parser.add_argument("-year_end", "-year_end", default=None, type=int, help="year end")
    parser.add_argument("-e1", default=None, type=int),
    parser.add_argument("-e2", default=None, type=int),
    parser.add_argument("-plot", default=None, type=str)
    parser.add_argument("-screenstats", default=None, type=str)
    parser.add_argument("-compute_lsp", default=None, type=str)

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plot', 'screenstats', 'compute_lsp']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def quickphase(station: str, year: int, doy: int, year_end: int = None, doy_end: int = None, snr: int = 66,
               fr: str = '20', e1: int = 5, e2: int = 30, plot: bool = False, screenstats: bool = False,
               compute_lsp: bool = True):
    """
    quickphase uses the apriori result file to restrict the number of satellite arcs that are used.

    Parmameters
    ___________
    station: string
        4 character ID of the station.

    year: integer
        Year to evaluate.

    doy: integer
        day of year to evaluate.
        Default is None.

    year_end: integer, optional
        year to end analysis. Using this option will create a range from year-year_end.
        Default is None.

    doy_end: integer, optional
        Day of year to end analysis. Using this option will create a range of doy-doy_end.
        If also using year_end, then this will be the day to end analysis in the year_end requested.
        Default is None.

    snr : integer, optional
        SNR format. This tells the code what elevation angles to save data for. Will be the snr file ending.
        value options:
            66 (default) : saves all data with elevation angles less than 30 degrees
            99 : saves all data with elevation angles between 5 and 30 degrees
            88 : saves all data with elevation angles between 5 and 90 degrees
            50 : saves all data with elevation angles less than 10 degrees

    fr : string, optional
        GNSS frequency. Currently only supports L2C.
        Default is 20 (l2c)

    e1 : integer, optional
        Elevation angle lower limit in degrees for the LSP.
        default is 5

    e2: integer, optional
        Elevation angle upper limit in degrees for the LSP.
        default is 30

    plot: boolean, optional
        Whether to plot results.
        Default is False

    screenstats: boolean, optional
        Whether to print stats to the screen.
        Default is False

    compute_lsp: boolean, optional
        Whether to compute the LSP.
        Default is True

    Returns
    _______
    Saves a file for each day in the doy-doy_end range: $REFL_CODE/<year>/phase/<station>/<doy>.txt'
    columns in files:
    year doy hour phase nv azimuth sat ampl emin emax delT aprioriRH freq estRH pk2noise LSPAmp
    """

    if fr == 'all':
        fr_list = [1, 20]
    else:
        fr_list = [int(fr)]

    # in case you want to analyze multiple days of data
    if not doy_end:
        doy_end = doy

    exitS = g.check_inputs(station, year, doy, snr)

    if exitS:
        sys.exit()

    g.result_directories(station, year, '')

    pele = [5, 30]  # polynomial fit limits  for direct signal

    # TODO maybe instead of specific doy we can do only year and pick up all those files just like the other parts?
    if year_end:
        year_range = np.arange(year, year_end+1)
        for y in np.arange(year, year_end+1):
            # If first year in multi-year range, then start on doy requested and finish year.
            if y == year_range[0]:
                date_range = np.arange(doy, 366)
            # If last year in multi-year range, then start on doy 1 finish on doy_end.
            elif y == year_range[-1]:
                date_range = np.arange(1, doy_end+1)
            # If year within multi-year range then do whole year start to finish.
            else:
                date_range = np.arange(1, 366)

            for d in date_range:
                print('Analyzing year/day of year ' + str(y) + '/' + str(d))
                qp.phase_tracks(station, y, d, snr, fr_list, e1, e2, pele, plot, screenstats, compute_lsp)
    else:
        for d in np.arange(doy, doy_end + 1):
            print('Analyzing year/day of year ' + str(year) + '/' + str(d))
            qp.phase_tracks(station, year, d, snr, fr_list, e1, e2, pele, plot, screenstats, compute_lsp)


def main():
    args = parse_arguments()
    quickphase(**args)


if __name__ == "__main__":
    main()