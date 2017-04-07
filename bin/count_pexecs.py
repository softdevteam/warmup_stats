#!/usr/bin/env python2.7

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
from warmup.krun_results import read_krun_results_file


def main(filenames):
    all_files_total = 0
    for filename in filenames:
        print(filename)
        file_total = 0
        js = read_krun_results_file(filename)

        for key, val in js['wallclock_times'].iteritems():
            assert isinstance(val, list)
            num = len(val)
            print('  {:<50s}: {:4d}'.format(key, num))
            file_total += num
        print(72 * '-')
        print('file total (%s): %s' % (filename, file_total))
        all_files_total += file_total

    print('\n')
    print(72 * '=')
    print('GRAND TOTAL: %s' % all_files_total)
    print(72 * '=')


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('usage: count_pexecs.py results_file1 ...')
        sys.exit(1)

    files = sys.argv[1:]
    main(files)
