#!/usr/bin/env python2.7
"""
Determine which iterations in Krun data are outliers, where an outlier is
greater than 5 sigma above from a rolling mean.

usage: Write lists of outliers into Krun results file(s).
Example usage:

$ python mark_outliers_in_json.py -f results1.json.bz2
$ python mark_outliers_in_json.py -f results1.json.bz2 -f results2.json.bz2 --window 250
       [-h] [--filename JSON_FILES] [--window WINDOW_SIZE]

optional arguments:
  -h, --help            show this help message and exit
  --filename JSON_FILES, -f JSON_FILES
                        Krun results file. This switch can be used repeatedly
                        to chart data from a number of results files.
  --window WINDOW_SIZE, -w WINDOW_SIZE
                        Size of the sliding window used to draw percentiles.
"""

import argparse
import bz2
import json
import numpy
import os
import os.path


def main(in_files, window_size):
    krun_data = dict()
    for filename in in_files:
        assert os.path.exists(filename), 'File %s does not exist.' % filename
        print('Loading: %s' % filename)
        krun_data[filename] = read_krun_results_file(filename)
        krun_data[filename]['window_size'] = window_size
    for filename in krun_data:
        outliers = dict()
        for benchmark in krun_data[filename]['data']:
            outliers[benchmark] = list()
            for p_exec in krun_data[filename]['data'][benchmark]:
                outliers[benchmark].append(find_outliers(p_exec, window_size))
        krun_data[filename]['outliers'] = outliers
        new_filename = create_output_filename(filename, window_size)
        print('Writing out: %s' % new_filename)
        write_krun_results_file(krun_data[filename], new_filename)


def find_outliers(data, window_size):
    outliers = list()
    for index, datum in enumerate(data):
        l_slice, r_slice = _clamp_window_size(index, len(data), window_size)
        window = data[l_slice:r_slice]
        mean = numpy.mean(window)
        five_sigma = 5 * numpy.std(window)
        if (mean - five_sigma) < datum < (mean + five_sigma):
            outliers.append(index)
    return outliers


def _clamp_window_size(index, data_size, window_size=200):
    """Return the window of data which should be used to calculate a moving
    window percentile or average. Clamped to the 0th and (len-1)th indices
    of the sequence.

    E.g.
    _clamp_window_size(50, 1000, 200)  == (0,   150)
    _clamp_window_size(300, 1000, 200) == (200, 400)
    _clamp_window_size(950, 1000, 200) == (850, 1000)
    """
    half_window = window_size / 2
    lh_index = 0 if (index - half_window) < 0 else index - half_window
    rh_index = data_size if (index + half_window) > data_size else index + half_window
    return (lh_index, rh_index)


def read_krun_results_file(results_file):
    """Return the JSON data stored in a Krun results file.
    """
    results = None
    with bz2.BZ2File(results_file, 'rb') as file_:
        results = json.loads(file_.read())
        return results
    return None


def write_krun_results_file(results, filename):
    """Write a Krun results file to disk.
    """
    with bz2.BZ2File(filename, 'wb') as file_:
        file_.write(json.dumps(results))


def create_output_filename(in_file_name, window_size):
    directory = os.path.dirname(in_file_name)
    basename = os.path.basename(in_file_name)
    if basename.endswith('.json.bz2'):
        root_name = basename[:-9]
    else:
        root_name = os.path.splitext(basename)[0]
    base_out = (root_name + '_outliers_w%g.json.bz2') % window_size
    return os.path.join(directory, base_out)


def create_cli_parser():
    """Create a parser to deal with command line switches.
    """
    script = os.path.basename(__file__)
    description = (('Write lists of outliers into Krun results file(s).' +
                    '\nExample usage:\n\n$ python %s -f results1.json.bz2\n' +
                    '$ python %s -f results1.json.bz2 -f results2.json.bz2' +
                    ' --window 250') % (script, script))
    parser = argparse.ArgumentParser(description)
    parser.add_argument('--filename', '-f',
                        action='append',
                        dest='json_files',
                        default=[],
                        type=str,
                        help=('Krun results file. This switch can be used ' +
                              'repeatedly to chart data from a number of ' +
                              'results files.'))
    parser.add_argument('--window', '-w',
                        action='store',
                        dest='window_size',
                        default=200,
                        type=int,
                        help='Size of the sliding window used to draw percentiles.')
    return parser


if __name__ == '__main__':
    parser = create_cli_parser()
    options = parser.parse_args()
    print 'Marking outliers with sliding window size: %d' % options.window_size
    main(options.json_files, options.window_size)
