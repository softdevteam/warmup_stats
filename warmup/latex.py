__LATEX_PREAMBLE = lambda title: """
\documentclass[12pt]{article}
\usepackage{longtable}
\usepackage{booktabs}
\\title{%s}
\\begin{document}
\maketitle
""" % title

__LATEX_SECTION = lambda section: """
\\section*{%s}
""" % section

__LATEX_START_TABLE = lambda format_, headings: """
\\begin{center}
\\begin{longtable}{%s}
\\toprule
%s\\\\
\midrule
\endfirsthead
\\toprule
%s\\\\
\midrule
\endhead
\midrule
\endfoot
\\bottomrule
\endlastfoot
""" % (format_, headings, headings)

__LATEX_END_TABLE = """
\end{longtable}
\end{center}
"""

__LATEX_END_DOCUMENT = """
\end{document}
"""


def end_document():
    return __LATEX_END_DOCUMENT


def end_table():
    return __LATEX_END_TABLE


def escape(word):
    return word.replace('_', '\\_')

def preamble(title):
    return __LATEX_PREAMBLE(title)


def section(heading):
    return __LATEX_SECTION(heading)


def start_table(format_, headings):
    return __LATEX_START_TABLE(format_, headings)
