#!/bin/env pypy

"""
This script is designed to be run with PyPy via a pipe.

It has been factored out because the code here is too slow to run on CPython.
It will read JSON format data from STDIN, and will write a comma-separated pair
of floats (mean, CI) on STDOUT.

Input data should be as per. the needs of the tables for the "main" warmup
experiment -- i.e. a list of pexecs, each containing a list of (steady state)
segments, each containing a list of floats.

Much of the code here comes from libkalibera.
"""

import argparse, json, math, random, sys

from decimal import Decimal, ROUND_UP, ROUND_DOWN


BOOTSTRAP_ITERATIONS_HIGHQ = 100000
BOOTSTRAP_ITERATIONS_LOWQ = 10000
CONFIDENCE_LEVEL = '0.99'  # Must be a string to pass to Decimal.


def _mean(data):
    assert len(data), '_mean() received no data to average.'
    return math.fsum(data) / float(len(data))


def _bootstrap_means_lowq(steady_segments_all_pexecs):
    # How many bootstrap samples do we need from each pexec? We want at least
    # BOOTSTRAP_ITERATIONS samples over all. If we want 100,000 samples in total
    # and we have 30 pexecs, we need 3333 samples from each pexec. In total we
    # will have 3333 * 30 bootstrapped samples, and 3333 * 30 == 99990. So, we
    # add a 1 here to ensure that we end up with >= BOOTSTRAP_ITERATIONS samples.
    n_resamples = int(math.floor(BOOTSTRAP_ITERATIONS_LOWQ / len(steady_segments_all_pexecs))) + 1
    means = list()  # Final list of BOOTSTRAP_ITERATIONS resamples.

    for segments in steady_segments_all_pexecs:  # Iterate over pexecs.
        for _ in xrange(n_resamples):
            num_samples = 0

            # Note that summing into a float like this does cause rounding
            # errors, but for 10,000 bootstrap iterations and values in the
            # 0.0-1.0 range, that error is only apparent at the 10th decimal
            # place. However, the error increases as the bootstrap iterations
            # and/or timings increase above: roughly speaking the error becomes
            # 1 decimal place worse for each order of magnitude bigger the
            # bootstrap iterations and/or timings become.
            sample_sum = 0.0
            for seg in segments:
                seg_len = len(seg)
                num_samples += seg_len
                for _ in xrange(seg_len):
                    sample_sum += seg[int(random.random() * seg_len)]

            means.append(sample_sum / float(num_samples))
    assert len(means) >= BOOTSTRAP_ITERATIONS_LOWQ
    return means

def _bootstrap_means_highq(steady_segments_all_pexecs):
    # How many bootstrap samples do we need from each pexec? We want at least
    # BOOTSTRAP_ITERATIONS samples over all. If we want 100,000 samples in total
    # and we have 30 pexecs, we need 3333 samples from each pexec. In total we
    # will have 3333 * 30 bootstrapped samples, and 3333 * 30 == 99990. So, we
    # add a 1 here to ensure that we end up with >= BOOTSTRAP_ITERATIONS samples.
    n_resamples = int(math.floor(BOOTSTRAP_ITERATIONS_HIGHQ / len(steady_segments_all_pexecs))) + 1
    means = list()  # Final list of BOOTSTRAP_ITERATIONS resamples.

    for segments in steady_segments_all_pexecs:  # Iterate over pexecs.
        for _ in xrange(n_resamples):
            sample = list()
            for seg in segments:
                sample.extend([random.choice(seg) for _ in xrange(len(seg))])
            means.append(_mean(sample))
    assert len(means) >= BOOTSTRAP_ITERATIONS_HIGHQ
    return means


def bootstrap_steady_perf(steady_segments_all_pexecs, confidence_level=CONFIDENCE_LEVEL, quality='HIGH'):
    """This is not a general bootstrapping function.
    Input is a list containing a list for each pexec, containing a list of
    segments with iteration times.
    """
    if quality.lower() == "high":
        means = _bootstrap_means_highq(steady_segments_all_pexecs)
    elif quality.lower() == "low":
        means = _bootstrap_means_lowq(steady_segments_all_pexecs)
    else:
        sys.stderr.write("Unknown quality level '%s'" % quality)
        sys.exit(1)
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
    parser = argparse.ArgumentParser(description='Bootstrap data.')
    parser.add_argument('--quality', action='store', default='HIGH',
                        dest='quality',
                        help='Quality of statistics. Must be one of: LOW, HIGH.')
    options = parser.parse_args()
    data = json.loads(sys.stdin.readline())
    results = bootstrap_steady_perf(data, quality=options.quality)
    sys.stdout.write(','.join([str(result) for result in results]))
    sys.stdout.flush()
