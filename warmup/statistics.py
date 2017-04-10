import numpy
import os
import subprocess
import traceback


LOW_IQR_BOUND = 5.0
HIGH_IQR_BOUND = 95.0

BOOTSTRAPPER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'warmup', 'bootstrapper.py')


def median_iqr(seq):
    return numpy.median(seq), (numpy.percentile(seq, LOW_IQR_BOUND), numpy.percentile(seq, HIGH_IQR_BOUND))


def bootstrap_runner(marshalled_data):
    """Input should be a JSON string, containing a list of pexecs, each
    containing a list of segments, each containing a list of floats.
    """

    try:
        pipe = subprocess.Popen(['pypy', BOOTSTRAPPER], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        pipe.stdin.write(marshalled_data + '\n')
        pipe.stdin.flush()
        output = pipe.stdout.readline().strip()
        mean_str, ci_str =  output.split(',')
        mean, ci = float(mean_str), float(ci_str)
        return mean, ci
    except:
        print 'Bootstrapper script failed:'
        traceback.print_exc()
        return None, None
