import math
import numpy
import textwrap

from matplotlib import pyplot
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter

ZOOM_PERCENTILE_MIN = 10.0
ZOOM_PERCENTILE_MAX = 90.0

ZORDER_GRID = 1

DARK_GRAY = '.15'
LIGHT_GRAY = '.8'
BASE_FONTSIZE = 8

MAX_INSTR_YLABEL_CHARS = 12

STYLE_DICT = {
    'figure.facecolor': 'white',
    'text.color': DARK_GRAY,
    'axes.labelcolor': DARK_GRAY,
    'legend.frameon': False,
    'legend.numpoints': 1,
    'legend.scatterpoints': 1,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'xtick.color': DARK_GRAY,
    'ytick.color': DARK_GRAY,
    'axes.axisbelow': True,
    'font.family': 'sans',
    'font.weight': 'regular',
    'font.size': BASE_FONTSIZE,
    'grid.linestyle': '-',
    'lines.solid_capstyle': 'round',
    'axes.facecolor': 'white',
    'axes.edgecolor': LIGHT_GRAY,
    'axes.linewidth': 1,
    'grid.color': LIGHT_GRAY,
    'lines.linewidth': 1.0,
    'axes.linewidth': 1.0,
    # Ensure type 3 fonts are not used
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
}


def wrap_ylabel(text, width=MAX_INSTR_YLABEL_CHARS):
    return textwrap.TextWrapper(width=width).fill(text.replace('_', '\n'))


def zoom_y_min(data, outliers, start_from=0):
    array = numpy.array(data)
    numpy.delete(array, outliers)
    numpy.delete(array, range(0, start_from))
    return numpy.percentile(array, ZOOM_PERCENTILE_MIN)


def zoom_y_max(data, outliers, start_from=0):
    array = numpy.array(data)
    numpy.delete(array, outliers)
    numpy.delete(array, range(0, start_from))
    return numpy.percentile(array, ZOOM_PERCENTILE_MAX)


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


def collide_rect((left, bottom, width, height), fig, axis, data, x_bounds):
    """Determine whether a rectangle (in axis coordinates) collides with
    any data (data coordinates, or seconds). We use the matplotlib transData
    API to convert between display and data coordinates.
    """
    # Find the values on the x-axis of left and right edges of the rect.
    x_left_float, _ = axis_data_transform(axis, left, 0, inverse=False)
    x_right_float, _ = axis_data_transform(axis, left + width, 0, inverse=False)
    x_left = int(math.floor(x_left_float)) - x_bounds[0]
    x_right = int(math.ceil(x_right_float)) - x_bounds[0]
    # Next find the highest and lowest y-value in that segment of data.
    minimum_y = min(data[x_left:x_right])
    maximum_y = max(data[x_left:x_right])
    # Next convert the bottom and top of the rect to data coordinates (seconds).
    _, inset_top = axis_data_transform(axis, 0, bottom + height, inverse=False)
    _, inset_bottom = axis_data_transform(axis, 0, bottom, inverse=False)
    for datum in data[x_left:x_right]:
        if ((datum >= inset_bottom and datum <= inset_top) or  # Inside rect.
            (bottom > 0.5 and datum >= inset_top) or           # Above rect.
            (bottom < 0.5 and datum <= inset_bottom)):         # Below rect.
            return True, -1.0
    if bottom > 0.5:  # Inset at top of chart.
        dist = math.fabs(inset_bottom - maximum_y)
    elif bottom < 0.5:  # Inset at bottom.
        dist = math.fabs(inset_top - minimum_y)
    return False, dist


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
    y_min, y_max= axis.get_ylim()
    if y_max > 100000 or (y_min < 0.00001 and y_min > 0.0):
        formatter = ScalarFormatter(useMathText=True, useOffset=False)
        formatter.set_scientific(True)
        formatter.set_powerlimits((-6, 6))
        axis.yaxis.set_major_formatter(formatter)
    else:
        formatter = FormatStrFormatter('%.5f')
        axis.yaxis.set_major_formatter(formatter)
    pyplot.draw()
    offset = axis.yaxis.get_offset_text().get_text()
    if len(offset) > 0:
        labels = [label.get_text() + offset for label in axis.get_yticklabels()]
        axis.set_yticklabels(labels)
        axis.yaxis.offsetText.set_visible(False)


def get_unified_yrange(executions, xlimits_start, xlimits_stop, padding=0.02):
    y_min, y_max = float('inf'), float('-inf')  # Wallclock data.
    for execution in executions:
        y_min = min(min(execution[xlimits_start:xlimits_stop]), y_min)
        y_max = max(max(execution[xlimits_start:xlimits_stop]), y_max)
    range_ = y_max - y_min
    adj = range_ * padding
    y_min -= adj
    if y_min < 0:
        y_min = 0
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


def compute_grid_offsets(d_min, d_max, num, with_max=False):
    if with_max:  # x-ticks for wallclock times, must include max value.
        rng = float(d_max) - d_min
        freq =  rng / num
        return [d_min + i * round(freq) for i in xrange(num)] + [d_max - 1]
    else:
        rng = float(d_max) - d_min
        freq =  rng / num
        return [d_min + i * freq for i in xrange(num + 1)]


def style_axis(axis, major_xticks, minor_xticks, major_yticks, minor_yticks, tick_fontsize):
    axis.set_xticks(major_xticks)
    axis.set_xticks(minor_xticks, minor=True)
    axis.set_yticks(major_yticks)
    axis.set_yticks(minor_yticks, minor=True)
    # Style ticks.
    x_axis = axis.get_xaxis()
    y_axis = axis.get_yaxis()
    x_axis.set_ticks_position('none')
    y_axis.set_ticks_position('none')
    x_axis.set_tick_params(labelsize=tick_fontsize, zorder=ZORDER_GRID)
    y_axis.set_tick_params(labelsize=tick_fontsize, zorder=ZORDER_GRID)
    # Grid should be drawn below all other splines.
    axis.grid(which='minor', alpha=0.4, zorder=ZORDER_GRID)
    axis.grid(which='major', alpha=0.8, zorder=ZORDER_GRID)
    # Remove hard outer frame.
    for i in ['right', 'left', 'top', 'bottom']:
        axis.spines[i].set_visible(False)
    axis.frameon = False
