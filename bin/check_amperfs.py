#!/usr/bin/env python2.7
"""
usage: check_amperfs.py <results_file> <aperf/mperf-ratio-bounds>
            <tickful-busy-threshold> <tickless-busy-threshold>
            <busy-threshold-factor> <migration-lookback>

Checks if the CPU has clocked down or entered turbo mode during Krun
benchmarking. A core is considered idle when the aperf value is less than the
estimated busy cycle count divided by the busy threshold factor. Busy core
aperf/mperf ratios for busy cores are then checked to be within the specified
bouunds.

Arguments:
    * results_file:
        A krun results file (with outliers annotated).

    * ratio-bounds:
        Comma separated pair of acceptable deviation from the target
        aperf/mperf ratio of 1. e.g. '0.9,1.2' allows ratios (r) in the bound
        0.9 <= r <= 1.2.

    * busy-cycle-count-estimate
        Estimated time-normalised (per-second) aperf reading for a busy CPU
        core. We do not differentiate tickful cores from tickless cores.

    * busy-threshold-factor:
        Value to divide busy-thresholds by to decide if a core was busy or
        idle. E.g. 1000

    * migration-lookback:
      Number of iterations to look back for migration. Dodgy aperf/mperf ratios
      will be ignored if the fall in this interval.
"""


import sys
import os

num_bad_pexecs = 0
outlier_violations = []
non_outlier_violations = []
num_bad_iterations = 0
num_bad_iterations_outliers = 0


sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from warmup.krun_results import read_krun_results_file


def recently_migrated(aperfs, iter_idx, busy_threshold, migration_lookback):
    for i in xrange(1, migration_lookback + 1):
        prior_aperf = aperfs[iter_idx - i]
        if prior_aperf < busy_threshold:
            return True
    return False


def check_amperfs(aperfs, mperfs, wcts, busy_threshold, ratio_bounds, key,
                  pexec_idx, core_idx, migration_lookback, cycles,
                  all_cores_aperfs, all_cores_mperfs, all_cores_cycles,
                  outliers):
    assert len(aperfs) == len(mperfs) == len(wcts)

    iter_idx = 0
    violating_iterations = set()
    for aval, mval, wctval in zip(aperfs, mperfs, wcts):
        # normalise the counts to per-second readings
        norm_aval = float(aval) / wctval
        norm_mval = float(mval) / wctval
        ratio = norm_aval / norm_mval

        if norm_aval > busy_threshold:
            # Busy core
            if ratio < ratio_bounds[0]:
                violating_iterations.add(iter_idx)
                badness_type = "throttling"
            elif ratio > ratio_bounds[1]:
                violating_iterations.add(iter_idx)
                badness_type = "turbo"
            else:
                badness_type = None

            if badness_type is not None:
                rec = ("%10s: key=%35s, pexec=%2d, iter=%4d core=%s, "
                       "ratio=%10.8f") % \
                    (badness_type, key, pexec_idx, iter_idx, core_idx,
                     ratio)
                if iter_idx in outliers:
                    outlier_violations.append(rec)
                else:
                    non_outlier_violations.append(rec)
        iter_idx += 1
    return violating_iterations


def main(data_dct, ratio_bounds, busy_cycle_threshold, migration_lookback):
    global num_bad_pexecs, num_bad_iterations, num_bad_iterations_outliers
    pexecs_checked = 0
    for key, key_wcts in data_dct["wallclock_times"].iteritems():
        key_aperfs = data_dct["aperf_counts"][key]
        key_mperfs = data_dct["mperf_counts"][key]
        key_cycles = data_dct["core_cycle_counts"][key]
        key_outliers = data_dct["all_outliers"][key]
        assert len(key_aperfs) == len(key_mperfs) == len(key_wcts), \
            "pexec count should match"

        for pexec_idx in xrange(len(key_aperfs)):
            bad_pexec = False
            pexec_aperfs = key_aperfs[pexec_idx]
            pexec_mperfs = key_mperfs[pexec_idx]
            pexec_wcts = key_wcts[pexec_idx]
            pexec_cycles = key_cycles[pexec_idx]
            pexec_cycles = key_cycles[pexec_idx]
            pexec_outliers = key_outliers[pexec_idx]
            assert len(pexec_aperfs) == len(pexec_mperfs), \
                "core count should match for a/mperfs"

            violating_iterations_pexec = set()
            for core_idx in xrange(len(pexec_aperfs)):
                core_aperfs = pexec_aperfs[core_idx]
                core_mperfs = pexec_mperfs[core_idx]
                core_cycles = pexec_cycles[core_idx]

                violating_iterations_core = check_amperfs(
                    core_aperfs, core_mperfs, pexec_wcts, busy_cycle_threshold,
                    ratio_bounds, key, pexec_idx, core_idx, migration_lookback,
                    core_cycles, pexec_aperfs, pexec_mperfs, pexec_cycles,
                    pexec_outliers)
                violating_iterations_pexec |= violating_iterations_core
                if violating_iterations_core:
                    bad_pexec = True
            num_bad_iterations += len(violating_iterations_pexec)
            num_bad_iterations_outliers += \
                len([x for x in violating_iterations_pexec
                     if x in pexec_outliers])
            if bad_pexec:
                num_bad_pexecs += 1
            pexecs_checked += 1

    print("OUTLIER VIOLATIONS:")
    for i in outlier_violations:
        print("  " + i)

    print("NON OUTLIER VIOLATIONS:")
    for i in non_outlier_violations:
        print("  " + i)

    print("\nTotal violations (across all cores): %s" %
          (len(outlier_violations) + len(non_outlier_violations)))
    print("Of which outliers: %s" % len(outlier_violations))

    print("\nTotal violating iterations: %s" % num_bad_iterations)
    print("Of which outliers: %s" % num_bad_iterations_outliers)

    print("\n# Pexecs with violations: %s" % num_bad_pexecs)
    print("# Pexecs examined: %s" % pexecs_checked)


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print(__doc__)
        sys.exit(1)

    try:
        lo_ratio, hi_ratio = sys.argv[2].split(",")
        ratio_bounds = float(lo_ratio), float(hi_ratio)
        busy_cycle_threshold = float(sys.argv[3]) / float(sys.argv[4])
        migration_lookback = int(sys.argv[5])
    except:
        print(__doc__)
        sys.exit(1)

    data_dct = read_krun_results_file(sys.argv[1])
    main(data_dct, ratio_bounds, busy_cycle_threshold, migration_lookback)
