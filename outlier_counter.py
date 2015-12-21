#!/usr/bin/env python2.7
"""
usage: outlier_counter.py [-h] [--filename JSON_FILES] [--infile IN_FILE]
                          [--latexfile LATEX_FILE] [--jsonfile JSON_FILE]
                          [--plotfile PLOT_FILE] [--pcmin PERCENTILE_MIN]
                          [--pcmax PERCENTILE_MAX] [--winmin WINDOW_MIN]
                          [--winmax WINDOW_MAX]

Determine the number of outliers that would be excluded from a Krun results file by choosing different sliding window sizes and different levels of confidence.

Example usage:

    $ python outlier_counter.py -f bencher_results.json.bz2 --pcmin 75 --pcmax 100 --winmin 2 --winmax 500

    $ python outlier_counter.py -i data.json

optional arguments:
  -h, --help            show this help message and exit
  --filename JSON_FILES, -f JSON_FILES
                        Krun results file. This switch can be used repeatedly to chart data from a number of results files.
  --infile IN_FILE, -i IN_FILE
                        JSON file containing outlier counts. Use this to load output from this script and produce LaTeX and PNG files.
  --latexfile LATEX_FILE, -l LATEX_FILE
                        Name of the LaTeX file to write to.
  --jsonfile JSON_FILE, -j JSON_FILE
                        Name of the JSON file to write to.
  --plotfile PLOT_FILE, -p PLOT_FILE
                        Name of the file to write a plot of the data to.
  --pcmin PERCENTILE_MIN, -m PERCENTILE_MIN
                        Smallest percentile to consider.
  --pcmax PERCENTILE_MAX, -n PERCENTILE_MAX
                        Largest percentile to consider.
  --winmin WINDOW_MIN, -w WINDOW_MIN
                        Smallest window size to consider.
  --winmax WINDOW_MAX, -x WINDOW_MAX
                        Largest window size to consider.
"""

import argparse
import bz2
import copy
import functools
import json
import matplotlib
import matplotlib.pyplot as pyplot
import multiprocessing
import numpy
import numpy.random
import os
import os.path
import seaborn

LATEX_FILENAME = 'outlier_counts_table.tex'
JSON_FILENAME  = 'outlier_counts_data.json'
PLOT_FILENAME  = 'outlier_counts_plot.pdf'

MIN_WSIZE = 100  # Minimum window size.
MAX_WSIZE = 500  # Maximum window size.

MIN_PC = 75   # Minimum percentile.
MAX_PC = 100  # Maximum percentile.

seaborn.set_palette("colorblind")
seaborn.set_style('whitegrid', {'grid' : False, 'axes.grid' : False})
seaborn.set_context("paper")

CHART_TITLE = ('Ratio of code excluded as outliers for a variety\n' +
               'of sliding window sizes and percentiles')
X_LABEL = 'Window size'
Y_LABEL = 'Percentile'
Z_LABEL = 'Ratio of outliers in data'
MAX_XTICKLABELS = 20
MAX_YTICKLABELS = 20

CMAP = seaborn.cubehelix_palette(8, start=.5, rot=-.75, as_cmap=True)

TICK_FONTSIZE = 12
TITLE_FONT_SIZE = 17
AXIS_FONTSIZE = 14
BASE_FONTSIZE = 13
FONT = {
    'family': 'sans',
    'weight': 'regular',
    'size': BASE_FONTSIZE,
}
matplotlib.rc('font', **FONT)

EXPORT_SIZE_INCHES = 20, 8

__LATEX_HEADER = lambda num_iterations: """
\documentclass[12pt]{article}
\usepackage{longtable}
\usepackage{booktabs}
\\title{Outlier counts}
\\begin{document}
\maketitle
\\begin{center}
\\begin{longtable}{c|c|c|c}
\\toprule
Window & Percentile & Number of        & Percentage of data \\\\
size   &            & outliers (of %s) & classed as outliers \\\\
\midrule
\endfirsthead
\\toprule
Window & Percentile & Number of        & Percentage of data \\\\
size   &            & outliers (of %s) & classed as outliers \\\\
\midrule
\endhead
\midrule
\endfoot
\\bottomrule
\endlastfoot
""" % (num_iterations, num_iterations)

__LATEX_FOOTER = """
\end{longtable}
\end{center}
\end{document}
"""


def main(data_dcts, p_min, p_max, w_min, w_max, tex_file, plot_file, json_file):
    """Count outliers for all window size / percentile configurations.
    Save results in a JSON file.
    """
    num_outliers = dict()
    # window size -> confidence level (percentile cut-off) -> number of outliers
    for w_index in xrange(w_min, w_max + 1):
        num_outliers[w_index] = dict()
        for p_index in xrange(p_min, p_max + 1):
            num_outliers[w_index][p_index] = 0
    num_iterations = 0
    # Collect data from all executions in the Krun results file.
    all_executions = list()
    for machine in data_dcts:
        keys = sorted(data_dcts[machine]['data'].keys())
        for key in keys:
            bench, vm, variant = key.split(':')
            executions = data_dcts[machine]['data'][key]
            if len(executions) == 0:
                print('Skipping: %s (no executions)' % key)
            elif len(executions[0]) == 0:
                print('Skipping: %s (benchmark crashed)' % key)
            else:
                print('Collecting data from: %s' % key)
                for execution in executions:
                    num_iterations += len(execution)
                all_executions.append(executions)
    # In testing benchmarks of 4000 iterations took >10 minutes to process on
    # a fast machine, so we use as much parallelism as possible.
    print('Collected %d benchmarks for processing.' % len(all_executions))
    outlier_dicts = [copy.copy(num_outliers) for _ in xrange(len(all_executions))]
    args = zip(outlier_dicts, all_executions)
    results = list()
    accept_result = lambda result : results.append(result)
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    func = functools.partial(_target, p_min, p_max, w_min, w_max)
    print('Calculating outliers. This is likely to take a very long time.')
    for arg in args:
        pool.apply_async(func, args=(arg, ), callback=accept_result)
    pool.close()
    pool.join()
    # Each process had its own copy of num_outliers, so we need to merge
    # all the results into a single dictionary.
    print('Collating data from %d results.' % len(results))
    for result in results:
        for w_index in num_outliers:
            for p_index in num_outliers[w_index]:
                num_outliers[w_index][p_index] += result[w_index][p_index]
    # Write out results.
    write_results_as_json(num_outliers, num_iterations, json_file)
    write_results_as_latex(num_outliers, num_iterations, tex_file)
    reshaped, xlim, ylim = reshape_data_for_plotting(num_outliers, num_iterations)
    write_results_as_plot(reshaped, xlim, ylim, plot_file)
    return


def _target(p_min, p_max, w_min, w_max, args):
    num_outliers, executions = args
    counts = count_outliers(executions, p_min, p_max, w_min, w_max)
    for w_index in counts:
        for p_index in counts[w_index]:
            num_outliers[w_index][p_index] += counts[w_index][p_index]
    return num_outliers


def write_results_as_json(num_outliers, num_iterations, json_file):
    print('Writing data to %s.' % json_file)
    num_outliers['TOTAL_ITERATIONS'] = num_iterations
    with open(json_file, 'w+') as fp:
        json.dump(num_outliers, fp, sort_keys=True, indent=4)
    return


def write_results_as_latex(num_outliers, num_iterations, tex_file):
    """Write a results file that looks like this:

                         Outlier Count

    Window       | Percentile   | # outliers   | % Data Classified
    Size         |              | (of 4000)    | as Outliers
    ==================================================================
    1            |  99          | 200          | 10%
    1            |  95          | 400          | 20%
    1            |  90          | 400          | 20%
    2            |  99          | 200          | 10%
    2            |  95          | 400          | 20%
    2            |  90          | 400          | 20%
    ...
    """
    print('Writing data to %s.' % tex_file)
    if 'TOTAL_ITERATIONS' in num_outliers.keys():
        del num_outliers['TOTAL_ITERATIONS']
    with open(tex_file, 'w') as fp:
        fp.write(__LATEX_HEADER(num_iterations))
        for window_size in num_outliers:
            for percentile in num_outliers[window_size]:
                pc = (float(num_outliers[window_size][percentile]) /
                      float(num_iterations) * 100.0)
                row = ('%d & %d & %d & %.3f\\\\ \n' %
                       (window_size, percentile,
                        num_outliers[window_size][percentile],
                        round(pc, 3)))
                fp.write(row)
            if window_size != MAX_WSIZE:
                fp.write('\midrule \n')
        fp.write(__LATEX_FOOTER)
    return


def write_results_as_plot(reshaped_data, xlim, ylim, plot_file):
    print('Writing plot to %s.' % plot_file)
    # Plot the data.
    figure, axes = pyplot.subplots()
    axes = seaborn.heatmap(reshaped_data,
                           ax=axes,
                           cmap=CMAP,
                           cbar=True,
                           linewidths=0.0,  # No space between rectangles.
                           # Workaround to remove gridlines.
                           # See: https://github.com/mwaskom/seaborn/issues/373
                           # If this doesn't work save to a PNG by passing in:
                           # --plotfile myfilename.png.
                           rasterized=True,
                           robust=True)
    axes.invert_yaxis()
    x_ax = axes.get_xaxis()
    y_ax = axes.get_yaxis()
    # Set xticks and yticks based on the original set of results.
    # We need to do this because neither the x or y axes start at 0.
    xticks = numpy.arange(xlim[0], xlim[1] + 1, 10)
    yticks = numpy.arange(ylim[0], ylim[1] + 1, 5)[::-1]
    axes.set_xticklabels([str(tick) for tick in xticks],
                         rotation=90, horizontalalignment='center')
    axes.set_yticklabels([str(tick) for tick in yticks],
                         verticalalignment='top')
    # Set labels.
    axes.set_title(CHART_TITLE, fontsize=TITLE_FONT_SIZE)
    axes.set_xlabel(X_LABEL, fontsize=AXIS_FONTSIZE)
    axes.set_ylabel(Y_LABEL, fontsize=AXIS_FONTSIZE)
    # Reduce number of tick labels on both axes.
    xloc = pyplot.MaxNLocator(len(xticks), prune=None, trim=False)
    yloc = pyplot.MaxNLocator(len(yticks), prune=None, trim=False)
    x_ax.set_major_locator(xloc)
    y_ax.set_major_locator(yloc)
    # Style ticks.
    x_ax.set_ticks_position('none')
    y_ax.set_ticks_position('none')
    x_ax.set_tick_params(labelsize=TICK_FONTSIZE)
    y_ax.set_tick_params(labelsize=TICK_FONTSIZE)
    # Turn grid lines off for both axes.
    axes.grid(False, axis='both', which='both')
    # Set-up figure for saving.
    pyplot.tight_layout(True)
    figure.set_size_inches(*EXPORT_SIZE_INCHES)
    figure.savefig(plot_file, dpi=figure.dpi)
    return


def reshape_data_for_plotting(results, total):
    """Extract data from the results dictionary and place into three arrays.
    """
    if 'TOTAL_ITERATIONS' in results.keys():
        del results['TOTAL_ITERATIONS']
    # How many window sizes and percentiles did we try?
    w_sizes = results.keys()
    num_w_sizes = max(w_sizes) + 1 - min(w_sizes)
    pcs = results[min(w_sizes)].keys()
    num_pc_sizes = max(pcs) + 1 - min(pcs)
    # Find the x and y limits to pass back for plotting.
    xlim = (min(w_sizes), max(w_sizes))
    ylim = (min(pcs), max(pcs))
    # Create an array of the correct shape.
    rectangular_data = numpy.zeros(shape=(num_pc_sizes, num_w_sizes))
    # Construct the rectangular array.
    w_sorted = sorted(w_sizes)
    p_sorted = sorted(pcs)
    for w_index, window in enumerate(w_sorted):
        for p_index, percentile in enumerate(p_sorted):
            rectangular_data[p_index][w_index] = results[window][percentile]
    return rectangular_data, xlim, ylim


def count_outliers(data, pc_min, pc_max, win_min, win_max):
    counts = dict()
    for window_size in xrange(win_min, win_max + 1):
        counts[window_size] = dict()
        for percentile in xrange(pc_min, pc_max + 1):
            counts[window_size][percentile] = 0
    for execution in data:
        data_narray = numpy.array(execution)
        pc_data = dict()
        # Calculate sliding window percentiles.
        for window_size in xrange(win_min, win_max + 1):
            pc_data[window_size] = sliding_window_percentiles(data_narray,
                                                              pc_min,
                                                              pc_max,
                                                              window_size)
        # Calculate counts.
        for window_size in xrange(win_min, win_max + 1):
            for percentile in pc_data[window_size]:
                percentile_array = numpy.array(pc_data[window_size][percentile])
                # the comparison returns a boolean array
                # the sum counts the True entries (True = 1)
                count = (data_narray > percentile_array).sum()
                counts[window_size][percentile] += count
    return counts


def sliding_window_percentiles(data, pc_min, pc_max, window_size=200):
    """Data should be a 1xn matrix.
    Returns a dictionary of:
        percentile : float -> percentile values : float list
    """
    pc_data = dict()
    percentiles = range(pc_min, pc_max + 1)
    for percentile in percentiles:
        pc_data[percentile] = list()
    for index, _ in enumerate(data):
        l_slice, r_slice = _clamp_window_size(index, len(data), window_size)
        window = data[l_slice:r_slice]
        values = numpy.percentile(window, percentiles, interpolation='nearest')
        for percentile, value in zip(percentiles, values):
            pc_data[percentile].append(value)
    return pc_data


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


def get_data_dictionaries(json_files):
    """Read a list of BZipped JSON files and return their contents as a
    dictionaries of machine name -> JSON values.
    """
    data_dictionary = dict()
    for filename in json_files:
        assert os.path.exists(filename), 'File %s does not exist.' % filename
        print('Loading: %s' % filename)
        data = read_krun_results_file(filename)
        machine_name = data['audit']['uname'].split(' ')[1]
        if '.' in machine_name:  # Remove domain, if there is one.
            machine_name = machine_name.split('.')[0]
        data_dictionary[machine_name] = data
    return data_dictionary


def create_cli_parser():
    """Create a parser to deal with command line switches.
    """
    script = os.path.basename(__file__)
    description = (('Determine the number of outliers that would be ' +
                    'excluded from a Krun results file by choosing different ' +
                    'sliding window sizes and different levels of confidence.'
                    '\n\nExample usage:\n\n' +
                    '\t$ python %s -f bencher_results.json.bz2' +
                    ' --pcmin 75 --pcmax 100 --winmin 2 --winmax 500\n\n' +
                    '\t$ python %s -i data.json\n\n') % (script, script))
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--filename', '-f',
                        action='append',
                        dest='json_files',
                        default=[],
                        type=str,
                        help=('Krun results file. This switch can be used ' +
                              'repeatedly to chart data from a number of ' +
                              'results files.'))
    parser.add_argument('--infile', '-i',
                        action='store',
                        dest='in_file',
                        default=None,
                        type=str,
                        help=('JSON file containing outlier counts. ' +
                              'Use this to load output from this ' +
                              'script and produce LaTeX and PNG files.'))
    parser.add_argument('--latexfile', '-l',
                        action='store',
                        dest='latex_file',
                        default=LATEX_FILENAME,
                        type=str,
                        help=('Name of the LaTeX file to write to.'))
    parser.add_argument('--jsonfile', '-j',
                        action='store',
                        dest='json_file',
                        default=JSON_FILENAME,
                        type=str,
                        help=('Name of the JSON file to write to.'))
    parser.add_argument('--plotfile', '-p',
                        action='store',
                        dest='plot_file',
                        default=PLOT_FILENAME,
                        type=str,
                        help=('Name of the file to write a ' +
                              'plot of the data to.'))
    parser.add_argument('--pcmin', '-m',
                        action='store',
                        dest='percentile_min',
                        default=MIN_PC,
                        type=int,
                        help=('Smallest percentile to consider.'))
    parser.add_argument('--pcmax', '-n',
                        action='store',
                        dest='percentile_max',
                        default=MAX_PC,
                        type=int,
                        help=('Largest percentile to consider.'))
    parser.add_argument('--winmin', '-w',
                        action='store',
                        dest='window_min',
                        default=MIN_WSIZE,
                        type=int,
                        help=('Smallest window size to consider.'))
    parser.add_argument('--winmax', '-x',
                        action='store',
                        dest='window_max',
                        default=MAX_WSIZE,
                        type=int,
                        help=('Largest window size to consider.'))
    return parser


if __name__ == '__main__':
    import sys
    parser = create_cli_parser()
    options = parser.parse_args()
    if options.in_file is None and len(options.json_files) == 0:
        print('Need EITHER a Krun results file or outlier data.')
        print(parser.print_help())
        sys.exit(1)
    if options.in_file is not None and len(options.json_files) > 0:
        print('Cannot pass in BOTH a Krun results file and outlier data')
        print(parser.print_help())
        sys.exit(1)
    if options.percentile_min < 1:
        print('Minimum percentile value is 1, %d is too low.' %
              options.percentile_min)
        sys.exit(1)
    if options.percentile_max > 100:
        print('Maximum percentile value is 100, %d is too high.' %
              options.percentile_max)
        sys.exit(1)
    if options.window_min < 2:
        print('Minimum window size is 2, %d is too low.' %
              options.window_min)
        sys.exit(1)
    if options.in_file is not None:
        # Read a JSON file produced by this script and dump
        # a LaTeX file containing the data in tabular form and
        # a plot of the data. Can be a PDF or image file.
        with open(options.in_file, 'r') as fp:
            print('Loading %s' % options.in_file)
            data = json.load(fp)
            total_iters = data['TOTAL_ITERATIONS']
            del data['TOTAL_ITERATIONS']
            numeric_data = dict()
            for w_key in data:
                numeric_data[int(w_key)] = dict()
                for p_key in data[w_key]:
                    numeric_data[int(w_key)][int(p_key)] = data[w_key][p_key]
            write_results_as_latex(numeric_data, total_iters, options.latex_file)
            reshaped, xlim, ylim = reshape_data_for_plotting(numeric_data, total_iters)
            write_results_as_plot(reshaped, xlim, ylim, options.plot_file)
    else:
        # Count outliers based on a Krun results file.
        main(get_data_dictionaries(options.json_files),
             options.percentile_min,
             options.percentile_max,
             options.window_min,
             options.window_max,
             options.latex_file,
             options.plot_file,
             options.json_file)
