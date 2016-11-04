__LATEX_PREAMBLE = lambda title: """
\documentclass[12pt]{article}
\usepackage{booktabs}
\\title{%s}
\\begin{document}
\maketitle
""" % title

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
    formatted_text = ''
    if as_integer:
        formatted_text = '$%d\\scriptstyle{\\pm%d}$' % (int(median), int(error))
    elif brief:  # Take up less space.
        formatted_text = '$%.2f\\scriptstyle{\\pm%.3f}$' % (median, error)
    else:
        formatted_text = '$%.5f\\scriptstyle{\\pm%.6f}$' % (median, error)
    return formatted_text


def preamble(title):
    return __LATEX_PREAMBLE(title)


def section(heading):
    return __LATEX_SECTION(heading)


def start_table(format_, headings):
    return __LATEX_START_TABLE(format_, headings)
