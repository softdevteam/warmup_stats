#! /bin/sh
#
# Copyright (c) 2018 King's College London
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
echo "devtools::install_git('git://github.com/rkillick/changepoint', branch = 'master')" | R_LIBS_USER=${R_LIB_DIR} R --no-save || exit $?

# Install the rpy2 Python package.
which lsb_release > /dev/null 2>&1
if [ $? -eq 0 ]; then
    if [ "$(lsb_release -si)" = "Ubuntu" ]; then
        pip install --target "${PIP_TARGET_DIR}" "rpy2==2.8.5" || exit $?
    else
        pip install --system --target "${PIP_TARGET_DIR}" "rpy2==2.8.5" || exit $?
    fi
else
    pip install --system --target "${PIP_TARGET_DIR}" "rpy2==2.8.5" || exit $?
fi
