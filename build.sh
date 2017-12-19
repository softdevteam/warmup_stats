#! /bin/sh

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

set -e

HERE_DIR=$(dirname $(readlink -f "$0"))
R_INST_DIR=${HERE_DIR}/work/R-inst
PIP_TARGET_DIR=${HERE_DIR}/work/pylibs
mkdir -p ${R_INST_DIR}

# Download a recent version of R (must be 3.3.1 or later).
cd work
wget https://cran.r-project.org/src/base/R-3/R-3.3.2.tar.gz
tar -xzf R-3.3.2.tar.gz
rm R-3.3.2.tar.gz
cd R-3.3.2

# Build R.
./configure --prefix=${R_INST_DIR} --enable-R-shlib
make
make install
cd ..
rm -Rf R-3.3.2/
cd ..

# Correct PATH and LD_LIBRARY_PATH variables.
export PATH=${R_INST_DIR}/bin:${PATH}
export LD_LIBRARY_PATH=${R_INST_DIR}/lib/R/lib:${LD_LIBRARY_PATH}

# Install R changepoint package.
echo "install.packages('devtools', lib='${R_INST_DIR}/lib/R/library', repos='http://cran.us.r-project.org')" | R_LIBS_USER=${R_INST_DIR}/lib/R/library/ ${R_INST_DIR}/bin/R --no-save
echo "install.packages('MultinomialCI', lib='${R_INST_DIR}/lib/R/library', repos='http://cran.us.r-project.org')" | R_LIBS_USER=${R_INST_DIR}/lib/R/library/ ${R_INST_DIR}/bin/R --no-save
echo "options(download.file.method = \"wget\"); devtools::install_github('rkillick/changepoint')" | R_LIBS_USER=${R_INST_DIR}/lib/R/library/ ${R_INST_DIR}/bin/R --no-save

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
    pip install -t ${PIP_TARGET_DIR} rpy2==2.8.5
else
    pip install --install-option="--prefix=${PIP_TARGET_DIR}" rpy2==2.8.5
fi
