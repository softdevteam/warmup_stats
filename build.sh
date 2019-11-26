#! /bin/sh

# Build dependencies for scripts in bin/

# Local directories for installing Python and R packages.
R_LIB_DIR=`pwd`/work/rlibs
PIP_TARGET_DIR=`pwd`/work/pylibs

# Check requirements.
which git > /dev/null 2>&1
if [ $? != 0 ]; then
    echo "git must be installed" >&2
    exit 1
fi

which python2.7 > /dev/null 2>&1
if [ $? != 0 ]; then
    echo "python2.7 must be installed" >&2
    exit 1
fi

python2.7 -c "import setuptools" > /dev/null 2>&1
if [ $? != 0 ]; then
    echo "setuptools for python2.7 must be installed" >&2
    exit 1
fi

which R > /dev/null 2>&1
if [ $? != 0 ]; then
    echo "R version 3.3.1 or later must be installed"
    exit 1
fi

version() {
    echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }'
}

if [ $(($(version "$(R --version | awk 'NR==1 {print $3}')") <= $(version "3.3.1"))) = 1 ]; then
    echo "R version 3.3.1 or later must be installed"
    exit 1
fi

# Install R changepoint package.
mkdir -p ${R_LIB_DIR} || exit $?
echo "install.packages('devtools', lib='${R_LIB_DIR}', repos='http://cran.us.r-project.org')" | R_LIBS_USER=${R_LIB_DIR} R --no-save || exit $?
echo "install.packages('MultinomialCI', lib='${R_LIB_DIR}', repos='http://cran.us.r-project.org')" | R_LIBS_USER=${R_LIB_DIR} R --no-save || exit $?
echo "install.packages('dplyr', lib='${R_LIB_DIR}', repos='http://cran.us.r-project.org')" | R_LIBS_USER=${R_LIB_DIR} R --no-save || exit $?
echo "install.packages('fs', lib='${R_LIB_DIR}', repos='http://cran.us.r-project.org')" | R_LIBS_USER=${R_LIB_DIR} R --no-save || exit $?
echo "devtools::install_git('git://github.com/rkillick/changepoint', branch = 'master')" | R_LIBS_USER=${R_LIB_DIR} R --no-save || exit $?

# Install the rpy2 Python package.
which lsb_release > /dev/null 2>&1
if [ $? -eq 0 ]; then
    if [ "$(lsb_release -si)" = "Ubuntu" ]; then
        python2.7 -m pip install --target "${PIP_TARGET_DIR}" "rpy2==2.8.5" || exit $?
    else
        python2.7 -m pip install --system --target "${PIP_TARGET_DIR}" "rpy2==2.8.5" || exit $?
    fi
else
    python2.7 -m pip install --system --target "${PIP_TARGET_DIR}" "rpy2==2.8.5" || exit $?
fi
