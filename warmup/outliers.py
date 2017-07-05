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

"""Outlier calculations.
These functions are designed to be executed by PyPy, and may run slowly with
other VMs.
"""

import math


def _clamp_window_size(index, data_size, window_size=200):
    """Return the window of data which should be used to calculate a moving
    window percentile or average. Clamped to the 0th and (len-1)th indices
    of the sequence.

    E.g.
    _clamp_window_size(50, 1000, 200)  == (0,   150)
    _clamp_window_size(300, 1000, 200) == (200, 400)
    _clamp_window_size(950, 1000, 200) == (850, 1000)
    """
    half_window = window_size / 2
    lh_index = 0 if (index - half_window) < 0 else index - half_window
    rh_index = data_size if (index + half_window) > data_size else index + half_window
    return (lh_index, rh_index)


def _no_first_window_get_window(index, window_size, data):
    """Calculate indices of window, ignore windows that do not have a full set
    of data at the start of the run sequence..
    """
    l_slice, r_slice = _clamp_window_size(index, len(data), window_size)
    if l_slice == 0 and r_slice < window_size:
        return []
    window = data[l_slice:r_slice]
    return window


def get_window(index, window_size, data):
    return _no_first_window_get_window(index, window_size, data)


def _tukey_all_outliers(data, window_size):
    """Use a formula from Tukey to find all outliers in a run sequence.
    An outlier is defined to be a data point outside the range:
        median +/- 3 * (90th percentile - 10th percentile)
    """
    all_outliers = list()
    size = len(data)
    for index, datum in enumerate(data):
        l_slice, r_slice = _clamp_window_size(index, size, window_size)
        if l_slice == 0 and r_slice < window_size:
            continue
        window = data[l_slice:r_slice]
        window_sorted = sorted(window)
        window_median = median(window_sorted)
        pc_band = 3 * (percentile(window_sorted, 90.0) - percentile(window_sorted, 10.0))
        if datum > (window_median + pc_band) or datum < (window_median - pc_band):
            all_outliers.append(index)
    return all_outliers


def get_all_outliers(data, window_size):
    return _tukey_all_outliers(data, window_size)


def get_outliers(all_outliers, window_size, threshold=1):
    """Return 'common' and 'unique' outliers.
    """
    common, unique = list(), list()
    for index, outliers in enumerate(all_outliers):
        common_exec = list()
        unique_exec = list()
        for outlier in outliers:
            other_execs = all_outliers[:index] + all_outliers[(index + 1):]
            sum_ = 0
            for execution in other_execs:
                if outlier in execution:
                    sum_ += 1
            if sum_ >= threshold:
                common_exec.append(outlier)
            else:
                unique_exec.append(outlier)
        common.append(common_exec)
        unique.append(unique_exec)
    return common, unique


def median(data):
    """Naive algorithm to compute the median of a list of (sorted) data.
    Linear interpolation is used when the percentile lies between two data
    points. It is assumed that the data contains no NaN or similar.
    This function is identical to percentile(data, 50) but faster.
    """
    size = len(data)
    if size == 0:
        raise ValueError('Cannot compute percentile of empty list!')
    if size == 1:
        return data[0]
    index = (size - 1) // 2
    if size % 2 == 1:
        return data[index]
    else:
        return (data[index] + data[index + 1]) / 2.0


def percentile(data, pc):
    """Naive algorithm to compute the pc'th percentile of a list of (sorted) data.
    Linear interpolation is used when the percentile lies between two data
    points. It is assumed that the data contains no NaN or similar.
    """
    if pc < 0 or pc > 100:
        raise ValueError('Percentile must be in the range [0, 100].')
    size = len(data)
    if size == 0:
        raise ValueError('Cannot compute percentile of empty list!')
    if size == 1:
        return data[0]
    index = (size - 1) * (pc / 100.0)
    index_floor = math.floor(index)
    index_ceil = math.ceil(index)
    if index_floor == index_ceil:
        return data[int(index)]
    d0 = data[int(index_floor)] * (index_ceil - index)
    d1 = data[int(index_ceil)] * (index - index_floor)
    return d0 + d1
