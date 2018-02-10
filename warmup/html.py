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

import math
import numpy


def html_histogram(data, nth):
    """HTML version of the LaTeX Sparkline histograms."""
    histogram, bin_edges = numpy.histogram(data, bins=10)
    total = math.fsum(histogram)
    median_index = int(math.floor(len(data) / 2.0))
    cum_freq = 0  # Cumulative frequency.
    normed = [value / total for value in histogram]
    for index, bin_value in enumerate(histogram):
        cum_freq += bin_value
        if cum_freq >= median_index:
            median_bin_index = index
            break
    data_s = "[ ['bin', 'value', { role: 'style' } ],\n"
    for index, value in enumerate(normed):
        colour = 'black'
        if index == median_bin_index:
            colour = 'red'
        data_s += "['%d', %.3f, '%s'], " % (index, value, colour)
    data_s += "]"
    return """
<script type="text/javascript">
google.charts.setOnLoadCallback(draw_chart%d);
function draw_chart%d() {
    var data = google.visualization.arrayToDataTable(%s);
    var view = new google.visualization.DataView(data);
    var options = { width: 100,
                    height: 70,
                    bars: 'vertical',
                    legend: { position: 'none' },
                    backgroundColor: 'transparent',
                    hAxis: { title: '',
                             gridlines: { count: 0 },
                             textPosition: 'none',
                           },
                    vAxis: { title: '',
                             viewWindowMode: 'explicit',
                             viewWindow: { min: 0.0, max: 1.1, },
                             gridlines: { count: 0 },
                             textPosition: 'none',
                           },
                  };
    var chart = new google.visualization.ColumnChart(document.getElementById("bar%d"));
    chart.draw(view, options);}
</script>
""" % (nth, nth, data_s, nth)


HTML_TABLE_TEMPLATE = """<h2>Results for %s</h2>
<table>
<tr>
<th>Benchmark</th>
<th>Classification</th>
<th>Steady iteration (&#35;)</th>
<th>Steady iteration (secs)</th>
<th>Steady performance (secs)</th>
</tr>
%s
</table>
"""  # VM name, table rows.


HTML_PAGE_TEMPLATE = """<html>
<head>
<title>Benchmark results</title>
<style>
body               { background-color: white;
                     border-collapse: collapse; }
table              { width: 100%%;
                     vertical-align: middle;
                     valign: middle;
                     text-align: left; }
td                 { white-space: nowrap;
                     height: 70px;
                     padding: 0px;
                     margin: 0px; }
th                 { background-color: black;
                     color: white;
                     text-align: center;
                     padding: 0px;
                     margin: 0px; }
tr                 { height: 70px;
                     margin: 0px;
                     padding: 0px; }
tr:nth-child(even) { background-color: #f2f2f2; }
.tdtext {
    height: 70px;
    padding: 0px;
    clear: right;
    vertical-align: middle;
    valign: middle;
    margin: 0px;
    display: block;
}
.histogram {
    height: 70px;
    width: 100px;
    float: left;
    clear: both;
    vertical-align: middle;
    valign: middle;
    margin: 0px;
    padding: 0px;
}
#lightred          { background-color: #e88a8a; }
#lightyellow       { background-color: #e8e58a; }
#lightgreen        { background-color: #8ae89c; }
</style>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">
google.charts.load('current', {'packages':['corechart']});
</script>
</head>
<body>
<h1>Benchmark results</h1>
%s
</body>
</html>
"""  # Strings from HTML_TABLE_TEMPLATE.


DIFF_LEGEND = """
<p>
<strong>Diff against previous results:</strong>
<span id="lightgreen">improved</span>
<span id="lightred">worsened</span>
<span id="lightyellow">different</span>
<span>unchanged.</span>
</p>
"""
