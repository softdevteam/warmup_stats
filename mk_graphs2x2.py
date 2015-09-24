#!/usr/bin/env python2.7
"""
usage:
mk_graphs2x2.py <mode> <config file1> <machine name1> <config file2>
  <machine name2> [<x_start> <y_start>]

where mode is one of {interactive, export}
"""

import sys
import json
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np

plt.style.use('ggplot')

plt.figure(tight_layout=True)

# Set font sizes
font = {
    'family': 'sans',
    'weight': 'regular',
    'size': '13',
}
matplotlib.rc('font', **font)
SUPTITLE_FONT_SIZE = 18
TITLE_FONT_SIZE = 17
AXIS_FONTSIZE = 14

ROLLING_AVG = 200
STDDEV_FACTOR = 3.290526731492 # a 99% confidence interval
LINES_PERCENT = 1

# Configures border and spacing of subplots.
# Here we just make it more space efficient for the paper
SUBPLOT_PARAMS = {
    'hspace': 0.35,
    'bottom': 0.07,
    'left': 0.05,
    'right': 0.98,
    'top': 0.93,
    'wspace': 0.11,
}

EXPORT_SIZE_INCHES = 20, 8


def usage():
    print(__doc__)
    sys.exit(1)


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def main(mode, data_dcts, mch_names, x_bounds):
    keys = sorted(data_dcts[0]["data"].keys())
    for key in keys:
        # Assume data in json files have the same keys
        bench, vm, variant = key.split(":")

        # Ignore warmup!
        executions1 = data_dcts[0]["data"][key]
        executions2 = data_dcts[1]["data"][key]

        draw_plot(mode, key, [executions1, executions2], mch_names, x_bounds)


def draw_runseq_subplot(axis, data, title):
    axis.plot(data)
    avg = np.convolve(
        data, np.ones((ROLLING_AVG,))/ROLLING_AVG)[ROLLING_AVG-1:-ROLLING_AVG]
    window = rolling_window(np.array(data), ROLLING_AVG)
    rolling_stddev = np.std(window, 1)
    pad = ROLLING_AVG / 2

    avg = np.mean(window, 1)

    upper_std_dev = avg + STDDEV_FACTOR * rolling_stddev
    upper_std_dev = np.insert(upper_std_dev, 0, [None] * pad)

    lower_std_dev = avg - STDDEV_FACTOR * rolling_stddev
    lower_std_dev = np.insert(lower_std_dev, 0, [None] * pad)

    # Must come after std_dev lines built
    avg = np.insert(avg, 0, [None] * pad)

    axis.plot(lower_std_dev)
    axis.plot(upper_std_dev)
    axis.plot(avg)

    #axis.plot(avg * (1 + LINES_PERCENT / 100.0))
    5#axis.plot(avg * (1 - LINES_PERCENT / 100.0))

    axis.set_title(title, fontsize=TITLE_FONT_SIZE)
    axis.set_xlabel("Iteration", fontsize=AXIS_FONTSIZE)
    axis.set_ylabel("Time(s)", fontsize=AXIS_FONTSIZE)


def draw_plot(mode, key, executions, mch_names, x_bounds):
    print("Drawing %s..." % key)

    assert len(executions) == 2
    assert len(executions[0]) == 2
    assert len(executions[1]) == 2
    n_execs = 2
    n_files = 2  # number of json files

    fig, axes = plt.subplots(n_execs, n_files, squeeze=False)

    row = 0
    col = 0
    for mch_name, mch_execs in zip(mch_names, executions):
        for idx in range(n_execs):
            data = mch_execs[idx]
            title = "%s, Execution #%d" % (mch_name.title(), idx)
            axis = axes[row, col]

            if x_bounds == [None, None]:
                x_bounds = [0, len(data) - 1]

            axis.set_xlim(x_bounds)
            draw_runseq_subplot(axis, data, title)
            col += 1
        row += 1
        col = 0

    fig.subplots_adjust(**SUBPLOT_PARAMS)
    fig.suptitle(key, fontsize=SUPTITLE_FONT_SIZE, fontweight="bold")
    if mode == "interactive":
        mng = plt.get_current_fig_manager()
        mng.resize(*mng.window.maxsize())
        plt.show()
    else:
        filename = "graph__2x2__%s__%s__%s.pdf" % (key.replace(":", "_"),
                                             x_bounds[0], x_bounds[1])
        fig.set_size_inches(*EXPORT_SIZE_INCHES)
        plt.savefig(filename=filename, format="pdf", dpi=300)
    plt.close()

if __name__ == "__main__":
    from krun.util import output_name
    try:
        mode = sys.argv[1]
    except IndexError:
        usage()

    if mode not in ["interactive", "export"]:
        usage()

    try:
        cfile1 = sys.argv[2]
        mch_name1 = sys.argv[3]
        cfile2 = sys.argv[4]
        mch_name2 = sys.argv[5]
    except IndexError:
        usage()

    try:
        x_start = int(sys.argv[6])
        x_end = int(sys.argv[7])
    except IndexError:  # optional
        x_start = None
        x_end = None
    except ValueError:
        usage()

    json_file1 = output_name(cfile1)
    json_file2 = output_name(cfile2)

    with open(json_file1, "r") as fh1:
        data_dct1 = json.load(fh1)
    with open(json_file2, "r") as fh2:
        data_dct2 = json.load(fh2)

    plt.close()  # avoid extra blank window
    main(mode, [data_dct1, data_dct2],
         [mch_name1, mch_name2], [x_start, x_end])
