#!/bin/env pypy
#
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

"""
This script is designed to be run with PyPy via a pipe.

It has been factored out because the code here is too slow to run on CPython,
and we need numpy as a dependency in related parts of the code base. Although
there is a version of numpy for PyPy, we wanted to reduce the number of
complications that arise for end-users.

It will read JSON format data from STDIN, and will write a comma-separated pair
of floats (mean, CI) on STDOUT.

Input data should be as per. the needs of the tables for the "main" warmup
experiment -- i.e. a list of pexecs, each containing a list of (steady state)
segments, each containing a list of floats.

Much of the code here comes from libkalibera.
"""

import math
import random

from decimal import Decimal, ROUND_UP, ROUND_DOWN


BOOTSTRAP_ITERATIONS = 100000
CONFIDENCE_LEVEL = '0.99'  # Must be a string to pass to Decimal.


def _mean(data):
    assert len(data), '_mean() received no data to average.'
    return math.fsum(data) / float(len(data))


def bootstrap_steady_perf(steady_segments_all_pexecs, confidence_level=CONFIDENCE_LEVEL):
    """This is not a general bootstrapping function.
    Input is a list containing a list for each pexec, containing a list of
    segments with iteration times.
    """

    # How many bootstrap samples do we need from each pexec? We want at least
    # BOOTSTRAP_ITERATIONS samples over all. If we want 100,000 samples in total
    # and we have 30 pexecs, we need 3333 samples from each pexec. In total we
    # will have 3333 * 30 bootstrapped samples, and 3333 * 30 == 99990. So, we
    # add a 1 here to ensure that we end up with >= BOOTSTRAP_ITERATIONS samples.
    n_resamples = int(math.floor(BOOTSTRAP_ITERATIONS / len(steady_segments_all_pexecs))) + 1
    means = list()  # Final list of BOOTSTRAP_ITERATIONS resamples.

    for segments in steady_segments_all_pexecs:  # Iterate over pexecs.
        for _ in xrange(n_resamples):
            sample = list()
            for seg in segments:
                sample.extend([random.choice(seg) for _ in xrange(len(seg))])
            means.append(_mean(sample))
    assert len(means) >= BOOTSTRAP_ITERATIONS

    means.sort()

    # Compute reported mean and confidence interval. Code below is from libkalibera.
    assert not isinstance(confidence_level, float)
    confidence_level = Decimal(confidence_level)
    assert isinstance(confidence_level, Decimal)
    exclude = (1 - confidence_level) / 2
    length = len(means)
    # There may be >1 median index if data is even-sized.
    if length % 2 == 0:
        median_indices = (length // 2 - 1, length // 2)
    else:
        median_indices = (length // 2, )
    lower_index = int((exclude * length).quantize(Decimal('1.0'), rounding=ROUND_DOWN))
    upper_index = int(((1 - exclude) * length).quantize(Decimal('1.0'), rounding=ROUND_UP))
    lower, upper = means[lower_index], means[upper_index - 1]  # upper is exclusive.
    median = _mean([means[i] for i in median_indices])  # Reported mean.
    ci = _mean([upper - median, median - lower])  # Confidence interval.
    return median, ci


if __name__ == '__main__':
    import json
    import sys
    data = json.loads(sys.stdin.readline())
    results = bootstrap_steady_perf(data)
    sys.stdout.write(','.join([str(result) for result in results]))
    sys.stdout.flush()
