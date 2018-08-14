#!/usr/bin/env python2.7
#
# Copyright (c) 2018 King's College London
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
KEY = 'dummyvm:dummybmark:0'  # 0th pexec.


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
