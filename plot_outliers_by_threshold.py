#!/usr/bin/env python2.7

import argparse
import bz2
import json
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import FormatStrFormatter, FuncFormatter, MaxNLocator
import numpy
import os
import os.path
import seaborn

WINDOWS = [25, 50, 100, 200, 300, 400]
PDF_FILENAME = 'outliers_per_threshold.pdf'

SUBPLOT_PARAMS = {
    'hspace': 0.55,
    'bottom': 0.07,
    'left': 0.07,
    'right': 0.98,
    'top': 0.88,
    'wspace': 0.20,
}

# Default (PDF) font sizes
TICK_FONTSIZE = 6
TITLE_FONT_SIZE = 8
AXIS_FONTSIZE = 8
BASE_FONTSIZE = 10
LEGEND_FONTSIZE = 10

GRID_MINOR_X_DIVS = 20
GRID_MAJOR_X_DIVS = 10

GRID_MINOR_Y_DIVS = 12
GRID_MAJOR_Y_DIVS = 6

YTICK_FORMAT = '%d'
YLIM_ADJUST = 250

SPINE_LINESTYLE = "solid"
SPINE_LINEWIDTH = 1

LINE_COLOUR = 'k'
LINE_WIDTH = 1
FILL_ALPHA = 0.2

MAX_SUBPLOTS_PER_ROW = 2
MARKERSIZE=4

seaborn.set_palette("colorblind")
seaborn.set_style('whitegrid', {"lines.linewidth": 1.0, "axes.linewidth": 1.0})
seaborn.set_context("paper")

plt.figure(tight_layout=True)


def sum_outliers(data):
    num_outliers = 0
    for outliers in data:
        num_outliers += len(outliers)
    return num_outliers


def plot_results(outliers_per_thresh, filename):
    """Plot a page of benchmarks.
    """
    num_windows = len(outliers_per_thresh.keys())  # == number of subplots.
    n_rows = int(math.ceil(float(num_windows) / MAX_SUBPLOTS_PER_ROW))
    n_cols = min(MAX_SUBPLOTS_PER_ROW, num_windows)
    fig, axes = plt.subplots(n_rows, n_cols, squeeze=False)
    index, row, col = 0, 0, 0
    pdf = PdfPages(filename)
    # Calculate ymin / ymax
    ymin = outliers_per_thresh[WINDOWS[0]][1]['all_outliers']
    ymax = ymin
    for window in outliers_per_thresh:
        for threshold in outliers_per_thresh[window]:
            for outlier_type in ('all_outliers', 'unique_outliers', 'common_outliers'):
                value = outliers_per_thresh[window][threshold][outlier_type]
                if value < ymin:
                    ymin = value
                if value > ymax:
                    ymax = value
    y_bounds = (ymin - YLIM_ADJUST, ymax + YLIM_ADJUST)
    # Draw subplots
    while index < num_windows:
        window = WINDOWS[index]
        axis = axes[row, col]
        axis.ticklabel_format(useOffset=False)
        x_bounds = (0, len(outliers_per_thresh[window].keys()))
        axis.set_xlim(x_bounds)
        axis.set_ylim(y_bounds)
        # Keep hold of handles / labels for legend.
        handles, labels = draw_subplot(axis, outliers_per_thresh[window],
                                       x_bounds, y_bounds, window)
        col += 1
        if col == MAX_SUBPLOTS_PER_ROW:
            col = 0
            row += 1
        index = row * MAX_SUBPLOTS_PER_ROW + col
    fig.subplots_adjust(**SUBPLOT_PARAMS)
    # Add margin to x-axis. Must be done *after* setting xlim and ylim
    # and calling subplots_adjust().
    index, row, col = 0, 0, 0
    while index < num_windows:
        window = WINDOWS[index]
        axis = axes[row, col]
        add_margin_to_axes(axis, x=0.02, y=0.00)
        col += 1
        if col == MAX_SUBPLOTS_PER_ROW:
            col = 0
            row += 1
        index = row * MAX_SUBPLOTS_PER_ROW + col
    fig.legend(handles, labels, loc='upper center', fontsize=LEGEND_FONTSIZE, ncol=10,)
    pdf.savefig(fig, dpi=fig.dpi, orientation='portrait', bbox_inches='tight')
    pdf.close()
    print('Saved: %s' % filename)


def draw_subplot(axis, data, x_range, y_range, window_size):
    all_ = []
    common = []
    unique = []
    for threshold in data:
        all_.append(data[threshold]['all_outliers'])
        common.append(data[threshold]['common_outliers'])
        unique.append(data[threshold]['unique_outliers'])
    axis.plot(numpy.array(all_), marker='o', linestyle='-',
              label='All outliers', markevery=1, markersize=MARKERSIZE)
    axis.plot(numpy.array(common), marker='o', linestyle='-',
              label='Common outliers', markevery=1, markersize=MARKERSIZE)
    axis.plot(numpy.array(unique), marker='o', linestyle='-',
              label='Unique outliers', markevery=1, markersize=MARKERSIZE)
    # Re-style the chart.
    major_xticks = compute_grid_offsets(
        x_range[0], x_range[1], GRID_MAJOR_X_DIVS)
    minor_xticks = compute_grid_offsets(
        x_range[0],x_range[1], GRID_MINOR_X_DIVS)
    major_yticks = compute_grid_offsets(
        y_range[0], y_range[1], GRID_MAJOR_Y_DIVS)
    minor_yticks = compute_grid_offsets(
        y_range[0], y_range[1], GRID_MINOR_Y_DIVS)
    style_axis(axis, major_xticks, minor_xticks, major_yticks, minor_yticks)
    # Set title, axis labels and legend.
    axis.set_xlabel('Threshold for window size %d' % window_size, fontsize=AXIS_FONTSIZE)
    axis.set_ylabel('Number of outliers', fontsize=AXIS_FONTSIZE)
    axis.set_ylim(y_range)
    # Format ticks.
    axis.xaxis.set_major_locator(MaxNLocator(integer=True, steps=xrange(11)))
    axis.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: str(int(x + 1))))
    axis.yaxis.set_major_formatter(FormatStrFormatter(YTICK_FORMAT))
    # Return artists needed for legend.
    handles, labels = axis.get_legend_handles_labels()
    return handles, labels


def add_margin_to_axes(axis, x=0.01, y=0.01):
    """Seaborn-friendly way to add margins to axes (default 1% margin).
    """

    if x > .0:
        xlim = axis.get_xlim()
        xmargin = (xlim[1] - xlim[0]) * x
        axis.set_xlim(xlim[0] - xmargin, xlim[1] + xmargin)
    if y > .0:
        ylim = axis.get_ylim()
        ymargin = (ylim[1] - ylim[0]) * y
        axis.set_ylim(ylim[0] - ymargin, ylim[1] + ymargin)


def compute_grid_offsets(d_min, d_max, num):
    rng = float(d_max) - d_min
    freq =  rng / num
    return [d_min + i * freq for i in xrange(num + 1)]


def style_axis(ax, major_xticks, minor_xticks, major_yticks, minor_yticks):
    ax.set_xticks(major_xticks)
    ax.set_xticks(minor_xticks, minor=True)
    ax.set_yticks(major_yticks)
    ax.set_yticks(minor_yticks, minor=True)

    x_ax = ax.get_xaxis()
    y_ax = ax.get_yaxis()

    x_ax.set_ticks_position('none')
    y_ax.set_ticks_position('none')
    x_ax.set_tick_params(labelsize=TICK_FONTSIZE)
    y_ax.set_tick_params(labelsize=TICK_FONTSIZE)

    ax.grid(which='minor', alpha=0.4)
    ax.grid(which='major', alpha=0.8)

    for i in ["top", "bottom"]:
        ax.spines[i].set_linestyle(SPINE_LINESTYLE)
        ax.spines[i].set_linewidth(SPINE_LINEWIDTH)

    for i in ["right", "left"]:
        ax.spines[i].set_visible(False)

    ax.frameon = False


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


def _tuckey_all_outliers(data, window_size):
    # Ignore windows that do not have a full set of data.
    all_outliers = list()
    for index, datum in enumerate(data):
        l_slice, r_slice = _clamp_window_size(index, len(data), window_size)
        if l_slice == 0 and r_slice < window_size:
            continue
        window = data[l_slice:r_slice]
        median = numpy.median(window)
        pc_band = 3 * (numpy.percentile(window, 90.0) - numpy.percentile(window, 10.0))
        if datum > (median + pc_band) or datum < (median - pc_band):
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
    return None


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
    plot_results(outliers_per_thresh, PDF_FILENAME)


if __name__ == '__main__':
    parser = create_cli_parser()
    options = parser.parse_args()
    main(options.json_files[0])
