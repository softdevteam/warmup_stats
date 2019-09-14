# warmup_stats

This system has various scripts for analysing the output of VM benchmarking. Any
system can be used to perform the benchmarking, e.g.
[Krun](http://soft-dev.org/src/krun/).

# Build

Run `./build.sh` to build warmup_stats.

# Basic usage

User should directly call the `bin/warmup_stats`, which is a front-end to other
scripts in `bin/`. `warmup_stats` takes either CSV files or
[Krun](http://soft-dev.org/src/krun/) results files as input. As output it can
create HTML or LaTeX / PDF tables and diffs, or PDF plots.

## Terminology

warmup_stats uses the following terminology:

  * A *process execution* is the execution of a single operating system
    process. In other words, it is equivalent to running a program from the
    command-line and waiting for it to terminate.

  * An *in-process iteration* is a single iteration of a benchmark within a
    process execution. In other words, a single process execution executes
    many in-process iterations.

## CSV format

The `bin/warmup_stats` script can take CSV files as input. The format is as
follows. The first row must contain a header with a process execution id,
benchmark name and sequence of iteration numbers. Subsequent rows are data rows,
one per process execution. Each row should contain an index for the given
process execution, the benchmark name and a list of times in seconds for the
corresponding in-process iteration. Each process execution must execute the same
number of iterations as described in the header. For example:

```
    process_exec_num, bench_name, 0, 1, 2, ...
    0, spectral norm, 0.2, 0.1, 0.4, ...
    1, spectral norm, 0.3, 0.15, 0.2, ...
```

When processing CSV files with `warmup_stats`, the `--language`, `--vm` and
`--uname` switches must be passed to the script. These are not needed with
Krun results files.

## Creating plots

The `--output-plots <file.pdf>` flag converts input data into visual plots.

If the input files are in CSV format, `bin/warmup_stats` also needs the names of
the language and VM under test, and the output of `uname -a` on the machine the
benchmarks were run on.

Example usage:

```sh
bin/warmup_stats  --output-plots plots.pdf --output-json summary.json -l javascript -v V8 -u "`uname -a`" results.csv
bin/warmup_stats  --output-plots plots.pdf --output-json summary.json results.json.bz2
```

## Creating tables

The `--output-table <file>` flag converts input data into an HTML table or a
LaTeX / PDF table. Conversion to PDF requires `pdflatex` to be installed.

If the input files are in CSV format, `bin/warmup_stats` also needs the names of
the language and VM under test, and the output of `uname -a` on the machine the
benchmarks were run on.

Example usage (LaTeX / PDF):

```sh
bin/warmup_stats --tex --output-table table.tex -l javascript -v V8 -u "`uname -a`" results.csv
bin/warmup_stats --tex --output-table table.tex results.json.bz2
```

Example usage (HTML):

```sh
bin/warmup_stats --html --output-table table.html -l javascript -v V8 -u "`uname -a`" results.csv
bin/warmup_stats --html --output-table table.html results.json.bz2
```

By default, `warmup_stats` produces high quality statistics, which can take
considerable time. If you want to quickly experiment with things, you can use
the `--quality low` switch: this makes `warmup_stats` run considerably quicker,
but does lead to lower quality (and thus less reliable) statistics being
produced. Although the differences are often fairly minor, we do not encourage
the use of `--quality low` when formally publishing benchmark results.

## Creating diffs

Benchmarking is often performed in order to test whether a change in a given
VM improves or worsens its performance. Unfortunately, the difference between
benchmark performance before and after a change is rarely simple. Users will
want to produce a detailed comparison of the results in Krun results tables
(above) in order to get a deeper insight into the effects of their changes.

The `--output-diff` flag converts data from exactly two CSV files into an HTML
table or a LaTeX / PDF table. Conversion to PDF requires `pdflatex` to be
installed.

If the input files are in CSV format, `bin/warmup_stats` also needs the names of
the language and VM under test, and the output of `uname -a` on the machine the
benchmarks were run on.

Example usage (LaTeX / PDF):

```sh
bin/warmup_stats --tex --output-diff diff.tex -l javascript -v V8 -u "`uname -a`" before.csv after.csv
bin/warmup_stats --tex --output-diff diff.tex before.json.bz2 after.json.bz2
```

Example usage (HTML):

```sh
bin/warmup_stats --html --output-diff diff.html -l javascript -v V8 -u "`uname -a`" before.csv after.csv
bin/warmup_stats --html --output-diff diff.html before.json.bz2 after.json.bz2
```

The resulting table will contain results from the `after.{csv,json.bz2}` file,
compared against the `before.{csv,json.bz2}` file. VMs and benchmarks that do
not appear in both CSV results files will be omitted from the table.
