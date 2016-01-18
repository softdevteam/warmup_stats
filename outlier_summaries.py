#!/usr/bin/env python2.7
"""
usage: outlier_summaries.py [-h] --filename JSON_FILES
                            [--latexfile LATEX_FILE]

Summarise outlier information stored within a Krun results file.

Example usage:

    $ python outlier_summaries.py -f bencher_results.json.bz2
    $ python outlier_summaries.py -f results.json.bz2
 -l summary.tex

optional arguments:
  -h, --help            show this help message and exit
  --filename JSON_FILES, -f JSON_FILES
                        Krun results file. This switch can be used repeatedly to chart data from a number of results files.
  --latexfile LATEX_FILE, -l LATEX_FILE
                        Name of the LaTeX file to write to.
"""

import argparse
import bz2
import json
import os
import os.path


LATEX_FILENAME = 'outlier_summary_tables.tex'

__LATEX_HEADER = lambda window_size: """
\documentclass[12pt]{article}
\usepackage{longtable}
\usepackage{booktabs}
\\title{Summaries of outlier counts. Window size: %s}
\\begin{document}
\maketitle
""" % window_size

__LATEX_START_TABLE = lambda col_title: """
\\begin{center}
\\begin{longtable}{l|r}
\\toprule
%s & Number of outliers \\\\
\midrule
\endfirsthead
\\toprule
%s & Number of outliers \\\\
\midrule
\endhead
\midrule
\endfoot
\\bottomrule
\endlastfoot
""" % (col_title, col_title)

__LATEX_END_TABLE = """
\end{longtable}
\end{center}
"""

__LATEX_FOOTER = """
\end{document}
"""


def main(data_dcts, window_size, latex_file):
    """Count outliers for all window size / percentile configurations.
    Save results in a JSON file.
    """
    outlier_summary = {'benchmarks':dict(), 'vms':dict(), 'variants':dict()}
    for machine in data_dcts:
        keys = sorted(data_dcts[machine]['outliers'].keys())
        for key in keys:
            bench, vm, variant = key.split(':')
            if bench not in outlier_summary['benchmarks']:
                outlier_summary['benchmarks'][bench] = 0
            if vm not in outlier_summary['vms']:
                outlier_summary['vms'][vm] = 0
            if variant not in outlier_summary['variants']:
                outlier_summary['variants'][variant] = 0
            executions = data_dcts[machine]['outliers'][key]
            if len(executions) == 0:
                continue  # Benchmark skipped
            elif len(executions[0]) == 0:
                continue  # Benchmark crashed.
            else:
                for outlier_list in executions:
                    outlier_summary['benchmarks'][bench] += len(outlier_list)
                    outlier_summary['vms'][vm] += len(outlier_list)
                    outlier_summary['variants'][variant] += len(outlier_list)
    # Write out results.
    write_results_as_latex(outlier_summary, window_size, latex_file)
    return


def _tex_escape(word):
    return word.replace('_', '\\_')


def write_results_as_latex(outlier_summary, window_size, tex_file):
    """Write a results file.
    """
    print('Writing data to %s.' % tex_file)
    with open(tex_file, 'w') as fp:
        fp.write(__LATEX_HEADER(str(window_size)))
        # Outliers per benchmark.
        fp.write(__LATEX_START_TABLE('Benchmark'))
        for bench in outlier_summary['benchmarks']:
            fp.write('%s & %d \\\\ \n' %
                     (_tex_escape(bench), outlier_summary['benchmarks'][bench]))
        fp.write(__LATEX_END_TABLE)
        # Outliers per VM.
        fp.write(__LATEX_START_TABLE('Virtual machine'))
        for vm in outlier_summary['vms']:
            fp.write('%s & %d \\\\ \n' %
                     (_tex_escape(vm), outlier_summary['vms'][vm]))
        fp.write(__LATEX_END_TABLE)
        # Outliers per language variant.
        fp.write(__LATEX_START_TABLE('Language variant'))
        for variant in outlier_summary['variants']:
            fp.write('%s & %d \\\\ \n' %
                     (_tex_escape(variant), outlier_summary['variants'][variant]))
        fp.write(__LATEX_END_TABLE)
        # End document.
        fp.write(__LATEX_FOOTER)
    return


def read_krun_results_file(results_file):
    """Return the JSON data stored in a Krun results file.
    """
    results = None
    with bz2.BZ2File(results_file, 'rb') as file_:
        results = json.loads(file_.read())
        return results
    return None


def get_data_dictionaries(json_files):
    """Read a list of BZipped JSON files and return their contents as a
    dictionaries of machine name -> JSON values.
    """
    data_dictionary = dict()
    window_size = None
    for filename in json_files:
        assert os.path.exists(filename), 'File %s does not exist.' % filename
        print('Loading: %s' % filename)
        data = read_krun_results_file(filename)
        machine_name = data['audit']['uname'].split(' ')[1]
        if '.' in machine_name:  # Remove domain, if there is one.
            machine_name = machine_name.split('.')[0]
        data_dictionary[machine_name] = data
        if window_size is None:
            window_size = data['window_size']
        else:
            assert window_size == data['window_size'], \
                   ('Cannot summarise outliers generated with different' +
                    ' window sizes.')
    return window_size, data_dictionary


def create_cli_parser():
    """Create a parser to deal with command line switches.
    """
    script = os.path.basename(__file__)
    description = (('Summarise outlier information stored within a Krun ' +
                    'results file.' +
                    '\n\nExample usage:\n\n' +
                    '\t$ python %s -f bencher_results.json.bz2\n' +
                    '\t$ python %s -f results.json.bz2\n -l summary.tex')
                   % (script, script))
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--filename', '-f',
                        action='append',
                        dest='json_files',
                        default=[],
                        type=str,
                        required=True,
                        help=('Krun results file. This switch can be used ' +
                              'repeatedly to chart data from a number of ' +
                              'results files.'))
    parser.add_argument('--latexfile', '-l',
                        action='store',
                        dest='latex_file',
                        default=LATEX_FILENAME,
                        type=str,
                        help=('Name of the LaTeX file to write to.'))
    return parser


if __name__ == '__main__':
    parser = create_cli_parser()
    options = parser.parse_args()
    window_size, data_dcts = get_data_dictionaries(options.json_files)
    main(data_dcts, window_size, options.latex_file)
