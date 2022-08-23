import argparse
import numpy as np
import os

from pathlib import Path

from gnssrefl.gps import l2c_l5_list
from gnssrefl.utils import read_files_in_dir, FileTypes, FileManagement


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("-year_end", default=None, help="year end", type=int)
    parser.add_argument("-min_tracks", default=None, help="minimum number of tracks needed to keep the mean RH", type=int)
    parser.add_argument("-freq", default=None, help="frequency", type=int)

    args = parser.parse_args().__dict__

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def apriori(station: str, year: int, year_end: int = None, freq: int = 20, min_tracks: int = 100):
    """
    apriori picks up reflector height results for a given station and year-year end and computes the mean values
    and returns a file with the mean values.
    Parameters
    __________
    station : string
        4 character ID of the station

    year : integer
        Year

    year_end : integer
        Day of year

    freq : integer, optional
        GPS frequency. Currently only supports l2c, which is frequency 20.

    min_tracks : integer, optional
        number of minimum tracks needed in order to keep the average RH

    Returns
    _______
    File with columns
    index, mean reflector_heights, satellite, average_azimuth, number of reflector heights in average, min azimuth, max azimuth

    Saves to $REFL_CODE/input/<station>_phaseRH.txt

    """
    # default l2c, but can ask for L1 and L2
    xdir = Path(os.environ["REFL_CODE"])
    if not year_end:
        year_end = year

    # not sure this is needed?
    if not min_tracks:
        min_tracks = 100

    print('Minimum number of tracks required ', min_tracks)
    years = np.arange(year, year_end+1)
    gnssir_results = []
    for y in years:
        # where the results are stored
        data_dir = xdir / str(y) / 'results' / station
        result_files = read_files_in_dir(data_dir)
        gnssir_results.extend(result_files)

    gnssir_results = np.array(gnssir_results).T

    # get the satellites for the requested frequency (20 for now) and most recent year
    print('Using L2C satellite list for December 31 on ', years[-1])
    l2c_sat, l5_sat = l2c_l5_list(years[-1], 365)
    # four quadrants
    azimuth_list = [0, 90, 180, 270]

    # window out frequency 20
    # the following function returns the index values where the statement is True
    frequency_indices = np.where(gnssir_results[10] == freq)

    reflector_height_gnssir_results = gnssir_results[2][frequency_indices]
    satellite_gnssir_results = gnssir_results[3][frequency_indices]
    azimuth_gnssir_results = gnssir_results[5][frequency_indices]

    b=0
    apriori_array = []
    for azimuth in azimuth_list:
        azimuth_min = azimuth
        azimuth_max = azimuth + 90
        for satellite in l2c_sat:
            reflector_heights = reflector_height_gnssir_results[(azimuth_gnssir_results > azimuth_min)
                                                                & (azimuth_gnssir_results < azimuth_max)
                                                                & (satellite_gnssir_results == satellite)]
            azimuths = azimuth_gnssir_results[(azimuth_gnssir_results > azimuth_min)
                                              & (azimuth_gnssir_results < azimuth_max)
                                              & (satellite_gnssir_results == satellite)]
            if (len(reflector_heights) > min_tracks):
                b = b+1
                average_azimuth = np.mean(azimuths)
                #print("{0:3.0f} {1:5.2f} {2:2.0f} {3:7.2f} {4:3.0f} {5:3.0f} {6:3.0f} ".format(b, np.mean(reflector_heights), satellite, average_azimuth, len(reflector_heights),azimuth_min,azimuth_max))
                apriori_array.append([b, np.mean(reflector_heights), satellite, average_azimuth, len(reflector_heights), azimuth_min, azimuth_max])

    apriori_path = FileManagement(station, FileTypes("apriori_rh_file")).get_file_path()

    # save file

    if (len(apriori_array) == 0):
        print('Found no results - perhaps wrong year? or ')
    else:
        print(f">>>> Apriori RH file used for phase estimation written to {apriori_path}")
        fout = open(apriori_path, 'w+')
        fout.write("{0:s}  \n".format('% apriori RH values used for phase estimation'))
        l = '% year/station ' + str(year) + ' ' + station 
        fout.write("{0:s}  \n".format(l))
        fout.write("{0:s}  \n".format('% tmin 0.05 (default)'))
        fout.write("{0:s}  \n".format('% tmax 0.50 (default)'))
        fout.write("{0:s}  \n".format('% Track  RefH SatNu MeanAz  Nval   Azimuths '))
        fout.write("{0:s}  \n".format('%         m   ' ))

    #with open(apriori_path, 'w') as my_file:
        np.savetxt(fout, apriori_array, fmt="%3.0f %6.3f %4.0f %7.2f   %4.0f  %3.0f  %3.0f")
        fout.close()


def main():
    args = parse_arguments()
    apriori(**args)


if __name__ == "__main__":
    main()
