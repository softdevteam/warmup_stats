STYLE_SYMBOLS = {  # Requires \usepackage{amssymb}
    'could not classify': '$\\bot$',
    'mostly could not classify': '\\bot{}^*',
    'flat': '\\flatc',
    'mostly flat': '\\flatc$^*$',
    'no steady state': '\\nosteadystate',
    'mostly no steady state': '\\nosteadystate$^*$',
    'slowdown': '\\slowdown',
    'mostly slowdown': '\\slowdown$^*$',
    'warmup': '\\warmup',
    'mostly warmup': '\\warmup$^*$',
    'inconsistent': '\\inconsistent',
}


def get_latex_symbol_map(prefix='\\textbf{Symbol key:} '):
    symbols = list()
    for key in sorted(STYLE_SYMBOLS):
        if key.startswith('mostly '):
            continue
        symbols.append('%s~%s' % (STYLE_SYMBOLS[key], key.lower()))
    text  = prefix + ', '.join(symbols)
    text += '.'  # Ignore the 'mostly' classifications for now.
    # text += '. Classifications which apply to more than half, but not all,'
    # text += '  process executions for a given benchmark are marked with $^*$.'
    return text


__MACROS = """
\\newcommand{\\flatc}{$\\rightarrow$}
\\newcommand{\\nosteadystate}{$\\rightsquigarrow$}
\\newcommand{\\warmup}{$\\uparrow$}
\\newcommand{\\slowdown}{$\\downarrow$}
\\newcommand{\\inconsistent}{$\\rightleftarrows$}
"""

__LATEX_PREAMBLE = lambda title: """
\documentclass[12pt,a4paper]{article}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
%s
\\title{%s}
\\begin{document}
\maketitle
""" % (__MACROS, title)

__LATEX_SECTION = lambda section: """
\\section*{%s}
""" % section

__LATEX_START_TABLE = lambda format_, headings: """
\\begin{tabular}{%s}
\\toprule
%s \\\\
\\midrule
""" % (format_, headings)

__LATEX_END_TABLE = """
\\bottomrule
\\end{tabular}
"""

__LATEX_END_DOCUMENT = """
\\end{document}
"""


def end_document():
    return __LATEX_END_DOCUMENT


def end_table():
    return __LATEX_END_TABLE


def escape(word):
    return word.replace('_', '\\_')



def format_median_error(median, error, as_integer=False, brief=False):
    if as_integer:
        median_s = '%d' % int(median)
        error_s = '%d' % int(error)
    elif brief:
        median_s = '%.2f' % median
        error_s = '%.3f' % error
    else:
        median_s = '%.5f' % median
        error_s = '%.6f' % error
    return """$
\\begin{array}{rr}
\\scriptstyle{%s} \\\\[-6pt]
\\scriptscriptstyle{\\pm%s}
\\end{array}
$"""  % (median_s, error_s)


def preamble(title):
    return __LATEX_PREAMBLE(title)


def section(heading):
    return __LATEX_SECTION(heading)


def start_table(format_, headings):
    return __LATEX_START_TABLE(format_, headings)
