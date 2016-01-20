#!/usr/bin/env python2.7
"""
Plot data from Krun results file(s).
"""

import argparse
import bz2
import datetime
import json
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy
import numpy.random
import os
import os.path
import seaborn
import sys

seaborn.set_palette("colorblind")
seaborn.set_style('whitegrid', {"lines.linewidth": 1.0, "axes.linewidth": 1.0})
seaborn.set_context("paper")

plt.figure(tight_layout=True)

PDF_FILENAME = 'krun_results.pdf'

# Configures border and spacing of subplots.
# Here we just make it more space efficient for the paper
SUBPLOT_PARAMS = {
    'hspace': 0.35,
    'bottom': 0.07,
    'left': 0.07,
    'right': 0.98,
    'top': 0.95,
    'wspace': 0.20,
}

# Display names that can't be formatted with .title()
BENCHMARKS = {
    'binarytrees':      'Binary Trees',
    'spectralnorm':     'Spectral Norm',
    'fannkuch_redux':   'Fannkuch Redux',
    'nbody':            'N-Body',
}

GRID_MINOR_X_DIVS = 20
GRID_MAJOR_X_DIVS = 10

GRID_MINOR_Y_DIVS = 12
GRID_MAJOR_Y_DIVS = 6

SPINE_LINESTYLE = "solid"
SPINE_LINEWIDTH = 1

LINE_COLOUR = 'k'
LINE_WIDTH = 1
FILL_ALPHA = 0.2

OUTLIER_MARKER = 'ro'
UNIQUE_MARKER = 'bo'
COMMON_MARKER = 'go'

# Default (PDF) font sizes
TICK_FONTSIZE = 18
TITLE_FONT_SIZE = 20
AXIS_FONTSIZE = 20
BASE_FONTSIZE = 20

FONT = {
    'family': 'sans',
    'weight': 'regular',
    'size': BASE_FONTSIZE,
}
matplotlib.rc('font', **FONT)

MAX_SUBPLOTS_PER_ROW = 2
EXPORT_SIZE_INCHES = 10, 8  # Based on 1 chart per page.
DPI = 300


def main(is_interactive, data_dcts, window_size, outfile, xlimits, single_exec,
         with_outliers, unique_outliers, mean=False, sigma=False,
         benchmark=None):
    """Create a new dictionary in bmark->machine->data format.
    Plot all data.
    """
    pdf = None  # PDF output (non-interactive mode).

    if not is_interactive:
        pdf = PdfPages(outfile)
        set_pdf_metadata(pdf)

    benchmark_in_results = False
    for machine in data_dcts:
        keys = sorted(data_dcts[machine]['data'].keys())
        if benchmark in keys:
            benchmark_in_results = True
        for key in keys:
            bench, vm, variant = key.split(':')
            executions = data_dcts[machine]['data'][key]
            if benchmark is None and len(executions) == 0:
                print('Skipping: %s (no executions)' % key)
            elif benchmark is None and len(executions[0]) == 0:
                print('Skipping: %s (benchmark crashed)' % key)
            elif (benchmark is not None) and key != benchmark:
                continue
            else:
                if with_outliers:
                    outliers = data_dcts[machine]['outliers'][key]
                else:
                    outliers = None
                if unique_outliers:
                    unique = data_dcts[machine]['unique_outliers'][key]
                    common = data_dcts[machine]['common_outliers'][key]
                else:
                    unique, common = None, None
                fig, export_size = draw_page(is_interactive,
                                             key,
                                             executions,
                                             machine,
                                             window_size,
                                             xlimits,
                                             single_exec,
                                             outliers,
                                             unique,
                                             common,
                                             mean,
                                             sigma)
                if not is_interactive:
                    fig.set_size_inches(*export_size)
                    pdf.savefig(fig, dpi=fig.dpi, orientation='landscape',
                                bbox_inches='tight')
                    plt.close()
        if not is_interactive:
            pdf.close()
            print('Saved: %s' % outfile)
        if benchmark is not None and not benchmark_in_results:
            fatal_error('Benchmark: %s did not appear in any results file.' %
                        benchmark)


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


def compute_grid_offsets(d_min, d_max, num):
    rng = float(d_max) - d_min
    freq =  rng / num
    return [d_min + i * freq for i in xrange(num + 1)]


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


def draw_subplot(axis, data, title, x_range, y_range, window_size, outliers,
                 unique, common, mean, sigma):
    data_narray = numpy.array(data)

    # Plot the original measurements.
    axis.plot(data_narray, label='Measurement', color=LINE_COLOUR)

    # If there are outliers, highlight them.
    if outliers is not None:
        axis.plot(outliers, data_narray[outliers], OUTLIER_MARKER, label='Outliers')
    if unique is not None:
        pc_unique = float(len(unique)) / float(len(data_narray)) * 100.0
        axis.plot(unique, data_narray[unique], UNIQUE_MARKER,
                  label=('Unique outliers (${%.2f}\\%%$)' % pc_unique))
    if common is not None:
        pc_common = float(len(common)) / float(len(data_narray)) * 100.0
        axis.plot(common, data_narray[common], COMMON_MARKER,
                  label=('Common outliers (${%.2f}\\%%$)' % pc_common))

    # Draw a rolling mean (optionally).
    if mean:
        means = list()
        sigmas = (list(), list())
        for index, datum in enumerate(data):
            l_slice, r_slice = _clamp_window_size(index, len(data), window_size)
            window = data[l_slice:r_slice]
            means.append(numpy.mean(window))
            if sigma:
                five_sigma = 5 * numpy.std(window)
                sigmas[0].append(means[index] - five_sigma)
                sigmas[1].append(means[index] + five_sigma)
        axis.plot(data_narray, label='Mean')
        # Fill between 5-sigmas.
        if sigma:
            iterations = numpy.array(list(xrange(len(data))))
            axis.fill_between(iterations, sigmas[0], means, alpha=FILL_ALPHA,
                              facecolor=LINE_COLOUR, edgecolor=LINE_COLOUR)
            axis.fill_between(iterations, means, sigmas[1], alpha=FILL_ALPHA,
                              facecolor=LINE_COLOUR, edgecolor=LINE_COLOUR)

    # Re-style the chart.
    major_xticks = compute_grid_offsets(
        x_range[0], x_range[1], GRID_MAJOR_X_DIVS)
    minor_xticks = compute_grid_offsets(
        x_range[0],x_range[1], GRID_MINOR_X_DIVS)
    major_yticks = compute_grid_offsets(
        y_range[0], y_range[1], GRID_MAJOR_Y_DIVS)
    minor_yticks = compute_grid_offsets(
        y_range[0], y_range[1], GRID_MINOR_Y_DIVS)

    style_axis(axis, major_xticks, minor_xticks,
                          major_yticks, minor_yticks)

    # Set title, axis labels and legend.
    axis.set_title(title, fontsize=TITLE_FONT_SIZE)
    axis.set_xlabel("Iteration", fontsize=AXIS_FONTSIZE)
    axis.set_ylabel("Time(s)", fontsize=AXIS_FONTSIZE)
    axis.set_ylim(y_range)

    handles, _ = axis.get_legend_handles_labels()
    if sigma:
        fill_patch = matplotlib.patches.Patch(color=LINE_COLOUR,
                                              alpha=FILL_ALPHA,
                                              label='5$\sigma$')
        handles.append(fill_patch)

    # Avoid drawing the legend if we are only charting measurements.
    if mean or sigma or (outliers is not None) or (unique is not None) or \
       (common is not None):
        legend = axis.legend(ncol=3, fontsize='medium', handles=handles)
        legend.draw_frame(False)


def draw_page(is_interactive, key, executions, machine_name,
              window_size, xlimits, single_exec, outliers,
              unique, common, mean, sigma):
    """Plot a single benchmark (may have been executed on multiple machines).
    """
    print('Plotting benchmark: %s...' % key)

    if single_exec is not None:
        executions = [executions[single_exec]]

    n_execs = len(executions)

    n_rows = int(math.ceil(float(len(executions)) / MAX_SUBPLOTS_PER_ROW))
    n_cols = min(MAX_SUBPLOTS_PER_ROW, n_execs)

    if not is_interactive:
        print('On this page, %g plots will be arranged in %g rows and %g columns.' %
              (len(executions), n_rows, n_cols))

    # Find the min and max y values across all plots for this view.
    if xlimits is None:
        xlimits_start = 0
        xlimits_stop = len(executions[0])  # Assume all execs are the same length
    else:
        try:
            xlimits_start, xlimits_stop = [int(x) for x in xlimits.split(",")]
        except ValueError:
            print("invalid xlimits pair")
            sys.exit(1)
    y_min, y_max = float('inf'), float('-inf')
    for execution in executions:
        y_min = min(min(execution[xlimits_start:xlimits_stop]), y_min)
        y_max = max(max(execution[xlimits_start:xlimits_stop]), y_max)
    # Allow 2% pad either side
    rng = y_max - y_min
    adj = rng * 0.02
    y_min -= adj
    y_max += adj

    fig, axes = plt.subplots(n_rows, n_cols, squeeze=False)
    key_elems = key.split(':')
    if len(key_elems) != 3:
            fatal_error('Malformed Krun results file: bad benchmark name: %s' %
                        key)
    bench_display = BENCHMARKS.get(key_elems[0], key_elems[0].title())

    index, row, col = 0, 0, 0
    while index < n_execs:
        data = executions[index]
        outliers_exec = outliers[index] if outliers is not None else None
        unique_exec = unique[index] if unique is not None else None
        common_exec = common[index] if common is not None else None

        actual_index = index + 1
        if single_exec:
            actual_index = single_exec + 1

        title = '%s, %s, %s, Process execution #%d' % (
            bench_display, key_elems[1], machine_name.title(), actual_index)
        axis = axes[row, col]
        axis.ticklabel_format(useOffset=False)
        x_bounds = [xlimits_start, xlimits_stop]
        axis.set_xlim(x_bounds)
        draw_subplot(axis, data, title, x_bounds, [y_min, y_max], window_size,
                     outliers_exec, unique_exec, common_exec, mean, sigma)
        col += 1
        if col == MAX_SUBPLOTS_PER_ROW:
            col = 0
            row += 1
        index = row * MAX_SUBPLOTS_PER_ROW + col

    key_elems = key.split(':')
    if not len(key_elems) == 3:
        fatal_error('Malformed Krun results file: bad benchmark name: %s' % key)
    bench_display = BENCHMARKS.get(key_elems[0], key_elems[0].title())

    fig.subplots_adjust(**SUBPLOT_PARAMS)
    if is_interactive:
        mng = plt.get_current_fig_manager()
        mng.resize(*mng.window.maxsize())
        plt.show()
        plt.close()
        return None, None
    else:
        # Return the figure to be saved in a multipage PDF.
        # Caller MUST close plt.
        export_size = (EXPORT_SIZE_INCHES[0] * n_cols,
                       EXPORT_SIZE_INCHES[1] * n_rows)
        return fig, export_size


def set_pdf_metadata(pdf_document):
    """Set metadata fields inside a PDF document.
    """
    info_dict = pdf_document.infodict()
    info_dict['Title'] = 'Krun results'
    info_dict['Author'] = 'soft-dev.org'
    info_dict['Creator'] = 'http://github.com/softdevteam/warmup_experiment'
    info_dict['Subject'] = 'Benchmarking results'
    info_dict['Keywords']= ('benchmark experiment interpreter measurement ' +
                            'software virtual machine')
    info_dict['CreationDate'] = datetime.datetime.today()
    info_dict['ModDate'] = datetime.datetime.today()


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
        if not os.path.exists(filename):
            fatal_error('File %s does not exist.' % filename)
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
    description = (('Plot data from Krun results file(s).' +
                    '\nExample usage:\n\n$ python %s -f results1.json.bz2\n' +
                    '$ python %s -i -f results1.json.bz2 -f results2.json.bz2' +
                    ' --window 250 --mean --sigma --with-outliers\n' +
                    '$ python %s -b  binarytrees:Hotspot:default-java') %
                   (script, script, script))
    parser = argparse.ArgumentParser(description)
    parser.add_argument('--interactive', '-i',
                        action='store_true',
                        dest='interactive',
                        default=False,
                        help='Display graphs (rather than writing to a file)')
    parser.add_argument('--filename', '-f',
                        action='append',
                        dest='json_files',
                        default=[],
                        type=str,
                        help=('Krun results file. This switch can be used ' +
                              'repeatedly to chart data from a number of ' +
                              'results files.'))
    parser.add_argument('--outfile', '-o',
                        action='store',
                        dest='outfile',
                        default=PDF_FILENAME,
                        type=str,
                        help=('Name of the PDF file to write to.'))
    parser.add_argument('--window', '-w',
                        action='store',
                        dest='window_size',
                        default=200,
                        type=int,
                        help='Size of the sliding window used to draw percentiles.')
    parser.add_argument('--benchmark', '-b',
                        action='store',
                        dest='benchmark',
                        default=None,
                        type=str,
                        help=('Only draw charts for a specific benchmark/' +
                              'vm/variant triplet. ' +
                              'e.g. binarytrees:Hotspot:default-java'))
    parser.add_argument('--xlimits', '-x',
                        action='store',
                        dest='xlimits',
                        default=None,
                        type=str,
                        help=("Specify X-axis limits as a comma separated pair "
                              "'start,end'. Samples start from 0. e.g. "
                              "'-x 100,130' will show samples in the range "
                              "100 to 130."))
    parser.add_argument('--single-exec', '-e',
                        type=int,
                        help=("Emit a graph for a single process execution. "
                              "e.g. '-e 0' emits only the first."))
    parser.add_argument('--mean', '-m',
                        action='store_true',
                        dest='mean',
                        default=False,
                        help=('Draw a rolling mean.'))
    parser.add_argument('--sigma', '-s',
                        action='store_true',
                        dest='sigma',
                        default=False,
                        help=('Draw 5-sigma interval around the rolling mean.'))
    parser.add_argument('--with-outliers',
                        action='store_true',
                        dest='outliers',
                        default=False,
                        help=('Annotate outliers. Only use this if your Krun' +
                              ' results file contains outlier information.'))
    parser.add_argument('--with-unique-outliers',
                        action='store_true',
                        dest='unique_outliers',
                        default=False,
                        help=('Annotate outliers common to multiple ' +
                              'executions and those unique to single ' +
                              'executions differently.'))
    return parser


def fatal_error(msg):
    print('')
    print('FATAL Krun plot error:')
    print('\t'+ msg)
    sys.exit(1)


if __name__ == '__main__':
    parser = create_cli_parser()
    options = parser.parse_args()
    if options.interactive and (options.outfile != PDF_FILENAME):
        parser.print_help()
        sys.exit(1)
    plt.close()  # avoid extra blank window
    if options.interactive:
        plt.switch_backend('TkAgg')
    else:
        from matplotlib.backends.backend_pdf import PdfPages
        print 'Saving results to: %s' % options.outfile
    print (('Charting with sliding window size: %d, xlimits: %s, '
            'single_exec: %s, ') %
            (options.window_size, options.xlimits, options.single_exec))
    print ('Using matplotlib backend: %s' % matplotlib.get_backend())

    # smaller fonts for on-screen plots
    if options.interactive:
        TICK_FONTSIZE = 12
        TITLE_FONT_SIZE = 17
        AXIS_FONTSIZE = 14
        BASE_FONTSIZE = 13

    main(options.interactive,
         get_data_dictionaries(options.json_files),
         options.window_size,
         options.outfile,
         options.xlimits,
         options.single_exec,
         options.outliers,
         options.unique_outliers,
         mean=options.mean,
         sigma=options.sigma,
         benchmark=options.benchmark)
