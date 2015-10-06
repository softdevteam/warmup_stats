import matplotlib

# Display names that can't be formatted with .title()
BENCHMARKS = {
    "binarytrees":      "Binary Trees",
    "spectralnorm":     "Spectral Norm",
    "fannkuch_redux":   "Fannkuch Redux",
    "nbody":            "N-Body",
}

GRID_MINOR_X_DIVS = 20
GRID_MAJOR_X_DIVS = 10

GRID_MINOR_Y_DIVS = 12
GRID_MAJOR_Y_DIVS = 6

TICK_FONTSIZE = 12
SPINE_LINESTYLE = "solid"
SPINE_LINEWIDTH = 1
LINE_COLOUR = "#000000"
LINE_WIDTH = 1
TITLE_FONT_SIZE = 17
AXIS_FONTSIZE = 14
BASE_FONTSIZE = 13
FONT = {
    'family': 'sans',
    'weight': 'regular',
    'size': BASE_FONTSIZE,
}
matplotlib.rc('font', **FONT)


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

def draw_runseq_subplot(axis, data, title, x_range, y_range):
    d_len = len(data)
    d_min = min(data)
    d_max = max(data)

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

    axis.plot(data, color=LINE_COLOUR, linewidth=LINE_WIDTH)

    axis.set_title(title, fontsize=TITLE_FONT_SIZE)
    axis.set_xlabel("Iteration", fontsize=AXIS_FONTSIZE)
    axis.set_ylabel("Time(s)", fontsize=AXIS_FONTSIZE)
    axis.set_ylim(y_range)
