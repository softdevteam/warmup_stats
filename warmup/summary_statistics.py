# Copyright (c) 2017 King's College London
# created by the Software Development Team <http://soft-dev.org/>
#
# The Universal Permissive License (UPL), Version 1.0
#
# Subject to the condition set forth below, permission is hereby granted to any
# person obtaining a copy of this software, associated documentation and/or
# data (collectively the "Software"), free of charge and under any and all
# copyright rights in the Software, and any and all patent rights owned or
# freely licensable by each licensor hereunder covering either (i) the
# unmodified Software as contributed to or provided by such licensor, or (ii)
# the Larger Works (as defined below), to deal in both
#
# (a) the Software, and
# (b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
# one is included with the Software (each a "Larger Work" to which the Software
# is contributed by such licensors),
#
# without restriction, including without limitation the rights to copy, create
# derivative works of, display, perform, and distribute the Software and make,
# use, sell, offer for sale, import, export, have made, and have sold the
# Software and the Larger Work(s), and to sublicense the foregoing rights on
# either these or other terms.
#
# This license is subject to the following condition: The above copyright
# notice and either this complete permission notice or at a minimum a reference
# to the UPL must be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import math

from collections import Counter, OrderedDict
from warmup.html import HTML_TABLE_TEMPLATE, HTML_PAGE_TEMPLATE
from warmup.latex import end_document, end_longtable, end_table, escape, format_median_ci
from warmup.latex import format_median_error, get_latex_symbol_map, preamble
from warmup.latex import start_longtable, start_table, STYLE_SYMBOLS
from warmup.statistics import bootstrap_runner, median_iqr

JSON_VERSION_NUMBER = '2'

TITLE = 'Summary of benchmark classifications'
TABLE_FORMAT = 'll@{\hspace{0cm}}ll@{\hspace{-1cm}}r@{\hspace{0cm}}r@{\hspace{0cm}}r@{\hspace{0cm}}l@{\hspace{.3cm}}ll@{\hspace{-1cm}}r@{\hspace{0cm}}r@{\hspace{0cm}}r'
TABLE_HEADINGS_START1 = '\\multicolumn{1}{c}{\\multirow{2}{*}{}}&'
TABLE_HEADINGS_START2 = '&'
TABLE_HEADINGS1 = '&&\\multicolumn{1}{c}{} &\\multicolumn{1}{c}{Steady}&\\multicolumn{1}{c}{Steady}&\\multicolumn{1}{c}{Steady}'
TABLE_HEADINGS2 = '&&\\multicolumn{1}{c}{Class.} &\\multicolumn{1}{c}{iter (\#)} &\\multicolumn{1}{c}{iter (s)}&\\multicolumn{1}{c}{perf (s)}'

BLANK_CELL = '\\begin{minipage}[c][\\blankheight]{0pt}\\end{minipage}'

# List indices (used in diff summaries).
CLASSIFICATIONS = 0  # Indices for top-level summary lists.
STEADY_ITER = 1
STEADY_STATE_TIME = 2
INTERSECTION = 3
SAME = 0  # Indices for nested lists.
DIFFERENT = 1
BETTER = 2
WORSE = 3


def collect_summary_statistics(data_dictionaries, delta, steady_state):
    """Create summary statistics of a dataset with classifications.
    Note that this function returns a dict which is consumed by other code to
    create tables. It also DEFINES the JSON format which the ../bin/warmup_stats
    script dumps to file.
    """

    summary_data = dict()
    # Although the caller can pass >1 json file, there should never be two
    # different machines.
    assert len(data_dictionaries) == 1
    machine = data_dictionaries.keys()[0]
    summary_data = { 'machines': { machine: dict() }, 'warmup_format_version': JSON_VERSION_NUMBER }
    # Parse data dictionaries.
    keys = sorted(data_dictionaries[machine]['wallclock_times'].keys())
    for key in sorted(keys):
        wallclock_times = data_dictionaries[machine]['wallclock_times'][key]
        if len(wallclock_times) == 0:
            print('WARNING: Skipping: %s from %s (no executions)' %
                   (key, machine))
        elif len(wallclock_times[0]) == 0:
            print('WARNING: Skipping: %s from %s (benchmark crashed)' %
                  (key, machine))
        else:
            bench, vm, variant = key.split(':')
            if vm not in summary_data['machines'][machine].keys():
                summary_data['machines'][machine][vm] = dict()
            # Get information for all p_execs of this key.
            categories = list()
            steady_state_means = list()
            steady_iters = list()
            time_to_steadys = list()
            n_pexecs = len(data_dictionaries[machine]['wallclock_times'][key])
            segments_for_bootstrap_all_pexecs = list()  # Steady state segments for all pexecs.
            # Lists of changepoints, outliers and segment means for each process execution.
            changepoints, outliers, segments = list(), list(), list()
            for p_exec in xrange(n_pexecs):
                segments_for_bootstrap_this_pexec = list()  # Steady state segments for this pexec.
                changepoints.append(data_dictionaries[machine]['changepoints'][key][p_exec])
                segments.append(data_dictionaries[machine]['changepoint_means'][key][p_exec])
                outliers.append(data_dictionaries[machine]['all_outliers'][key][p_exec])
                categories.append(data_dictionaries[machine]['classifications'][key][p_exec])
                # Next we calculate the iteration at which a steady state was
                # reached, it's average segment mean and the time to reach a
                # steady state. However, the last segment may be equivalent to
                # its adjacent segments, so we first need to know which segments
                # are steady-state segments.
                if data_dictionaries[machine]['classifications'][key][p_exec] == 'no steady state':
                    continue
                # Capture the last steady state segment for bootstrapping.
                segment_data = list()
                if data_dictionaries[machine]['changepoints'][key][p_exec]:
                    start = data_dictionaries[machine]['changepoints'][key][p_exec][-1]
                else:
                    start = 0  # No changepoints in this pexec.
                end = len(data_dictionaries[machine]['wallclock_times'][key][p_exec])
                for segment_index in xrange(start, end):
                    if segment_index in data_dictionaries[machine]['all_outliers'][key][p_exec]:
                        continue
                    segment_data.append(data_dictionaries[machine]['wallclock_times'][key][p_exec][segment_index])
                segments_for_bootstrap_this_pexec.append(segment_data)

                first_steady_segment = len(data_dictionaries[machine]['changepoint_means'][key][p_exec]) - 1
                num_steady_segments = 1
                last_segment_mean = data_dictionaries[machine]['changepoint_means'][key][p_exec][-1]
                last_segment_var = data_dictionaries[machine]['changepoint_vars'][key][p_exec][-1]
                lower_bound = min(last_segment_mean - last_segment_var, last_segment_mean - delta)
                upper_bound = max(last_segment_mean + last_segment_var, last_segment_mean + delta)
                # This for loop deals with segments that are equivalent to the
                # final, steady state segment.
                for index in xrange(len(data_dictionaries[machine]['changepoint_means'][key][p_exec]) - 2, -1, -1):
                    current_segment_mean = data_dictionaries[machine]['changepoint_means'][key][p_exec][index]
                    current_segment_var = data_dictionaries[machine]['changepoint_vars'][key][p_exec][index]
                    if (current_segment_mean + current_segment_var >= lower_bound and
                            current_segment_mean - current_segment_var<= upper_bound):
                        # Extract this segment from the wallclock data for bootstrapping.
                        segment_data = list()
                        if index == 0:
                            start = 0
                            end = data_dictionaries[machine]['changepoints'][key][p_exec][index] + 1
                        else:
                            start = data_dictionaries[machine]['changepoints'][key][p_exec][index - 1] + 1
                            end = data_dictionaries[machine]['changepoints'][key][p_exec][index] + 1
                        for segment_index in xrange(start, end):
                            if segment_index in data_dictionaries[machine]['all_outliers'][key][p_exec]:
                                continue
                            segment_data.append(data_dictionaries[machine]['wallclock_times'][key][p_exec][segment_index])
                        segments_for_bootstrap_this_pexec.append(segment_data)
                        # Increment / decrement counters.
                        first_steady_segment -= 1
                        num_steady_segments += 1
                    else:
                        break
                segments_for_bootstrap_all_pexecs.append(segments_for_bootstrap_this_pexec)
                # End of code to capture segments for bootstrapping.
                steady_state_mean = (math.fsum(data_dictionaries[machine]['changepoint_means'][key][p_exec][first_steady_segment:])
                                     / float(num_steady_segments))
                steady_state_means.append(steady_state_mean)
                # Not all process execs have changepoints. However, all
                # p_execs will have one or more segment mean.
                if data_dictionaries[machine]['classifications'][key][p_exec] != 'flat':
                    steady_iter = data_dictionaries[machine]['changepoints'][key][p_exec][first_steady_segment - 1]
                    steady_iters.append(steady_iter + 1)
                    to_steady = 0.0
                    for index in xrange(steady_iter):
                        to_steady += data_dictionaries[machine]['wallclock_times'][key][p_exec][index]
                    time_to_steadys.append(to_steady)
                else:  # Flat execution, with no changepoints.
                    steady_iters.append(1)
                    time_to_steadys.append(0.0)
            # Get overall and detailed categories.
            categories_set = set(categories)
            if len(categories_set) == 1:  # NB some benchmarks may have errored.
                reported_category = categories[0]
            elif categories_set == set(['flat', 'warmup']):
                reported_category = 'good inconsistent'
            else:  # Bad inconsistent.
                reported_category = 'bad inconsistent'
            cat_counts = dict()
            for category, occurences in Counter(categories).most_common():
                cat_counts[category] = occurences
            for category in ['flat', 'warmup', 'slowdown', 'no steady state']:
                if category not in cat_counts:
                    cat_counts[category] = 0
            # Average information for all process executions.
            if cat_counts['no steady state'] > 0:
                mean_time, error_time = None, None
                median_iter, error_iter = None, None
                median_time_to_steady, error_time_to_steady = None, None
            elif categories_set == set(['flat']):
                median_iter, error_iter = None, None
                median_time_to_steady, error_time_to_steady = None, None
                # Shell out to PyPy for speed.
                marshalled_data = json.dumps(segments_for_bootstrap_all_pexecs)
                mean_time, error_time = bootstrap_runner(marshalled_data)
                if mean_time is None or error_time is None:
                    raise ValueError()
            else:
                # Shell out to PyPy for speed.
                marshalled_data = json.dumps(segments_for_bootstrap_all_pexecs)
                mean_time, error_time = bootstrap_runner(marshalled_data)
                if mean_time is None or error_time is None:
                    raise ValueError()
                if steady_iters:
                    median_iter, error_iter = median_iqr([float(val) for val in steady_iters])
                    median_time_to_steady, error_time_to_steady = median_iqr(time_to_steadys)
                else:  # No changepoints in any process executions.
                    assert False  # Should be handled by elif clause above.
            # Add summary for this benchmark.
            current_benchmark = dict()
            current_benchmark['classification'] = reported_category
            current_benchmark['detailed_classification'] = cat_counts
            current_benchmark['steady_state_iteration'] = median_iter
            current_benchmark['steady_state_iteration_iqr'] = error_iter
            current_benchmark['steady_state_iteration_list'] = steady_iters
            current_benchmark['steady_state_time_to_reach_secs'] = median_time_to_steady
            current_benchmark['steady_state_time_to_reach_secs_iqr'] = error_time_to_steady
            current_benchmark['steady_state_time_to_reach_secs_list'] = time_to_steadys
            current_benchmark['steady_state_time'] = mean_time
            current_benchmark['steady_state_time_ci'] = error_time
            current_benchmark['steady_state_time_list'] = steady_state_means

            pexecs = list()  # This is needed for JSON output.
            for index in xrange(n_pexecs):
                pexecs.append({'index':index, 'classification':categories[index],
                              'outliers':outliers[index], 'changepoints':changepoints[index],
                              'segment_means':segments[index]})
            current_benchmark['process_executons'] = pexecs
            summary_data['machines'][machine][vm][bench] = current_benchmark
    return summary_data


def convert_to_latex(summary_data, delta, steady_state, diff=None, previous=None):
    assert 'warmup_format_version' in summary_data and summary_data['warmup_format_version'] == JSON_VERSION_NUMBER, \
        'Cannot process data from old JSON formats.'
    if (diff and not previous) or (previous and not diff):
        assert False, 'convert_to_latex needs both diff and previous arguments.'
    machine = None
    for key in summary_data['machines']:
        if key == 'warmup_format_version':
            continue
        elif machine is not None:
            assert False, 'Cannot summarise data from more than one machine.'
        else:
            machine = key
    benchmark_names = set()
    latex_summary = dict()
    for vm in summary_data['machines'][machine]:
        latex_summary[vm] = dict()
        for bmark_name in summary_data['machines'][machine][vm]:
            bmark = summary_data['machines'][machine][vm][bmark_name]
            benchmark_names.add(bmark_name)
            if bmark['classification'] == 'bad inconsistent':
                reported_category = STYLE_SYMBOLS['bad inconsistent']
                cats_sorted = OrderedDict(sorted(bmark['detailed_classification'].items(),
                                                 key=lambda x: x[1], reverse=True))
                cat_counts = list()
                for category in cats_sorted:
                    if cats_sorted[category] == 0:
                        continue
                    cat_counts.append('$%d$%s' % (cats_sorted[category], STYLE_SYMBOLS[category]))
                reported_category += ' \\scriptsize(%s)' % ', '.join(cat_counts)
            elif bmark['classification'] == 'good inconsistent':
                reported_category = STYLE_SYMBOLS['good inconsistent']
                cats_sorted = OrderedDict(sorted(bmark['detailed_classification'].items(),
                                                 key=lambda x: x[1], reverse=True))
                cat_counts = list()
                for category in cats_sorted:
                    if cats_sorted[category] == 0:
                        continue
                    cat_counts.append('$%d$%s' % (cats_sorted[category], STYLE_SYMBOLS[category]))
                reported_category += ' \\scriptsize(%s)' % ', '.join(cat_counts)
            elif (sum(bmark['detailed_classification'].values()) ==
                  bmark['detailed_classification'][bmark['classification']]):
                # Consistent benchmark with no errors.
                reported_category = STYLE_SYMBOLS[bmark['classification']]
            else:  # No inconsistencies, but some process executions errored.
                reported_category = ' %s\\scriptsize{($%d$)}' % \
                                    (STYLE_SYMBOLS[bmark['classification']],
                                     bmark['detailed_classification'][bmark['classification']])
            if bmark['steady_state_iteration'] is not None:
                change = None
                if diff and diff[vm][bmark_name] and diff[vm][bmark_name][STEADY_ITER] > 0 and \
                        previous['machines'][machine][vm][bmark_name]['steady_state_iteration']:
                    change = bmark['steady_state_iteration'] - \
                        previous['machines'][machine][vm][bmark_name]['steady_state_iteration']
                mean_steady_iter = format_median_error(bmark['steady_state_iteration'],
                                                       bmark['steady_state_iteration_iqr'],
                                                       bmark['steady_state_iteration_list'],
                                                       one_dp=True,
                                                       change=change)
            else:
                mean_steady_iter = ''
            if bmark['steady_state_time'] is not None:
                change = None
                if diff and diff[vm][bmark_name] and diff[vm][bmark_name][STEADY_STATE_TIME] > 0 and \
                        previous['machines'][machine][vm][bmark_name]['steady_state_time_ci']:
                    change = bmark['steady_state_time'] - \
                        previous['machines'][machine][vm][bmark_name]['steady_state_time']
                mean_steady = format_median_ci(bmark['steady_state_time'],
                                               bmark['steady_state_time_ci'],
                                               bmark['steady_state_time_list'],
                                               change=change)
            else:
                mean_steady = ''
            if bmark['steady_state_time_to_reach_secs'] is not None:
                change = None
                if diff and diff[vm][bmark_name] and diff[vm][bmark_name][STEADY_ITER] > 0 and \
                        previous['machines'][machine][vm][bmark_name]['steady_state_time_to_reach_secs']:
                    change = bmark['steady_state_time_to_reach_secs'] - \
                        previous['machines'][machine][vm][bmark_name]['steady_state_time_to_reach_secs']
                time_to_steady = format_median_error(bmark['steady_state_time_to_reach_secs'],
                                                     bmark['steady_state_time_to_reach_secs_iqr'],
                                                     bmark['steady_state_time_to_reach_secs_list'],
                                                     two_dp=True,
                                                     change=change)
            else:
                time_to_steady = ''
            latex_summary[vm][bmark_name] = {'style': reported_category,
                'last_cpt': mean_steady_iter, 'last_mean': mean_steady,
                'time_to_steady_state':time_to_steady}
    return machine, list(sorted(benchmark_names)), latex_summary


def write_latex_table(machine, all_benchs, summary, tex_file, num_splits,
                      with_preamble=False, longtable=False):
    """Write a tex table to disk"""

    num_benchmarks = len(all_benchs)
    all_vms = sorted(summary.keys())
    num_vms = len(summary)

    # decide how to lay out the splits
    num_vms_rounded = int(math.ceil(num_vms / float(num_splits)) * num_splits)
    vms_per_split = int(num_vms_rounded / float(num_splits))
    splits = [[] for x in xrange(num_splits)]
    vm_num = 0
    split_idx = 0
    for vm_idx in xrange(num_vms_rounded):
        if vm_idx < len(all_vms):
            vm = all_vms[vm_idx]
        else:
            vm = None
        splits[split_idx].append(vm)
        vm_num += 1
        if vm_num % vms_per_split == 0:
            split_idx += 1

    with open(tex_file, 'w') as fp:
        if with_preamble:
            fp.write(preamble(TITLE))
            fp.write('\\centering %s' % get_latex_symbol_map())
            fp.write('\n\n\n')
            if not longtable:
                fp.write('\\begin{landscape}\n')
                fp.write('\\begin{table*}[hptb]\n')
                fp.write('\\vspace{.8cm}\n')
                fp.write('\\begin{adjustbox}{totalheight=12.4cm}\n')
        # emit table header
        heads1 = TABLE_HEADINGS_START1 + '&'.join([TABLE_HEADINGS1] * num_splits)
        heads2 = TABLE_HEADINGS_START2 + '&'.join([TABLE_HEADINGS2] * num_splits)
        heads = '%s\\\\%s' % (heads1, heads2)
        if longtable:
            fp.write(start_longtable(TABLE_FORMAT, heads))
        else:
            fp.write(start_table(TABLE_FORMAT, heads))
        split_row_idx = 0
        for row_vms in zip(*splits):
            bench_idx = 0
            for bench in sorted(all_benchs):
                row = []
                for vm in row_vms:
                    if vm is None:
                        continue # no more results
                    try:
                        this_summary = summary[vm][bench]
                    except KeyError:
                        last_cpt = BLANK_CELL
                        time_steady = BLANK_CELL
                        last_mean = BLANK_CELL
                        classification = ''
                    else:
                        classification = this_summary['style']
                        last_cpt = this_summary['last_cpt']
                        time_steady = this_summary['time_to_steady_state']
                        last_mean = this_summary['last_mean']

                        classification = '\\multicolumn{1}{l}{%s}' % classification
                        if classification == STYLE_SYMBOLS['flat']:
                            last_cpt = BLANK_CELL
                            time_steady = BLANK_CELL
                    if last_cpt == '':
                        last_cpt = BLANK_CELL
                    if time_steady == '':
                        time_steady = BLANK_CELL
                    if last_mean == '':
                        last_mean = BLANK_CELL

                    if bench_idx == 0:
                        if num_benchmarks == 10:
                            fudge = 4
                        elif num_benchmarks == 12:
                            fudge = 5
                        else:
                            fudge = 0
                        vm_cell = '\\multirow{%s}{*}{\\rotatebox[origin=c]{90}{%s}}' \
                            % (num_benchmarks + fudge, vm)
                    else:
                        vm_cell = ''
                    row_add = [BLANK_CELL, vm_cell, classification, last_cpt,
                               time_steady, last_mean]
                    if not row:  # first bench in this row, needs the vm column
                        row.insert(0, escape(bench))
                    row.extend(row_add)
                    vm_idx += 1
                fp.write('&'.join(row))
                # Only -ve space row if not next to a midrule
                if bench_idx < num_vms - 1:
                    fp.write('\\\\[-3pt] \n')
                else:
                    fp.write('\\\\ \n')
                bench_idx += 1
            if split_row_idx < vms_per_split - 1:
                if longtable:
                    fp.write('\\hline\n')
                else:
                    fp.write('\\midrule\n')
            split_row_idx += 1
        if longtable:
            fp.write(end_longtable())
        else:
            fp.write(end_table())
        if with_preamble:
            if not longtable:
                fp.write('\\end{adjustbox}\n')
                fp.write('\\end{table*}\n')
                fp.write('\\end{landscape}\n')
            fp.write(end_document())


def write_html_table(summary_data, html_filename):
    assert 'warmup_format_version' in summary_data and summary_data['warmup_format_version'] == JSON_VERSION_NUMBER, \
        'Cannot process data from old JSON formats.'
    machine = None
    for key in summary_data['machines']:
        if key == 'warmup_format_version':
            continue
        elif machine is not None:
            assert False, 'Cannot summarise data from more than one machine.'
        else:
            machine = key
    html_table_contents = dict()  # VM name -> html rows
    for vm in sorted(summary_data['machines'][machine]):
        html_rows = ''  # Just the table rows, no table header, etc.
        for bmark_name in sorted(summary_data['machines'][machine][vm]):
            bmark = summary_data['machines'][machine][vm][bmark_name]
            if bmark['classification'] == 'bad inconsistent':
                reported_category = 'bad inconsistent:'
                cats_sorted = OrderedDict(sorted(bmark['detailed_classification'].items(),
                                                 key=lambda x: x[1], reverse=True))
                cat_counts = list()
                for category in cats_sorted:
                    if cats_sorted[category] == 0:
                        continue
                    cat_counts.append('%d %s' % (cats_sorted[category], category))
                reported_category += ' %s' % ', '.join(cat_counts)
            elif bmark['classification'] == 'good inconsistent':
                reported_category = 'good inconsistent:'
                cats_sorted = OrderedDict(sorted(bmark['detailed_classification'].items(),
                                                 key=lambda x: x[1], reverse=True))
                cat_counts = list()
                for category in cats_sorted:
                    if cats_sorted[category] == 0:
                        continue
                    cat_counts.append('%d %s' % (cats_sorted[category], category))
                reported_category += ' %s' % ', '.join(cat_counts)
            elif (sum(bmark['detailed_classification'].values()) ==
                  bmark['detailed_classification'][bmark['classification']]):
                # Consistent benchmark with no errors.
                reported_category = bmark['classification']
            else:  # No inconsistencies, but some process executions errored.
                reported_category = ' %s %d' % (bmark['classification'],
                                     bmark['detailed_classification'][bmark['classification']])
            if bmark['steady_state_iteration'] is not None:
                mean_steady_iter = '%d (%d, %d)' % (int(math.ceil(bmark['steady_state_iteration'])),
                                                    int(math.ceil(bmark['steady_state_iteration_iqr'][0])),
                                                    int(math.ceil(bmark['steady_state_iteration_iqr'][1])))
            else:
                mean_steady_iter = ''
            if bmark['steady_state_time'] is not None:
                mean_steady = '%.5f&plusmn;%.6f' % (bmark['steady_state_time'],
                                                    bmark['steady_state_time_ci'])
            else:
                mean_steady = ''
            if bmark['steady_state_time_to_reach_secs'] is not None:
                time_to_steady = '%.3f (%.3f, %.3f)' % (bmark['steady_state_time_to_reach_secs'],
                                                        bmark['steady_state_time_to_reach_secs_iqr'][0],
                                                        bmark['steady_state_time_to_reach_secs_iqr'][1])
            else:
                time_to_steady = ''
            # Benchmark name, classification, steady iter, time to reach, steady perf
            row = ('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>\n' %
                   (bmark_name, reported_category, mean_steady_iter,
                    time_to_steady, mean_steady))
            html_rows += row
        html_table_contents[vm] = html_rows
    page_contents = ''
    for vm in html_table_contents:
        page_contents += HTML_TABLE_TEMPLATE % (vm, html_table_contents[vm])
        page_contents += '\n\n'
    with open(html_filename, 'w') as fp:
        fp.write(HTML_PAGE_TEMPLATE % page_contents)
