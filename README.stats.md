# Statistical scripts and packages

The scripts in `bin/` use a number of external packages to generate statistics,
and require both Python 2 and R to be installed.

In order to generate statistics from a Krun results file (or a CSV file), you
first need to follow the instructions in `INSTALL.md`. These detail the system
packages that are required and the Python and R packages. On some OS
distributions you may need to install the required R package manually, in which
case please follow the instructions towards the end of the `INSTALL.md` file.
For most users, we hope that the `build_stats.sh` script (in the root of this
repository) can be used to automate this process.


## Working with Krun output


### Initial statistical scripts

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


### Generating tables from Krun results files

There are two scripts used for generating tables,
`bin/table_classification_summaries_main` and
`bin/table_classification_summaries_others`. The `_main` script is intended to
be used with the results of our full "warmup" experiment where a number of
different VMs were tested on a number of different benchmarks, and the `_others`
script is intended to be used with small numbers of VMs (1 or 2) and a set of
benchmarks (e.g. Da Capo, Octane, etc.).

Both script generate LaTeX code which needs to be translated to PDF (e.g. with
`pdflatex`). The largest difference between the two scripts is that `_main`
produces tables where every row is a VM (and benchmarks are grouped in blocks),
and `_other` produces tables where every row is a benchmark (and benchmarks may
be grouped by VMs, if more than one VM has been benchmarked).

The two scripts are invoked slightly differently:

```
./bin/table_classification_summaries_others --with-preamble -s 1 -o mytable.tex myresults_outliers_w200_changepoints.json.bz2
```

where `-s 1` gives the number of VMs which were benchmarked, versus:

```
./bin/table_classification_summaries_main --with-preamble -o mytable.tex myresults_outliers_w200_changepoints.json.bz2
```

The switch `--with-preamble` will generate a stand-alone LaTeX file which can be
compiled to PDF. You may wish to remove this switch if you want to copy and
paste the LaTeX output into a larger document, but you will need to provide the
relevant LaTeX packages in your own preamble.


## Generating charts from Krun results files

If you have followed the instructions in the `Initial statistical scripts`
section above, you will be able to generate plots similar to the ones you can
see in the paper "Virtual Machine Warmup Blows Hot and Cold". The plotting
script `./bin/plot_krun_results` has a large number of command-line options, but
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


### Generating charts and plots without Krun

If you did not use Krun to generate your benchmarking results, please use the
`bin/warmup_stats` script to generate tables and plots from your data, which
should be in CSV format.


### CSV format

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


### Running `warmup_stats`

For non-Krun users, the Python script `bin/warmup_stats` must be used as a
front-end to all other scripts. The script can be used to generate JSON
containing summary statistics for the input data, PDF plots or LaTeX tables.

The script also needs the names of the language and VM under test, and the
output of `uname -a` on the machine the benchmarks were run on. Example usage:

```
./bin/warmup_stats  --output-plots plots.pdf --output-json summary.json -l javascript -v V8 -u "`uname -a`" results.csv
```
