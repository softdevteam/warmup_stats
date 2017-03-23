import numpy

LOW_IQR_BOUND = 5.0
HIGH_IQR_BOUND = 95.0


def median_iqr(seq):
    return numpy.median(seq), (numpy.percentile(seq, LOW_IQR_BOUND), numpy.percentile(seq, HIGH_IQR_BOUND))
