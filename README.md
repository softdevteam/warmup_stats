# warmup_stats

This system has various scripts for analysing the output of VM benchmarking. Any
system can be used to perform the benchmarking (e.g. Krun
http://soft-dev.org/src/krun/).


# Installation

First run the `build.sh` script which should perform most, if not all, of the
installation work needed.


# Basic usage

Krun users should see later in this README, but for non-Krun users, the main
interface is the `bin/warmup_stats` script which takes in files and produces
various types of plots and tables.

## CSV format

The `bin/warmup_stats` script takes CSV files as input. The format is as
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


## Creating plots

The `--output-plots <file.pdf>` flag converts input data into visual plots.
`bin/warmup_stats` also needs the names of the language and VM under test, and
the output of `uname -a` on the machine the benchmarks were run on. Example
usage:

```
./bin/warmup_stats  --output-plots plots.pdf --output-json summary.json -l javascript -v V8 -u "`uname -a`" results.csv
```


# Warmup stats from Krun

## Initial statistical scripts

Before generating tables or charts from your Krun data, you will need to run two
scripts to add *outliers* and *changepoints* to your data.

To add outliers to your Krun output, run:

```
./bin/mark_outliers_in_json -w 200 myresults.json.bz2
```

`-w` gives the size of the sliding window used to draw percentiles. We recommend
that you set this to 0.1 * the number of in-process iterations in each process
execution of your benchmarks (for example, we used 2000 iterations and a window
size of 200).

This script will generate a new Krun output file called
`myresults_outliers_w200.json.bz2`.

To add changepoints to your Krun output, run:

```
./bin/mark_changepoints_in_json -s 500 myresults_outliers_200.json.bz2
```

Note that we run this script **on the output of the `mark_outliers` script**.

In the example invocation above, we stated `-s 500` which tells the script to
expect that the VM will reach a steady state should be reached before the last
500 in-process iterations. We recommend that this value be set at 0.25 * the
number of in-process iterations in each process execution of your benchmarks
(for example, we used 2000 iterations and a `-s` value of 500).

The invocation of this script shown above will generate a new Krun results file
called `myresults_outliers_w200_changepoints.json.bz2`. When generating tables
and plots, this is the version of your results that should be passed to the
tabling or plotting scripts.


## Generating tables from Krun results files

`bin/table_classification_summaries_others` plots summary tables with various
statistics, and is useful for getting an overall view of a VM(s) performance.
An example run is as follows:

```
bin/table_classification_summaries_others -s 1 -o mytable.tex myresults_outliers_w200_changepoints.json.bz2
```

where `-s 1` gives the number of VMs which were benchmarked. By default, the
script will generate a stand-alone LaTeX file which can be compiled to PDF
with `pdflatex`, or similar. If you want to copy and paste the LaTeX output into
a larger document, use the `--without-preamble`, and provide the relevant LaTeX
packages in your own preamble.


## Generating charts from Krun results files

If you have followed the instructions in the `Initial statistical scripts`
section above, you will be able to generate plots similar to the ones you can
see in the paper "Virtual Machine Warmup Blows Hot and Cold". The plotting
script `bin/plot_krun_results` has a large number of command-line options, but
will commonly be invoked as follows:

```
./bin/plot_krun_results --with-outliers --with-changepoint-means -w 200 -o myplots.pdf myresults_outliers_200.json.bz2
```

If you need more tailored output, it is wise to run
`./bin/plot_krun_results --help` and read through the options. There are a large
number of switches to this script, but ones that users are most likely to need
are:

  * `-b` to generate only a few plots from a larger data set
  * `--export-size` to resize plots for publication
  * `--wallclock-only` to suppress most details
  * `--xlimits` and `--inset-xlimits` to "zoom in" on parts of the x-axis


## Diffing Krun results files

Benchmarking is often performed in order to test whether a change in a given
VM improves or worsens its performance. Unfortunately, the difference between
benchmark performance before and after a change is rarely simple. Users will
want to produce a detailed comparison of the results in Krun results tables
(above) in order to get a deeper insight into the effects of their changes.

The `bin/diff_results` scripts takes two Krun results files as an input and
produces a LaTeX file (which can be compiled to PDF with pdflatex or similar)
as output:

```
./bin/diff_results -r BEFORE.json.bz2 AFTER.json.bz2 -o diff.tex -n 1
```

The `-n` should normally be set to the number of VMs that were benchmarked
(this switch controls the number of columns in the table).

The resulting LaTeX table will contain results from the `AFTER.json.bz2` file,
compared against the `BEFORE.json.bz2` file. VMs and benchmarks that do not
appear in both Krun results files will be omitted from the table.
