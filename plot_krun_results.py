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
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy
import numpy.random
import os
import os.path
import seaborn

seaborn.set_palette("colorblind")
seaborn.set_style('whitegrid', {"lines.linewidth": 1.0, "axes.linewidth": 1.0})
seaborn.set_context("paper")

plt.figure(tight_layout=True)

PDF_FILENAME = 'krun_results.pdf'

SUPTITLE_FONT_SIZE = 18

# Configures border and spacing of subplots.
# Here we just make it more space efficient for the paper
SUBPLOT_PARAMS = {
    'hspace': 0.35,
    'bottom': 0.07,
    'left': 0.07,
    'right': 0.98,
    'top': 0.95,
    'wspace': 0.15,
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

MAX_SUBPLOTS_PER_ROW = 2
EXPORT_SIZE_INCHES = 10, 8  # Based on 1 chart per page.
DPI = 300


def main(is_interactive, data_dcts, percentiles, window_size,
         level, num_samples, outfile, benchmark=None):
    """Create a new dictionary in bmark->machine->data format.
    Plot all data.
    """
    if is_interactive:  # Display all benchmarks on the screen.
        for machine in data_dcts:
            keys = sorted(data_dcts[machine]['data'].keys())
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
                    draw_page(is_interactive, key, executions, machine,
                              percentiles, level, num_samples, window_size)
    else:  # Generate all charts and write to a single PDF.
        from matplotlib.backends.backend_pdf import PdfPages
        with PdfPages(outfile) as pdf:
            set_pdf_metadata(pdf)
            for machine in data_dcts:
                keys = sorted(data_dcts[machine]['data'].keys())
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
                        fig, suptitle, export_size = draw_page(is_interactive,
                                                               key,
                                                               executions,
                                                               machine,
                                                               percentiles,
                                                               level,
                                                               num_samples,
                                                               window_size)
                        fig.set_size_inches(*export_size)
                        pdf.savefig(fig,
                                    dpi=fig.dpi, orientation='landscape',
                                    bbox_inches='tight',
                                    bbox_extra_artists=[suptitle])
                        plt.close()
        print('Saved: %s' % outfile)


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


def bootstrap(data_array, n_resamples, alpha):
    """ Bootstrap resample an array_like
    """
    index = numpy.floor(numpy.random.rand(n_resamples)*len(data_array)).astype(int)
    bootstraps = data_array[index]
    return numpy.percentile(bootstraps, [alpha / 2.0, 100 - (alpha / 2.0)], axis=0)


def sliding_window_confidence(data, level, num_samples, window_size=200):
    """Data should be a 1xn matrix.
    """
    rolling_cis = ([], [])  # lower, upper CI
    alpha = 100.0 - level
    for index, datum in enumerate(data):
        l_slice, r_slice = _clamp_window_size(index, len(data), window_size)
        window = data[l_slice:r_slice]
        assert len(window) == r_slice - l_slice
        low, high = bootstrap(window, num_samples, alpha)
        rolling_cis[0].append(low)
        rolling_cis[1].append(high)
    return rolling_cis


def sliding_window_percentiles(data, percentiles, window_size=200):
    """Data should be a 1xn matrix.
    Returns a dictionary of:
        percentile : float -> percentile values : float list
    """
    pc_data = dict()
    percentile_set = set(percentiles)
    for percentile in percentile_set:
        pc_data[percentile] = list()
    for index, _ in enumerate(data):
        l_slice, r_slice = _clamp_window_size(index, len(data), window_size)
        window = data[l_slice:r_slice]
        assert len(window) == r_slice - l_slice
        for percentile in percentile_set:
            value = numpy.percentile(window, percentile)
            pc_data[percentile].append(value)
    return pc_data


def draw_subplot(axis, data, title, x_range, y_range, percentiles,
                 level, num_samples, window_size):
    data_narray = numpy.array(data)

    # Plot the original measurements.
    axis.plot(data_narray, label='Measurement', color=LINE_COLOUR)

    # Plot sliding window percentiles.
    pc_data = sliding_window_percentiles(data_narray, percentiles, window_size)
    for percentile in pc_data:
        label = r"$%d^\mathsf{th}$ percentile" % int(percentile)
        axis.plot(pc_data[percentile], label=label)

    # Plot sliding window confidence intervals.
    cis = sliding_window_confidence(data_narray, level, num_samples, window_size)
    iterations = numpy.array(list(xrange(len(data))))
    axis.fill_between(iterations, cis[0], data_narray, alpha=FILL_ALPHA,
                      facecolor=LINE_COLOUR, edgecolor=LINE_COLOUR)
    axis.fill_between(iterations, data_narray, cis[1], alpha=FILL_ALPHA,
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
    legend = axis.legend(ncol=3, fontsize='medium')
    legend.draw_frame(False)


def draw_page(is_interactive, key, executions, machine_name,
              percentiles, level, num_samples, window_size):
    """Plot a single benchmark (may have been executed on multiple machines).
    """
    print('Plotting benchmark: %s...' % key)

    if len(executions) > 2:
        n_cols = MAX_SUBPLOTS_PER_ROW
        n_rows = int(math.ceil(float(len(executions)) / MAX_SUBPLOTS_PER_ROW))
    else:
        n_cols, n_rows = len(executions), 1
    if not is_interactive:
        print('On this page, %g plots will be arranged in %g rows and %g columns.' %
              (len(executions), n_rows, n_cols))

    # find the min and max y values across all plots for this view.
    y_min, y_max = float('inf'), float('-inf')
    for execution in executions:
        y_min = min(min(execution), y_min)
        y_max = max(max(execution), y_max)

    # Allow 2% pad either side
    rng = y_max - y_min
    adj = rng * 0.02
    y_min -= adj
    y_max += adj

    fig, axes = plt.subplots(n_rows, n_cols, squeeze=False)

    index, row, col = 0, 0, 0
    while index < len(executions):
        data = executions[index]
        title = '%s, Execution #%d' % (machine_name.title(), index + 1)
        axis = axes[row, col]
        axis.ticklabel_format(useOffset=False)
        x_bounds = [0, len(data)]
        axis.set_xlim(x_bounds)
        draw_subplot(axis, data, title, x_bounds, [y_min, y_max],
                     percentiles, level, num_samples, window_size)
        col += 1
        if col == MAX_SUBPLOTS_PER_ROW:
            col = 0
            row += 1
        index = row * MAX_SUBPLOTS_PER_ROW + col

    key_elems = key.split(':')
    assert len(key_elems) == 3, \
            'Malformed Krun results file: bad benchmark name: %s' % key
    bench_display = BENCHMARKS.get(key_elems[0], key_elems[0].title())
    display_key = '%s, %s' % (bench_display, key_elems[1])

    fig.subplots_adjust(**SUBPLOT_PARAMS)
    suptitle = fig.suptitle(display_key, fontsize=SUPTITLE_FONT_SIZE, fontweight='bold')
    if is_interactive:
        mng = plt.get_current_fig_manager()
        mng.resize(*mng.window.maxsize())
        plt.show()
        plt.close()
        return None, None, None
    else:
        # Return the figure to be saved in a multipage PDF.
        # Caller MUST close plt.
        export_size = (EXPORT_SIZE_INCHES[0] * n_cols,
                       EXPORT_SIZE_INCHES[1] * n_rows)
        return fig, suptitle, export_size


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
    description = (('Plot data from Krun results file(s).' +
                    '\nExample usage:\n\n$ python %s -f results1.json.bz2\n' +
                    '$ python %s -i -f results1.json.bz2 -f results2.json.bz2' +
                    ' --window 250 -l 99 -s 100000 -p 99 -p 95 -p 90\n' +
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
    parser.add_argument('--percentiles', '-p',
                        action='append',
                        dest='percentiles',
                        default=[],
                        type=int,
                        help=('Percentiles to plot. This switch can be used ' +
                              'repeatedly to chart a number of sliding ' +
                              'window percentiles.'))
    parser.add_argument('--window', '-w',
                        action='store',
                        dest='window_size',
                        default=200,
                        type=int,
                        help='Size of the sliding window used to draw percentiles.')
    parser.add_argument('--level', '-l',
                        action='store',
                        dest='level',
                        default=99.0,
                        type=float,
                        help='Level of confidence.')
    parser.add_argument('--samples', '-s',
                        action='store',
                        dest='num_samples',
                        default=10000,
                        type=int,
                        help=('Number of bootstrap samples used to estimate ' +
                              'the rolling confidence interval.'))
    parser.add_argument('--benchmark', '-b',
                        action='store',
                        dest='benchmark',
                        default=None,
                        type=str,
                        help=('Only draw charts for a specific benchmark/' +
                              'vm/variant triplet. ' +
                              'e.g. binarytrees:Hotspot:default-java'))
    return parser


if __name__ == '__main__':
    import sys
    parser = create_cli_parser()
    options = parser.parse_args()
    if options.interactive and (options.outfile != PDF_FILENAME):
        parser.print_help()
        sys.exit(1)
    plt.close()  # avoid extra blank window
    if not options.interactive:
        print 'Saving results to: %s' % options.outfile
    print (('Charting with sliding window size: %d, confidence level: %d ' +
            'bootstrap samples: %d and percentiles: %s') %
            (options.window_size, options.level, options.num_samples,
             " ".join([str(pc) for pc in options.percentiles])))
    float_percentiles = [float(pc) for pc in options.percentiles]
    main(options.interactive,
         get_data_dictionaries(options.json_files),
         float_percentiles,
         options.window_size,
         options.level,
         options.num_samples,
         options.outfile,
         benchmark=options.benchmark)
