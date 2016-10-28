import bz2
import json


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
