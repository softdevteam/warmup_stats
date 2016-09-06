#!/usr/bin/env pypy

import argparse
import bz2
import json
import math
import os
import sys


FILENAME = 'outliers_per_threshold.json.bz2'
WINDOWS = [25, 50, 100, 200, 300, 400]


def sum_outliers(data):
    num_outliers = 0
    for outliers in data:
        num_outliers += len(outliers)
    return num_outliers


def get_outliers(all_outliers, window_size, threshold=1):
    common, unique = list(), list()
    for index, outliers in enumerate(all_outliers):
        common_exec = list()
        unique_exec = list()
        for outlier in outliers:
            other_execs = all_outliers[:index] + all_outliers[(index + 1):]
            sum_ = 0
            for execution in other_execs:
                if outlier in execution:
                    sum_ += 1
            if sum_ >= threshold:
                common_exec.append(outlier)
            else:
                unique_exec.append(outlier)
        common.append(common_exec)
        unique.append(unique_exec)
    return common, unique


def median(data):
    """Naive algorithm to compute the median of a list of (sorted) data.
    Linear interpolation is used when the percentile lies between two data
    points. It is assumed that the data contains no NaN or similar.
    This function is identical to percentile(data, 50) but faster.
    """
    size = len(data)
    if size == 0:
        raise ValueError('Cannot compute percentile of empty list!')
    if size == 1:
        return data[0]
    index = (size - 1) // 2
    if size % 2 == 1:
        return data[index]
    else:
        return (data[index] + data[index + 1]) / 2.0


def percentile(data, pc):
    """Naive algorithm to compute the pc'th percentile of a list of (sorted) data.
    Linear interpolation is used when the percentile lies between two data
    points. It is assumed that the data contains no NaN or similar.
    """
    if pc < 0 or pc > 100:
        raise ValueError('Percentile must be in the range [0, 100].')
    size = len(data)
    if size == 0:
        raise ValueError('Cannot compute percentile of empty list!')
    if size == 1:
        return data[0]
    index = (size - 1) * (pc / 100.0)
    index_floor = math.floor(index)
    index_ceil = math.ceil(index)
    if index_floor == index_ceil:
        return data[int(index)]
    d0 = data[int(index_floor)] * (index_ceil - index)
    d1 = data[int(index_ceil)] * (index - index_floor)
    return d0 + d1


def _tuckey_all_outliers(data, window_size):
    # Ignore windows that do not have a full set of data.
    all_outliers = list()
    size = len(data)
    for index, datum in enumerate(data):
        l_slice, r_slice = _clamp_window_size(index, size, window_size)
        if l_slice == 0 and r_slice < window_size:
            continue
        window = data[l_slice:r_slice]
        window_sorted = sorted(window)
        window_median = median(window_sorted)
        pc_band = 3 * (percentile(window_sorted, 90.0) - percentile(window_sorted, 10.0))
        if datum > (window_median + pc_band) or datum < (window_median - pc_band):
            all_outliers.append(index)
    return all_outliers


def get_all_outliers(data, window_size):
    return _tuckey_all_outliers(data, window_size)


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


def create_cli_parser():
    """Create a parser to deal with command line switches.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('json_files', nargs='+', action='append', default=[],
                        type=str, help='One or more Krun result files.')
    return parser


def main(in_files):
    krun_data = dict()
    for filename in in_files:
        assert os.path.exists(filename), 'File %s does not exist.' % filename
        print('Loading: %s' % filename)
        krun_data[filename] = read_krun_results_file(filename)
    # Get number of executions per benchmark, must be the same for all files!
    bench_1 = krun_data[filename]['data'].keys()[0]  # Name of first benchmark.
    n_execs = len(krun_data[filename]['data'][bench_1])
    print ('ASSUMING %d process executions per vm:benchmark:variant '
           'in ALL files.' % n_execs)
    # Scaffold results dictionary.
    outliers_per_thresh = dict()
    for window in WINDOWS:
        outliers_per_thresh[window] = dict()
        for threshold in xrange(1, n_execs):
            outliers_per_thresh[window][threshold] = {'all_outliers': 0,
                              'common_outliers': 0, 'unique_outliers': 0}
    # Calculate numbers of outliers for each window / threshold.
    for filename in in_files:
        for window in outliers_per_thresh:
            for thresh in outliers_per_thresh[window]:
                print 'Window %d, threshold %d, file %s' % (window, thresh, filename)
                outliers_per_key = dict()  # All executions for a vm:bench:variant
                for key in krun_data[filename]['data']:
                    outliers_per_key[key] = list()  # Outliers for each execution
                    for p_exec in krun_data[filename]['data'][key]:
                        outliers_per_key[key].append(get_all_outliers(p_exec, window))
                    common, unique = get_outliers(outliers_per_key[key], window, thresh)
                    outliers_per_thresh[window][thresh]['all_outliers'] += sum_outliers(outliers_per_key[key])
                    outliers_per_thresh[window][thresh]['common_outliers'] += sum_outliers(common)
                    outliers_per_thresh[window][thresh]['unique_outliers'] += sum_outliers(unique)
    with bz2.BZ2File(FILENAME, 'w') as f:
        f.write(json.dumps(outliers_per_thresh, indent=1, sort_keys=True,
                           encoding='utf-8'))


if __name__ == '__main__':
    if sys.subversion[0] != 'PyPy':
        print('WARNING: This script is designed to run efficiently with the '
              'PyPy interpreter.\nIt is likely to run very slowly on other VMs.')
    parser = create_cli_parser()
    options = parser.parse_args()
    main(options.json_files[0])
