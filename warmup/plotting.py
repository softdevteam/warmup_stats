import math

from matplotlib import pyplot
from matplotlib.ticker import ScalarFormatter

SPINE_LINESTYLE = 'solid'
SPINE_LINEWIDTH = 1
ZORDER_GRID = 1


def axis_data_transform(axis, xin, yin, inverse=False):
    """Translate axis and data coordinates.
    If 'inverse' is True, data coordinates are translated to axis coordinates,
    otherwise the transformation is reversed.

    Code by Covich, from: http://stackoverflow.com/questions/29107800/
    """
    xlim = axis.get_xlim()
    ylim = axis.get_ylim()
    xdelta = xlim[1] - xlim[0]
    ydelta = ylim[1] - ylim[0]
    if not inverse:
        xout =  xlim[0] + xin * xdelta
        yout =  ylim[0] + yin * ydelta
    else:
        xdelta2 = xin - xlim[0]
        ydelta2 = yin - ylim[0]
        xout = xdelta2 / xdelta
        yout = ydelta2 / ydelta
    return xout, yout


def axis_to_figure_transform(fig, axis, coord):
    """Transform axis coordinates to figure coordinates.
    Code by Ben Schmidt http://stackoverflow.com/questions/41462693/
    """
    return fig.transFigure.inverted().transform(axis.transAxes.transform(coord))


def collide_rect((left, bottom, width, height), fig, axis, data):
    """Determine whether a rectangle (in axis coordinates) collides with
    any data (data coordinates, or seconds). We use the matplotlib transData
    API to convert between display and data coordinates.
    """
    # Find the values on the x-axis of left and right edges of the rect.
    x_left_float, _ = axis_data_transform(axis, left, 0, inverse=False)
    x_right_float, _ = axis_data_transform(axis, left + width, 0, inverse=False)
    x_left = int(math.floor(x_left_float))
    x_right = int(math.ceil(x_right_float))
    # Clamp x values.
    if x_left < 0:
        x_left = 0
    if x_right >= len(data):
        x_right = len(data) - 1
    # Next find the highest and lowest y-value in that segment of data.
    minimum_y = min(data[int(x_left):int(x_right)])
    maximum_y = max(data[int(x_left):int(x_right)])
    # Next convert the bottom and top of the rect to data coordinates (seconds).
    _, inset_top = axis_data_transform(axis, 0, bottom + height, inverse=False)
    _, inset_bottom = axis_data_transform(axis, 0, bottom, inverse=False)
    if ((bottom > 0.5 and maximum_y > inset_bottom) or  # inset at top of chart
           (bottom < 0.5 and minimum_y < inset_top)):   # inset at bottom
        return True
    return False


def add_inset_to_axis(fig, axis, rect):
    left, bottom, width, height = rect
    fig_left, fig_bottom = axis_to_figure_transform(fig, axis, (left, bottom))
    fig_width, fig_height = axis_to_figure_transform(fig, axis, [width, height]) \
                                   - axis_to_figure_transform(fig, axis, [0, 0])
    return fig.add_axes([fig_left, fig_bottom, fig_width, fig_height], frameon=True)


def format_yticks_scientific(axis):
    """Apply scientific formatting to y-axis of a given set of axes.
    Change from 'offset' notation (where a number is added / subtracted to each
    ticklabel) to the more intuitive scientific notation (where a number
    multiplies each ticklabel). Remove the multiplier from the top-left hand
    corner of the plot, and add it to the ticklabel instead.
    """
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_scientific(True)
    formatter.set_powerlimits((-2, 2))
    axis.yaxis.set_major_formatter(formatter)
    y_axis = axis.yaxis
    pyplot.draw()
    offset = y_axis.get_offset_text().get_text()
    if len(offset) > 0:
        labels = [label.get_text() + offset for label in axis.get_yticklabels()]
        axis.set_yticklabels(labels)
        y_axis.offsetText.set_visible(False)


def get_unified_yrange(executions, xlimits_start, xlimits_stop, padding=0.02):
    y_min, y_max = float('inf'), float('-inf')  # Wallclock data.
    for execution in executions:
        y_min = min(min(execution[xlimits_start:xlimits_stop]), y_min)
        y_max = max(max(execution[xlimits_start:xlimits_stop]), y_max)
    range_ = y_max - y_min
    adj = range_ * padding
    y_min -= adj
    y_max += adj
    return y_min, y_max


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


def style_axis(ax, major_xticks, minor_xticks, major_yticks, minor_yticks, tick_fontsize):
    ax.set_xticks(major_xticks)
    ax.set_xticks(minor_xticks, minor=True)
    ax.set_yticks(major_yticks)
    ax.set_yticks(minor_yticks, minor=True)

    x_ax = ax.get_xaxis()
    y_ax = ax.get_yaxis()

    x_ax.set_ticks_position('none')
    y_ax.set_ticks_position('none')
    x_ax.set_tick_params(labelsize=tick_fontsize, zorder=ZORDER_GRID)
    y_ax.set_tick_params(labelsize=tick_fontsize, zorder=ZORDER_GRID)

    # Grid should be drawn below all other splines.
    ax.grid(which='minor', alpha=0.4, zorder=ZORDER_GRID)
    ax.grid(which='major', alpha=0.8, zorder=ZORDER_GRID)

    for i in ['right', 'left', 'top', 'bottom']:
        ax.spines[i].set_visible(False)

    ax.frameon = False
