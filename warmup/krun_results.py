import bz2
import csv
import json
import os.path


_MACHINES = {
    'bencher3': r'Linux$_\mathrm{4790K}$',
    'bencher5': r'Linux$_\mathrm{4790}$',
    'bencher6': r'OpenBSD$_\mathrm{4790}$',
    'bencher7': r'Linux$_\mathrm{E3-1240v5}$',
}


_VARIANTS = {'default-python': 'Python',
             'default-c': 'C',
             'default-php': 'PHP',
             'default-java': 'Java',
             'default-ruby': 'Ruby',
             'default-javascript': 'Javascript',
             'default-lua': 'Lua'}


_BLANK_BENCHMARK = { 'wallclock_times': dict(), # Measurement data.
                    'core_cycle_counts': dict(), 'aperf_counts': dict(),
                    'mperf_counts': dict(), 'audit': dict(), 'config': '',
                    'reboots': 0, 'starting_temperatures': list(),
                    'eta_estimates': list(), 'error_flag': list(), }

_SKIP_OUTER_KEYS = ['audit', 'reboots', 'mperf_counts', 'aperf_counts',
                    'eta_estimates', 'starting_temperatures', 'core_cycle_counts',
                    'config', 'error_flag', 'window_size']


def csv_to_krun_json(in_files, language, vm, uname):
    for filename in in_files:
        data_dictionary = _BLANK_BENCHMARK

        # First sort the lines by benchmark, then pexec number.
        # We do this so we can easily check for gaps (missing pexecs).
        with open(filename, 'r') as fd:
            reader = csv.reader(fd)
            header = reader.next()  # Skip header row.
            rows = iter(reader)
            sorted_rows = sorted(rows, key=lambda l: (l[1], int(l[0])))

        data_dictionary['audit']['uname'] = uname
        expect_idx = [0]  # check we get in-order indices, first always 0
        for row in sorted_rows:
            # First cell contains process execution number.
            assert int(row[0]) in expect_idx, \
                'Found gaps in process executions for %s.\n' \
                'Expected a pexec number in %s, but got %s!' \
                % (row[1], expect_idx, row[0])
            bench = row[1]
            if row[2] == 'crash':
                data = []
            else:
                data = [float(datum) for datum in row[2:]]
            key = '%s:%s:default-%s' % (bench, vm, language)
            if key not in data_dictionary['wallclock_times']:
                data_dictionary['wallclock_times'][key] = list()
                data_dictionary['core_cycle_counts'][key] = list()
                data_dictionary['aperf_counts'][key] = list()
                data_dictionary['mperf_counts'][key] = list()
            data_dictionary['wallclock_times'][key].append(data)
            data_dictionary['core_cycle_counts'][key].append(None)
            data_dictionary['aperf_counts'][key].append(None)
            data_dictionary['mperf_counts'][key].append(None)
            # Expect the next process execution index, or the first process
            # execution index (0) of the next benchmark.
            expect_idx = [0, int(row[0]) + 1]

        new_filename = os.path.splitext(filename)[0] + '.json.bz2'
        write_krun_results_file(data_dictionary, new_filename)
        return header, new_filename


def pretty_print_machine(machine):
    if machine in _MACHINES:
        return _MACHINES[machine]
    return machine.capitalize()


def pretty_print_variant(language):
    if language in _VARIANTS:
        return _VARIANTS[language]
    elif language.startswith('default-'):
        name = language[len('default-'):]
        return name.capitalize()
    return language.capitalize()


def create_minimal_blank_results(audit):
    return {'wallclock_times':dict(), 'all_outliers':dict(),
            'common_outliers':dict(), 'unique_outliers':dict(), 'audit':audit}


def copy_results(key, p_execs, from_results, to_results):
    if p_execs is None:
        to_results['wallclock_times'][key] = from_results['wallclock_times'][key]
        to_results['all_outliers'][key] = from_results['all_outliers'][key]
        to_results['unique_outliers'][key] = from_results['unique_outliers'][key]
        to_results['common_outliers'][key] = from_results['common_outliers'][key]
        return
    to_results['wallclock_times'][key] = list()
    to_results['all_outliers'][key] = list()
    to_results['unique_outliers'][key] = list()
    to_results['common_outliers'][key] = list()
    for p_exec in p_execs:
        to_results['wallclock_times'][key].append(from_results['wallclock_times'][key][p_exec])
        to_results['all_outliers'][key].append(from_results['all_outliers'][key][p_exec])
        to_results['unique_outliers'][key].append(from_results['unique_outliers'][key][p_exec])
        to_results['common_outliers'][key].append(from_results['common_outliers'][key][p_exec])


def parse_krun_file_with_changepoints(json_files):
    data_dictionary = dict()
    classifier = None  # steady and delta values used by classifer.
    window_size = None
    for filename in json_files:
        assert os.path.exists(filename), 'File %s does not exist.' % filename
        data = read_krun_results_file(filename)
        assert 'classifications' in data, 'Please run mark_changepoints_in_json before re-running this script.'
        machine_name = data['audit']['uname'].split(' ')[1]
        if '.' in machine_name:  # Remove domain, if there is one.
            machine_name = machine_name.split('.')[0]
        if machine_name not in data_dictionary:
            data_dictionary[machine_name] = data
        else:  # We may have two datasets from the same machine.
            for outer_key in data:
                if outer_key in _SKIP_OUTER_KEYS:
                    continue
                elif outer_key == 'classifier':
                    assert data_dictionary[machine_name][outer_key] == data[outer_key]
                    continue
                for key in data[outer_key]:
                    assert key not in data_dictionary[machine_name][outer_key]
                    if key not in data_dictionary[machine_name][outer_key]:
                        data_dictionary[machine_name][outer_key][key] = dict()
                    data_dictionary[machine_name][outer_key][key] = data[outer_key][key]
        if classifier is None:
            classifier = data['classifier']
        else:
            assert classifier == data['classifier'], \
                   ('Cannot summarise categories generated with different '
                    'command-line options for steady-state-expected '
                    'or delta. Please re-run the mark_changepoints_in_json script.')
        if window_size is None:
            window_size = data['window_size']
        else:
            assert window_size == data['window_size'], \
                   ('Cannot summarise categories generated with different window-size '
                    'options. Please re-run the mark_outliers_in_json script.')
    return classifier, data_dictionary


def read_krun_results_file(results_file):
    """Return the JSON data stored in a Krun results file.
    """
    results = None
    with bz2.BZ2File(results_file, 'rb') as file_:
        results = json.loads(file_.read())
        return results
    return None


def write_krun_results_file(results, filename):
    """Write a Krun results file to disk."""

    with bz2.BZ2File(filename, 'wb') as file_:
        file_.write(json.dumps(results, indent=4))
