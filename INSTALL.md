# Installing requirements

## Mandatory requirements

  * Python 2.7 - the code here is not Python 3.x ready
  * bzip2 / bunzip2 and bzip2 (including header files)
  * curl (including header files)
  * gcc and make
  * gfortran (including header files)
  * liblzma library (including header files)
  * Python modules: numpy, pip, libcap
  * openssl (including header files)
  * pkg-config
  * pcre library (including header files)
  * R (version 3.3.1 or later)
  * readline (including header files)
  * wget
  * lsb-release (needed on Ubuntu systems)

## Optional requirements

  * PyPy (will allow some code here to run faster)
  * Python modules required for plotting: matplotlib
  * Required for generating LaTeX tables: a LaTeX distribution which provides
    pdflatex, and the following packages: amsmath, amssymb, booktabs, calc,
    geometry, mathtools, multicol, multirow, rotating, sparklines, xspace.
    The TeX Live distribution should be fine.

## Installing on Debian systems

The following command will install all (mandatory and optional) dependencies on
Debian-based systems:

```sh
$ sudo apt-get install build-essential python2.7 pypy bzip2 libssl-dev \
       pkg-config libcurl4-openssl-dev python-numpy python-matplotlib \
       python-pip texlive-latex-extra wget python2.7-dev libreadline-dev \
       libbz2-dev liblzma-dev libpcre3-dev gfortran r-base lsb-release
$ ./build.sh
```

## Setting up R

To run the scripts here, it is necessary to install R and some R packages.
To do this, just run the `build.sh` script included in this repository.

## Manually setting up R

If you prefer not to run `build.sh` you will need to install R version
3.3.1 or later R for your platform (you may need to build R manually).

By default, R will install its packages in `$HOME/R`. If you do not want R to
use your home directory, then set the environment variable `$R_LIBS_USER`,
e.g. (in BASH):

```bash
$ git clone https://github.com/softdevteam/warmup_experiment.git
$ cd warmup_experiment
$ mkdir R
$ export R_LIBS_USER=`pwd`/R
$ echo "export R_LIBS_USER=`pwd`/R" >> ~/.bashrc
```

You will then need to open R on the command line, and run the following commands:

```R
> install.packages("devtools")
```

At this point R may ask you to choose a CRAN mirror. Choose one and wait for
installation to complete.

Some Debian systems include a buggy version of R, as a work-around you may
have to execute this command:

```R
options(download.file.method = "wget")
```

Lastly, you need to run:

```R
> devtools::install_github("rkillick/changepoint")
```

When you exit the R REPL, you may be asked to 'save the workspace'. It is not
necessary to do this.
