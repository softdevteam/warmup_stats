STYLE_SYMBOLS = {  # Requires \usepackage{amssymb} and \usepackage{sparklines}
    'could not classify': '$\\bot$',
    'flat': '\\flatc',
    'no steady state': '\\nosteadystate',
    'slowdown': '\\slowdown',
    'warmup': '\\warmup',
    'good inconsistent': '\\goodinconsistent',
    'bad inconsistent': '\\badinconsistent',
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
%
% blankheight.
%
\\newlength{\\blankheight}
\\settototalheight{\\blankheight}{
$\\begin{array}{rr}
\\scriptstyle{0.16} \\\\[-6pt]
\\scriptscriptstyle{\\pm0.000}
\end{array}$
}


%
% Benchmark names.
%
\\newcommand{\\binarytrees}{\\emph{binary trees}\\xspace}
\\newcommand{\\richards}{\\emph{Richards}\\xspace}
\\newcommand{\\spectralnorm}{\\emph{spectralnorm}\\xspace}
\\newcommand{\\nbody}{\\emph{n-body}\\xspace}
\\newcommand{\\fasta}{\\emph{fasta}\\xspace}
\\newcommand{\\fannkuch}{\\emph{fannkuch redux}\\xspace}
\\newcommand{\\bencherthree}{Linux$_\\mathrm{4790K}$\\xspace}
\\newcommand{\\bencherfive}{Linux$_\\mathrm{4790}$\\xspace}
\\newcommand{\\benchersix}{OpenBSD$_\\mathrm{4790}$\\xspace}
\\newcommand{\\bencherseven}{Linux$_\\mathrm{E3-1240v5}$\\xspace}


%
% Sparklines.
%
\\DeclareRobustCommand{\\flatc}{%
\\setlength{\\sparklinethickness}{0.4pt}%
\\begin{sparkline}{1.5}
\\spark 0.0 0.35
       1.0 0.35
       /%
\\end{sparkline}\\xspace}
\\DeclareRobustCommand{\\nosteadystate}{%
\\setlength{\\sparklinethickness}{0.4pt}%
\\begin{sparkline}{1.5}
\\spark 0.0 0.35
       0.1 0.5
       0.3 0.2
       0.5 0.5
       0.7 0.2
       0.9 0.5
       1.0 0.35
       /%
\\end{sparkline}\\xspace}
\\DeclareRobustCommand{\\warmup}{%
\\setlength{\\sparklinethickness}{0.4pt}%
\\begin{sparkline}{1.5}
\\spark 0.0 0.8
       0.5 0.8
       0.5 0.0
       1.0 0.0
       /%
\\end{sparkline}\\xspace}
\\DeclareRobustCommand{\\slowdown}{%
\\setlength{\\sparklinethickness}{0.4pt}%
\\begin{sparkline}{1.5}
\\spark 0.0 0.0
       0.5 0.0
       0.5 0.8
       1.0 0.8
       /%
\\end{sparkline}\\xspace}
\\DeclareRobustCommand{\\badinconsistent}{%
\\setlength{\\sparklinethickness}{0.4pt}%
\\begin{sparkline}{1.5}
\\spark 0.1 0.4
       0.9 0.4
       /%
\\spark 0.1 0.2
       0.9 0.2
       /%
\\spark 0.1 0.6
       0.9 0.0
       /%
\\end{sparkline}\\xspace}
\\DeclareRobustCommand{\\goodinconsistent}{%
\\setlength{\\sparklinethickness}{0.4pt}%
\\begin{sparkline}{1.5}
\\spark 0.0 0.8
       0.5 0.8
       0.5 0.0
       1.0 0.0
       /%
\\spark 0.0 0.4
       1.0 0.4
       /%
\\end{sparkline}\\xspace}
"""

DEFAULT_DOCOPTS = '10pt, a4paper'

__LATEX_PREAMBLE = lambda title, doc_opts=DEFAULT_DOCOPTS: """
\\documentclass[%s]{article}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{booktabs}
\\usepackage{calc}
\\usepackage[margin=1.0cm]{geometry}
\\usepackage{mathtools}
\\usepackage{multicol}
\\usepackage{multirow}
\\usepackage{rotating}
\\usepackage{sparklines}
\\usepackage{xspace}


%s
\\title{%s}
\\begin{document}
\\maketitle
\\thispagestyle{empty}
\\pagestyle{empty}
""" % (doc_opts, __MACROS, title)

__LATEX_SECTION = lambda section: """
\\section*{%s}
""" % section

__LATEX_START_TABLE = lambda format_, headings: """
{
\\begin{tabular}{%s}
\\toprule
%s \\\\
\\midrule
""" % (format_, headings)

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
