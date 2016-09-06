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
import os
import os.path
import seaborn

from calculate_outliers_by_threshold import WINDOWS

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
    print outliers_per_thresh.keys()
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
    axis.plot(all_, marker='o', linestyle='-',
              label='All outliers', markevery=1, markersize=MARKERSIZE)
    axis.plot(common, marker='o', linestyle='-',
              label='Common outliers', markevery=1, markersize=MARKERSIZE)
    axis.plot(unique, marker='o', linestyle='-',
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


def _map_json_keys_to_ints(json_object):
    """Some dictionary keys in outlier JSON files are integers. These will
    be converted to unicode by json.dump and need to be parsed.
    """
    if isinstance(json_object, dict):
        try:
            return {int(key): value for key, value in json_object.items()}
        except ValueError:
            return json_object
    return json_object


def read_outliers_per_threshold_file(outliers_file):
    """Return the JSON data stored in a Krun results file.
    """
    results = None
    with bz2.BZ2File(outliers_file, 'rb') as file_:
        results = json.loads(file_.read(), encoding='utf-8',
                             object_hook=_map_json_keys_to_ints)
    return results


def create_cli_parser():
    """Create a parser to deal with command line switches.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('json_file', action='store',
                        type=str, help=('Outlier per threshold file. This file '
                                        'should have been generated by the '
                                        'calculate_outliers_by_threshold '
                                        'script.'))
    return parser


def main(filename):
    assert os.path.exists(filename), 'File %s does not exist.' % filename
    print('Loading: %s' % filename)
    outliers_per_thresh = read_outliers_per_threshold_file(filename)
    plot_results(outliers_per_thresh, PDF_FILENAME)


if __name__ == '__main__':
    parser = create_cli_parser()
    options = parser.parse_args()
    main(options.json_file)
