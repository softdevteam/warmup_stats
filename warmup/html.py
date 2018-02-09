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
table              { width: 100%%; }
td                 { white-space: pre-wrap;
                     word-wrap: break-word;
                     text-align: left;
                     padding: 8px; }
th                 { background-color: black;
                     color: white;
                     text-align: left;
                     padding: 8px; }
tr:nth-child(even) { background-color: #f2f2f2; }
#lightred          { background-color: #e88a8a; }
#lightyellow       { background-color: #e8e58a; }
#lightgreen        { background-color: #8ae89c; }
</style>
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
