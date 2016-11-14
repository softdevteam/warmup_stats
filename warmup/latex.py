STYLE_SYMBOLS = {  # Requires \usepackage{amssymb}
    'could not classify': '$\\bot$',
    'flat': '\\flatc',
    'no steady state': '\\nosteadystate',
    'slowdown': '\\slowdown',
    'warmup': '\\warmup',
    'inconsistent': '\\inconsistent',
}


def get_latex_symbol_map(prefix='\\textbf{Symbol key:} '):
    symbols = list()
    for key in sorted(STYLE_SYMBOLS):
        if key.startswith('mostly '):
            continue
        symbols.append('%s~%s' % (STYLE_SYMBOLS[key], key.lower()))
    text  = prefix + ', '.join(symbols)
    text += '.'
    return text


__MACROS = """
\\newcommand{\\flatc}{$\\rightarrow$}
\\newcommand{\\nosteadystate}{$\\rightsquigarrow$}
\\newcommand{\\warmup}{$\\uparrow$}
\\newcommand{\\slowdown}{$\\downarrow$}
\\newcommand{\\inconsistent}{$\\rightleftarrows$}
"""

DEFAULT_DOCOPTS = '12pt, a4paper'

__LATEX_PREAMBLE = lambda title, doc_opts=DEFAULT_DOCOPTS: """
\documentclass[%s]{article}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{rotating}
\usepackage{calc}
%s
\\title{%s}
\\begin{document}
\maketitle
""" % (doc_opts, __MACROS, title)

__LATEX_SECTION = lambda section: """
\\section*{%s}
""" % section

__LATEX_START_TABLE = lambda format_, headings, before='': """
{
%s
\\begin{tabular}{%s}
\\toprule
%s \\\\
\\midrule
""" % (before, format_, headings)

__LATEX_END_TABLE = """
\\bottomrule
\\end{tabular}
}
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


def preamble(title, doc_opts=DEFAULT_DOCOPTS):
    return __LATEX_PREAMBLE(title, doc_opts)


def section(heading):
    return __LATEX_SECTION(heading)


def start_table(format_, headings, before=''):
    return __LATEX_START_TABLE(format_, headings, before=before)
