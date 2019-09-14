# Installing requirements

## Mandatory requirements

  * Python 2.7 - the code here is not Python 3.x ready
  * bzip2 / bunzip2 and bzip2 (including header files)
  * curl (including header files)
  * gcc and make
  * gfortran (including header files)
  * liblzma library (including header files)
  * Python modules: numpy, pip, libpcap
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

## Building this software

Simply execute `./build.sh` in order to build the necessary local dependencies
for `warmup_stats`.
