#!/usr/bin/env python2.7
"""
usage:
mk_graphs.py <mode> <config file> <machine name> [<x_start> <y_start>]

where mode is one of {interactive, export}
"""

import sys
import json
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import util_graph

plt.figure(tight_layout=True)

# Configures border and spacing of subplots.
# Here we just make it more space efficient for the paper
SUBPLOT_PARAMS = {
    'hspace': 0.35,
    'bottom': 0.1,
    'left': 0.12,
    'right': 0.95,
    'top': 0.93,
    'wspace': 0.11,
}

EXPORT_SIZE_INCHES = 10, 6


def usage():
    print(__doc__)
    sys.exit(1)


def main(mode, data_dct, mch_name, x_bounds):
    keys = sorted(data_dct["data"].keys())
    for key in keys:
        # Assume data in json files have the same keys
        bench, vm, variant = key.split(":")

        # Ignore warmup!
        executions = data_dct["data"][key]

        draw_plots(mode, key, executions, mch_name, x_bounds)


def draw_plots(mode, key, executions, mch_name, x_bounds):
    print("Drawing %s..." % key)

    key_elems = key.split(":")
    assert len(key_elems) == 3
    bench_display = util_graph.BENCHMARKS.get(
        key_elems[0], key_elems[0].title())
    display_key = "%s, %s" % (bench_display, key_elems[1])

    for idx in xrange(len(executions)):
        fig, axes = plt.subplots(1, 1, squeeze=False)

        data = executions[idx]
        title = "%s, %s, Execution #%d" % (display_key, mch_name.title(), idx)
        axis = axes[0, 0]
        axis.ticklabel_format(useOffset=False)

        if x_bounds == [None, None]:
            x_bounds = [0, len(data)]

        y_min, y_max = min(data), max(data)

        # Allow 2% pad either side
        rng = y_max - y_min
        adj = rng * 0.02
        y_min -= adj
        y_max += adj

        axis.set_xlim(x_bounds)
        util_graph.draw_runseq_subplot(axis, data, title, x_bounds,
                                       [y_min, y_max])
        fig.subplots_adjust(**SUBPLOT_PARAMS)

        if mode == "interactive":
            mng = plt.get_current_fig_manager()
            mng.resize(*mng.window.maxsize())
            plt.show()
        else:
            filename = "graph__%s__1x1__%s__exec%03d__%s__%s.pdf" % \
                (mch_name, key.replace(":", "_"),
                 idx, x_bounds[0], x_bounds[1])
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
        cfile = sys.argv[2]
        mch_name = sys.argv[3]
    except IndexError:
        usage()

    try:
        x_start = int(sys.argv[4])
        x_end = int(sys.argv[5])
    except IndexError:  # optional
        x_start = None
        x_end = None
    except ValueError:
        usage()

    json_file = output_name(cfile)

    with open(json_file, "r") as fh:
        data_dct = json.load(fh)

    plt.close()  # avoid extra blank window
    main(mode, data_dct, mch_name, [x_start, x_end])
