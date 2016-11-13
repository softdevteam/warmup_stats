import bz2
import json


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


def read_krun_results_file(results_file):
    """Return the JSON data stored in a Krun results file.
    """
    results = None
    with bz2.BZ2File(results_file, 'rb') as file_:
        results = json.loads(file_.read())
        return results
    return None


def write_krun_results_file(results, filename):
    """Write a Krun results file to disk.
    """
    with bz2.BZ2File(filename, 'wb') as file_:
        file_.write(json.dumps(results))
