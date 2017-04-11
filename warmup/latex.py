import math
import numpy

_NUMBERS = {0:'zero', 1:'one', 2:'two', 3:'three', 4:'four', 5:'five',
            6:'six', 7:'seven', 8:'eight', 9:'nine'}

_SPARKLINE_WIDTH = '3'  # Unit: ex.

STYLE_SYMBOLS = {  # Requires \usepackage{amssymb} and \usepackage{sparklines}
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
\\end{array}$
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
\\spark 0.1 0.0
       0.9 0.6
       /%
\\end{sparkline}\\xspace}
\\DeclareRobustCommand{\\goodinconsistent}{%
\\setlength{\\sparklinethickness}{0.4pt}%
\\begin{sparkline}{1.5}
\\spark 0.1 0.4
       0.9 0.4
       /%
\\spark 0.1 0.2
       0.9 0.2
       /%
\\end{sparkline}\\xspace}
"""

DEFAULT_DOCOPTS = '10pt, a4paper'

__LATEX_PREAMBLE = lambda title, doc_opts=DEFAULT_DOCOPTS: """
\\documentclass[%s]{article}
\\usepackage{adjustbox}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{booktabs}
\\usepackage{calc}
\\usepackage[margin=1.0cm]{geometry}
\\usepackage{mathtools}
\\usepackage{multicol}
\\usepackage{multirow}
\\usepackage{pdflscape}
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
\\setlength\\sparkspikewidth{1pt}
\\definecolor{sparkbottomlinecolor}{gray}{0.8}
%% Older versions of sparklines do not expose bottomlinethickness
\\renewcommand{\\sparkbottomline}[1][1]{\\pgfsetlinewidth{0.2pt}%%
  \\color{sparkbottomlinecolor}%%
  \\pgfline{\\pgfxy(0,0)}{\\pgfxy(#1,0)}\\color{sparklinecolor}}

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


def _histogram(data):
    histogram, bin_edges = numpy.histogram(data, bins=10)
    total = math.fsum(histogram)
    size = float(len(histogram))
    normed = [value / total for value in histogram]
    # Lower bound of the index of the median.
    median_index = int(math.floor(len(data) / 2.0))
    cum_freq = 0  # Cumulative frequency.
    for index, bin_value in enumerate(histogram):
        cum_freq += bin_value
        if cum_freq >= median_index:
            median_bin_index = index
            break
    sparkline = ['\\renewcommand{\\sparklineheight}{2.75}',
                 '\\begin{sparkline}{%s}' % _SPARKLINE_WIDTH]
    for index, value in enumerate(normed):
        # sparkspike x-position y-position
        if index == median_bin_index:
            sparkline.append('\\definecolor{sparkspikecolor}{named}{red}')
            sparkline.append('\\sparkspike %.2f %.2f' % ((index + 1) / size, value))
            sparkline.append('\\definecolor{sparkspikecolor}{named}{black}')
        else:
            sparkline.append('\\sparkspike %.2f %.2f' % ((index + 1) / size, value))
    sparkline.append('\\sparkbottomline')
    sparkline.append('\\end{sparkline}')
    sparkline.append('\\renewcommand{\\sparklineheight}{1.75}')
    return '\n'.join(sparkline)


def format_median_error(median, error, data, one_dp=False, two_dp=False):
    if one_dp:
        median_s = '%.1f' % median
        error_s = '(%.1f, %.1f)' % (error[0], error[1])
    elif two_dp:
        median_s = '%.2f' % median
        error_s = '(%.3f, %.3f)' % (error[0], error[1])
    else:
        assert False
    return """$
\\begin{array}{r}
\\scriptstyle{%s} \\\\[-6pt]
\\scriptscriptstyle{%s}
\\end{array}
$
\\noindent\\parbox[p]{%s}{%s}
"""  % (median_s, error_s, _SPARKLINE_WIDTH + 'ex', _histogram(data))


def format_median_ci(median, error, data):
    median_s = '%.5f' % median
    error_s = '%.6f' % error
    return """$
\\begin{array}{r}
\\scriptstyle{%s} \\\\[-6pt]
\\scriptscriptstyle{\\pm%s}
\\end{array}
$
\\noindent\\parbox[p]{%s}{%s}
"""  % (median_s, error_s, _SPARKLINE_WIDTH + 'ex', _histogram(data))


def preamble(title, doc_opts=DEFAULT_DOCOPTS):
    return __LATEX_PREAMBLE(title, doc_opts)


def machine_name_to_macro(machine):
    for number in _NUMBERS:
        machine = machine.replace(str(number), _NUMBERS[number])
    return '\\' + machine


def section(heading):
    return __LATEX_SECTION(heading)


def start_table(format_, headings):
    return __LATEX_START_TABLE(format_, headings)
