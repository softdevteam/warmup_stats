#! /bin/sh

set -e

# Local directories for installing Python and R packages.
R_INST_DIR=`pwd`/work/R-inst
PIP_TARGET_DIR=`pwd`/work/pylibs

# Check requirements.
which git > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "git must be installed" >&2
    exit 1
fi

which python2.7 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "python2.7 must be installed" >&2
    exit 1
fi

python2.7 -c "import setuptools" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "setuptools for python2.7 must be installed" >&2
    exit 1
fi

which R > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "R version 3.3.1 or later must be installed"
    exit 1
fi

version() {
    echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }';
}

if [ $(version `R --version | awk 'NR==1 {print $3}'`) -le $(version "3.3.1") ]; then
    echo "R version 3.3.1 or later must be installed"
    exit 1
fi

# Install R changepoint package.
mkdir -p ${R_INST_DIR}/lib/R/library
echo "install.packages('devtools', lib='${R_INST_DIR}/lib/R/library', repos='http://cran.us.r-project.org')" | R_LIBS_USER=${R_INST_DIR}/lib/R/library/ R --no-save
echo "install.packages('MultinomialCI', lib='${R_INST_DIR}/lib/R/library', repos='http://cran.us.r-project.org')" | R_LIBS_USER=${R_INST_DIR}/lib/R/library/ R --no-save
echo "devtools::install_git('git://github.com/rkillick/changepoint', branch = 'master')" | R_LIBS_USER=${R_INST_DIR}/lib/R/library/ R --no-save

# Install rpy2 Python package.
DEB8_HACK=0
if [ -f /etc/debian_version ]; then
    DEB_MAJOR_V=`cat /etc/debian_version | cut -d. -f1`
    if [ "${DEB_MAJOR_V}" = "8" ]; then
        DEB8_HACK=1
    fi
fi

if [ "${DEB8_HACK}" = "1" ]; then
    # Debian 8
    pip install -t ${PIP_TARGET_DIR} "rpy2==2.8.5"
else
    pip install --install-option="--prefix=${PIP_TARGET_DIR}" "rpy2==2.8.5"
fi
