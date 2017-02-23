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
tr:nth-child(even) { background-color: "#f2f2f2"; }
</style>
</head>
<body>
<h1>Benchmark results</h1>
%s
</body>
</html>
"""  # Strings from HTML_TABLE_TEMPLATE.
