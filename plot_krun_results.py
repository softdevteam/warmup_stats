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

from matplotlib.ticker import FormatStrFormatter

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
    'top': 0.88,
    'wspace': 0.20,
}

# Display names that can't be formatted with .title()
BENCHMARKS = {
    'binarytrees':      'Binary Trees',
    'spectralnorm':     'Spectral Norm',
    'fannkuch_redux':   'Fannkuch Redux',
    'nbody':            'N-Body',
}

# Machine names that need to be reformatted.
MACHINES = {
    'bencher3': 'Linux1/i7-4790K',
    'bencher5': 'Linux2/i7-4790',
    'bencher6': 'OpenBSD/i7-4790',
    'bencher7': 'ARM',  # this machine has not been set up yet
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

OUTLIER_MARKER = 'o'
OUTLIER_COLOR = 'r'
OUTLIER_SIZE = 20
UNIQUE_COLOR = 'g'
UNIQUE_MARKER = 'o'
UNIQUE_SIZE = 20
COMMON_COLOR = 'r'
COMMON_MARKER = '*'
COMMON_SIZE = 40

# Inset placement (left, bottom, width, height) relative to subplot axis.
INSET_RECT = (0.65, 0.8, 0.3, 0.15)

YTICK_FORMAT = '%.4f'

# Default (PDF) font sizes
TICK_FONTSIZE = 18
TITLE_FONT_SIZE = 20
AXIS_FONTSIZE = 20
BASE_FONTSIZE = 20
LEGEND_FONTSIZE = 17

FONT = {
    'family': 'sans',
    'weight': 'regular',
    'size': BASE_FONTSIZE,
}
matplotlib.rc('font', **FONT)

MAX_SUBPLOTS_PER_ROW = 2
EXPORT_SIZE_INCHES = 10, 8  # Based on 1 chart per page.
DPI = 300


def main(is_interactive, data_dcts, plot_titles, window_size, outfile,
         xlimits, with_outliers, unique_outliers, mean=False, sigma=False,
         inset_xlimit=None, one_page=False):
    """Determine which plots to put on each page of output.
    Plot all data.
    """

    pdf = None  # PDF output (for non-interactive mode).

    if not is_interactive:
        pdf = PdfPages(outfile)
        set_pdf_metadata(pdf)

    # Run sequences, outliers and subplot titles for each page we need to plot.
    pages, all_subplot_titles = list(), list()
    all_outliers, all_common, all_unique = list(), list(), list()

    # By default, each benchmark from each machine is placed on a separate
    # page. If the --one-page switch has been passed in, then we place
    # all plots on a single page. In which case, we need to construct
    # a flat list of all run sequences.
    if one_page:
        page, subplot_titles = list(), list()
        page_common, page_unique, page_outlier = list(), list(), list()
        for key in sorted(data_dcts['data']):
            for machine in sorted(data_dcts['data'][key]):
                for index, run_seq in enumerate(data_dcts['data'][key][machine]):
                    page.append(run_seq)
                    subplot_titles.append(plot_titles[key][machine][index])
                    # Collect outliers, if the user wishes to annotate them on
                    # the plots. The draw_page() and draw_subplot() functions
                    # expect either lists of outliers or None (if outliers are
                    # not to be annotated).
                    if with_outliers:
                        page_outlier.append(data_dcts['all_outliers'][key][machine][index])
                    else:
                        page_outlier.append(None)
                    if unique_outliers:
                        page_common.append(data_dcts['common_outliers'][key][machine][index])
                        page_unique.append(data_dcts['unique_outliers'][key][machine][index])
                    else:
                        page_common.append(None)
                        page_unique.append(None)
        pages.append(page)
        all_subplot_titles.append(subplot_titles)
        all_outliers.append(page_outlier)
        all_common.append(page_common)
        all_unique.append(page_unique)
    else:  # Create multiple pages.
        for key in sorted(data_dcts['data']):
            for machine in sorted(data_dcts['data'][key]):
                pages.append(data_dcts['data'][key][machine])
                all_subplot_titles.append(plot_titles[key][machine])
                if with_outliers:
                    all_outliers.append(data_dcts['all_outliers'][key][machine])
                else:
                    all_outliers.append(None)
                if unique_outliers:
                    all_common.append(data_dcts['common_outliers'][key][machine])
                    all_unique.append(data_dcts['unique_outliers'][key][machine])
                else:
                    all_common.append(None)
                    all_unique.append(None)

    # Draw each page and display (interactive mode) or save to disk.
    for index, page in enumerate(pages):
        print 'Plotting page %g.' % (index + 1),
        fig, export_size = draw_page(is_interactive,
                                     page,
                                     all_subplot_titles[index],
                                     window_size,
                                     xlimits,
                                     all_outliers[index],
                                     all_unique[index],
                                     all_common[index],
                                     mean,
                                     sigma,
                                     inset_xlimit)
        if not is_interactive:
            fig.set_size_inches(*export_size)
            pdf.savefig(fig, dpi=fig.dpi, orientation='landscape',
                        bbox_inches='tight')
            plt.close()
    if not is_interactive:
        pdf.close()
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


def add_inset_to_axis(axis, rect):
    """Adds a new axis to an existing axis, located at rect.
    rect should be a 4-tuple of (left, bottom, width, height) all relative
    to the axis.
    """
    fig = axis.figure
    left, bottom, width, height = rect
    def transform(coord):
        return fig.transFigure.inverted().transform(
            axis.transAxes.transform(coord))
    fig_left, fig_bottom = transform((left, bottom))
    fig_width, fig_height = transform([width, height]) - transform([0, 0])
    return fig.add_axes([fig_left, fig_bottom, fig_width, fig_height])


def draw_subplot(axis, data, title, x_range, y_range, window_size, outliers,
                 unique, common, mean, sigma):
    data_narray = numpy.array(data)

    # Plot the original measurements.
    axis.plot(data_narray, label='Measurement', color=LINE_COLOUR)

    # If there are outliers, highlight them.
    if outliers is not None:
        axis.scatter(outliers, data_narray[outliers], color=OUTLIER_COLOR,
                     marker=OUTLIER_MARKER, s=OUTLIER_SIZE, label='Outliers')
    if unique is not None:
        pc_unique = float(len(unique)) / float(len(data_narray)) * 100.0
        axis.scatter(unique, data_narray[unique], c=UNIQUE_COLOR,
                     marker=UNIQUE_MARKER, s=UNIQUE_SIZE,
                     label=('Unique outliers (${%.2f}\\%%$)' % pc_unique))
    if common is not None:
        pc_common = float(len(common)) / float(len(data_narray)) * 100.0
        axis.scatter(common, data_narray[common], c=COMMON_COLOR,
                     marker=COMMON_MARKER, s=COMMON_SIZE,
                     label=('Common outliers (${%.2f}\\%%$)' % pc_common))

    # Draw a rolling mean (optionally).
    if mean or sigma:
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
        if mean:  # Plot the mean.
            axis.plot(means, label='Mean')
        if sigma:  # Fill between 5-sigmas.
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

    style_axis(axis, major_xticks, minor_xticks, major_yticks, minor_yticks)

    # Format y-ticks to 3 decimal places.
    axis.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter(YTICK_FORMAT))

    # Set title, axis labels and legend.
    axis.set_title(title, fontsize=TITLE_FONT_SIZE)
    axis.set_xlabel('In-process iteration', fontsize=AXIS_FONTSIZE)
    axis.set_ylabel('Time(s)', fontsize=AXIS_FONTSIZE)
    axis.set_ylim(y_range)

    handles, labels = axis.get_legend_handles_labels()
    return handles, labels


def draw_page(is_interactive, executions, titles, window_size, xlimits,
              outliers, unique, common, mean, sigma, inset_xlimit=100):
    """Plot a page of benchmarks.
    """

    n_execs = len(executions)
    n_rows = int(math.ceil(float(len(executions)) / MAX_SUBPLOTS_PER_ROW))
    n_cols = min(MAX_SUBPLOTS_PER_ROW, n_execs)

    print('On this page, %g plots will be arranged in %g rows and %g columns.'
          % (len(executions), n_rows, n_cols))

    # Find the min and max y values across all plots for this view.
    if xlimits is None:
        xlimits_start = 0
        xlimits_stop = len(executions[0])  # Assume all execs are the same length
    else:
        try:
            xlimits_start, xlimits_stop = [int(x) for x in xlimits.split(',')]
        except ValueError:
            fatal_error('Invalid xlimits pair: %s' % xlimits)
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

    index, row, col = 0, 0, 0
    while index < n_execs:
        data = executions[index]
        outliers_exec = outliers[index] if outliers is not None else None
        unique_exec = unique[index] if unique is not None else None
        common_exec = common[index] if common is not None else None
        # Get axis and draw plot.
        axis = axes[row, col]
        axis.ticklabel_format(useOffset=False)
        x_bounds = [xlimits_start, xlimits_stop]
        axis.set_xlim(x_bounds)
        handles, labels = draw_subplot(axis, data, titles[index], x_bounds,
                               [y_min, y_max], window_size, outliers_exec,
                               unique_exec, common_exec, mean, sigma)
        col += 1
        if col == MAX_SUBPLOTS_PER_ROW:
            col = 0
            row += 1
        index = row * MAX_SUBPLOTS_PER_ROW + col

    fig.subplots_adjust(**SUBPLOT_PARAMS)

    # Draw an inset, if required. This MUST be done after adjusting subplots,
    # so that we can calculate the correct bounding box for the inset.
    if inset_xlimit is not None:
        index, row, col = 0, 0, 0
        while index < n_execs:
            axis = axes[row, col]
            inset = add_inset_to_axis(axis, INSET_RECT)
            inset.set_ylim([y_min, y_max])  # Same scale as larger subplot.
            inset.grid(False)  # Too many lines and y-ticks looks very messy.
            inset.set_yticks([y_min, y_min + ((y_max - y_min) / 2.0), y_max])
            inset.yaxis.set_major_formatter(FormatStrFormatter(YTICK_FORMAT))
            inset.plot(range(*inset_xlimit),  # Plot subset of the data.
                       executions[index][inset_xlimit[0]:inset_xlimit[1]],
                       color=LINE_COLOUR)
            col += 1
            if col == MAX_SUBPLOTS_PER_ROW:
                col = 0
                row += 1
            index = row * MAX_SUBPLOTS_PER_ROW + col

    if sigma:  # Add sigma to legend.
        fill_patch = matplotlib.patches.Patch(color=LINE_COLOUR,
                                              alpha=FILL_ALPHA,
                                              label='5$\sigma$')
        handles.append(fill_patch)
        labels.append('5$\sigma$')

    outliers_plotted = False
    if isinstance(outliers, list):
        if not all([x == None for x in outliers]):
            outliers_plotted = True
    elif outliers is not None:
        outliers_plotted = True

    unique_plotted = False
    if isinstance(unique, list):
        if not all([x == None for x in unique]):
            unique_plotted = True
    elif unique is not None:
        unique_plotted = True

    if mean or sigma or outliers_plotted or unique_plotted:
        fig.legend(handles, labels, loc='upper center',
                   fontsize=LEGEND_FONTSIZE, ncol=10,)

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


def get_data_dictionaries(json_files, benchmarks=[], outliers=False,
                          unique_outliers=False):
    """Read a list of BZipped JSON files and return their contents as a
    dictionaries of key -> machine name -> results.

    This function returns ONLY the data that the user has requested on the
    command line. Therefore, we check carefully that all data can be found
    in the available Krun results files. Also, we pass back the title text
    for each subplot.
    """

    data_dictionary = {'data': dict(), # Measurement data to be plotted.
                       'all_outliers': dict(),
                       'common_outliers': dict(),
                       'unique_outliers': dict(),
                      }
    plot_titles = dict()  # All subplot titles.

    # Find out what data the user requested.
    # In bmark key -> machine  -> proces execs format.
    requested_data = dict()
    if benchmarks != []:
        for quintuplet in benchmarks:
            try:
                machine, bmark, vm, variant, pexec = quintuplet.split(':')
            except ValueError:
                fatal_error('Malformed benchmark: %s. The correct '
                            'format is: machine:benchmark:vm:variant:pexec '
                            'e.g. mc.example.com:fasta:PyPy:default-python:0')
            key = ':'.join([bmark, vm, variant])
            if key not in requested_data:
                requested_data[key] = dict()
            if machine not in requested_data[key]:
                requested_data[key][machine] = list()
            requested_data[key][machine].append(int(pexec))

    # Collect the requested data from Krun results files.
    for filename in json_files:
        if not os.path.exists(filename):
            fatal_error('File %s does not exist.' % filename)
        print('Loading: %s' % filename)

        # All benchmarking data from one Krun results file.
        data = read_krun_results_file(filename)

        # Get machine name from Krun results file.
        machine = data['audit']['uname'].split(' ')[1]
        if '.' in machine:  # Strip domain names.
            machine = machine.split('.')[0]
        if machine in MACHINES:
            machine_name = MACHINES[machine]
        else:
            machine_name = machine

        # Collect any results requested from this file.
        if benchmarks == []:  # Chart all available data from this file.
            for key in data['data']:
                if len(data['data'][key]) == 0:
                    print('WARNING: Skipping: %s from %s (no executions)' %
                          (key, machine))
                elif len(data['data'][key][0]) == 0:
                    print('WARNING: Skipping: %s from %s (benchmark crashed)' %
                          (key, machine))
                else:
                    if key not in data_dictionary['data']:
                        data_dictionary['data'][key] = dict()
                    data_dictionary['data'][key][machine] = data['data'][key]
            # Construct plot titles for all data in this file.
            for key in data_dictionary['data']:
                if key not in plot_titles:
                    plot_titles[key] = dict()
                if machine not in plot_titles[key]:
                    plot_titles[key][machine] = list()
                benchmark_name = key.split(':')[0]
                if benchmark_name in BENCHMARKS:
                    benchmark_name = BENCHMARKS[benchmark_name]
                else:
                    benchmark_name = benchmark_name.title()

                # Add one title for each process execution
                try:
                    num_p_execs = len(data_dictionary['data'][key][machine])
                except KeyError:
                    pass  # no data for this
                else:
                    for p_exec in xrange(num_p_execs):
                        title = '%s, %s, %s, Process execution #%d' % \
                                (benchmark_name,
                                 key.split(':')[1],
                                 machine_name,
                                 p_exec + 1)
                        plot_titles[key][machine].append(title)
        else:  # Chart only the data specified on command line.
            for key in requested_data:
                if machine not in requested_data[key]:
                    continue
                if key not in data['data']:
                    # Hope the key appears in another file, checked below.
                    continue
                if key not in data_dictionary['data']:
                    data_dictionary['data'][key] = dict()
                if machine not in data_dictionary['data'][key]:
                    data_dictionary['data'][key][machine] = list()
                if key not in plot_titles:
                    plot_titles[key] = dict()
                if machine not in plot_titles[key]:
                    plot_titles[key][machine] = list()
                if len(data['data'][key]) == 0:
                    print('WARNING: Skipping: %s from %s (no executions)' %
                          (key, machine))
                elif len(data['data'][key][0]) == 0:
                    print('WARNING: Skipping: %s from %s (benchmark '
                          'crashed)' % (key, machine))
                else:
                    benchmark_name = key.split(':')[0]
                    if benchmark_name in BENCHMARKS:
                        benchmark_name = BENCHMARKS[benchmark_name]
                    else:
                        benchmark_name = benchmark_name.title()
                    for p_exec in requested_data[key][machine]:
                        if p_exec >= len(data['data'][key][p_exec]):
                            fatal_error('You requested that process '
                                        'execution %g for benchmark %s '
                                        'from machine %s be plotted, but '
                                        'the Krun results file for that '
                                        'machine only has %g process '
                                        'executions for the benchmark.' %
                                        (p_exec,
                                         key,
                                         machine,
                                         len(data['data'][key][p_exec])))
                        # Add run sequence to data dictionary.
                        print 'Adding run sequence to ', key, machine
                        data_dictionary['data'][key][machine].append(data['data'][key][p_exec])
                        # Construct plot title.
                        title = '%s, %s, %s, Process execution #%d' % \
                                (benchmark_name,
                                 key.split(':')[1],
                                 machine_name,
                                 p_exec + 1)
                        plot_titles[key][machine].append(title)

        # Collect outliers, if requested.
        if unique_outliers or outliers:
            if not ('common_outliers' in data and
                    'unique_outliers' in data and
                    'all_outliers' in data):
                fatal_error('You requested that outliers be annotated '
                            'on your plots, but file %s does not'
                            'contain the relevant keys. Please run the '
                            'mark_outliers_in_json.py script before '
                            'proceeding.' % filename)
            for key in data_dictionary['data']:
                if key not in data_dictionary['all_outliers']:
                    data_dictionary['all_outliers'][key] = dict()
                    data_dictionary['common_outliers'][key] = dict()
                    data_dictionary['unique_outliers'][key] = dict()
                for p_exec in xrange(len(data_dictionary['data'][key])):
                    data_dictionary['all_outliers'][key][machine] = data['all_outliers'][key]
                    data_dictionary['common_outliers'][key][machine] = data['common_outliers'][key]
                    data_dictionary['unique_outliers'][key][machine] = data['unique_outliers'][key]

    # Check that every benchmark that was requested has been found in the
    # given Krun results files.
    for key in requested_data:
        for machine in requested_data[key]:
            if (key not in data_dictionary['data'] or
                machine not in data_dictionary['data'][key]):
                fatal_error('You requested that plots for benchmark %s from '
                            'machine %s be produced, but no such data was '
                            'found in the Krun results files.' %
                            (key, machine))

    return data_dictionary, plot_titles


def create_cli_parser():
    """Create a parser to deal with command line switches.
    """
    script = os.path.basename(__file__)
    description = (('Plot data from Krun results file(s).'
                    '\nExample usage:\n\n$ python %s -f results1.json.bz2\n'
                    '$ python %s -i -f results1.json.bz2 -f results2.json.bz2'
                    ' --window 250 --mean --sigma --with-outliers\n'
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
                        help='Krun results file. This switch can be used '
                             'repeatedly to chart data from a number of '
                             'results files.')
    parser.add_argument('--outfile', '-o',
                        action='store',
                        dest='outfile',
                        default=PDF_FILENAME,
                        type=str,
                        help='Name of the PDF file to write to.')
    parser.add_argument('--benchmark', '-b',
                        action='append',
                        dest='benchmarks',
                        default=[],
                        type=str,
                        help='Only draw charts for specific '
                             'machine:benchmark:vm:variant:pexec quintuplet(s). '
                             'e.g. "-b mc1.example.com:binarytrees:Hotspot:default-java:0. '
                             'will chart the first process execution of the '
                             'binary trees benchmark, in Java, on the Hotspot '
                             'VM, as measured on machine mc1. '
                             'This switch can be used repeatedly to chart '
                             'a number of benchmarks.')
    parser.add_argument('--one-page',
                        action='store_true',
                        dest='one_page',
                        default=False,
                        help='Place all charts on a single page')
    parser.add_argument('--window', '-w',
                        action='store',
                        dest='window_size',
                        default=200,
                        type=int,
                        help='Size of the sliding window used to draw a '
                             'rolling mean and/or 5-sigma.')
    parser.add_argument('--mean', '-m',
                        action='store_true',
                        dest='mean',
                        default=False,
                        help='Draw a rolling mean.')
    parser.add_argument('--sigma', '-s',
                        action='store_true',
                        dest='sigma',
                        default=False,
                        help='Draw 5-sigma interval around the rolling mean.')
    parser.add_argument('--xlimits', '-x',
                        action='store',
                        dest='xlimits',
                        default=None,
                        type=str,
                        help="Specify X-axis limits as a comma separated pair "
                             "'start,end'. Samples start from 0. e.g. "
                             "'-x 100,130' will show samples in the range "
                             "100 to 130.")
    parser.add_argument('--inset-xlimits',
                        action='store',
                        dest='inset_xlimits',
                        default=None,
                        type=str,
                        metavar='LIMIT',
                        help='Place a small chart plotting a small number of '
                             'values in an inset inside each plot. This is '
                             'intended to make it easier to see detail during '
                             'the warm-up phase of each benchmark. LIMIT '
                             'should be a 2-tuple, e.g. 0,100 would show '
                             'the fist 100 iterations in the inset.')
    parser.add_argument('--with-outliers',
                        action='store_true',
                        dest='outliers',
                        default=False,
                        help='Annotate outliers. Only use this if your '
                             'Krun results file contains outlier information.')
    parser.add_argument('--with-unique-outliers',
                        action='store_true',
                        dest='unique_outliers',
                        default=False,
                        help='Annotate outliers common to multiple '
                             'executions and those unique to single '
                             'executions differently. Only use this if '
                             'your Krun results file contains outlier '
                             'information.')
    return parser


def fatal_error(msg):
    print('')
    print('FATAL Krun plot error:')
    print('\t'+ msg)
    sys.exit(1)


if __name__ == '__main__':
    parser = create_cli_parser()
    options = parser.parse_args()
    if options.outliers and options.unique_outliers:
        fatal_error('Cannot use --with-outliers and --with-unique-outliers '
                    'together.')
    if options.interactive and (options.outfile != PDF_FILENAME):
        parser.print_help()
        sys.exit(1)
    plt.close()  # avoid extra blank window
    if options.interactive:
        plt.switch_backend('TkAgg')
    else:
        from matplotlib.backends.backend_pdf import PdfPages
        print 'Saving results to: %s' % options.outfile
    print (('Charting with sliding window size: %d, xlimits: %s') %
           (options.window_size, options.xlimits))
    print ('Using matplotlib backend: %s' % matplotlib.get_backend())

    # Smaller fonts for on-screen plots.
    if options.interactive:
        TICK_FONTSIZE = 12
        TITLE_FONT_SIZE = 17
        AXIS_FONTSIZE = 14
        BASE_FONTSIZE = 13

    data, plot_titles = get_data_dictionaries(options.json_files,
                                              options.benchmarks,
                                              options.outliers,
                                              options.unique_outliers)

    inset_xlimits = None
    if options.inset_xlimits is not None:
        inset_xlimits = (int(options.inset_xlimits.split(',')[0]),
                         int(options.inset_xlimits.split(',')[1]))

    main(options.interactive,
         data,
         plot_titles,
         options.window_size,
         options.outfile,
         options.xlimits,
         options.outliers,
         options.unique_outliers,
         mean=options.mean,
         sigma=options.sigma,
         inset_xlimit=inset_xlimits,
         one_page=options.one_page)
