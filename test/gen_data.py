#!/usr/bin/env python2.7

"""Generate random Krun JSON files."""

import os
import os.path
import random
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from warmup.krun_results import write_krun_results_file


UNAME = 'Linux bencher8 4.9.0-3-amd64 #1 SMP Debian 4.9.30-2+deb9u5 (2017-09-19) x86_64 GNU/Linux'
AUDIT = { 'uname': UNAME }
ITERS = 2000
KEY = 'dummybmark:dummyvm:0'  # 0th pexec.


def create_filename(nth):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'example' + str(nth) + '.json.bz2')


def create_random_results():
    results = { 'audit': AUDIT,
                'wallclock_times': { KEY: [[]] },
                'core_cycle_counts': { KEY: [[]] },
              }
    for _ in xrange(ITERS):
        results['wallclock_times'][KEY][0].append(random.random())
    return results


if __name__ == '__main__':
    seed = random.randrange(sys.maxint)
    random.seed(a=seed)
    print('Test data was generated with seed: %d' % seed)
    # We create two example data files, so that we can diff them.
    write_krun_results_file(create_random_results(), create_filename(1))
    write_krun_results_file(create_random_results(), create_filename(2))
