#! /bin/sh

# Simple tests for Travis-CI.

set -e

./bin/mark_outliers_in_json -w 200 test/example1.json.bz2
./bin/mark_outliers_in_json -w 200 test/example2.json.bz2
./bin/mark_changepoints_in_json -s 1500 test/example1_outliers_w200.json.bz2
./bin/mark_changepoints_in_json -s 1500 test/example2_outliers_w200.json.bz2
./bin/plot_krun_results --with-outliers --with-changepoints test/example1_outliers_w200_changepoints.json.bz2 -o test/plots1.pdf
./bin/plot_krun_results --with-outliers --with-changepoints test/example2_outliers_w200_changepoints.json.bz2 -o test/plots2.pdf
./bin/table_classification_summaries_others test/example1_outliers_w200_changepoints.json.bz2 -o test/table1.tex
./bin/table_classification_summaries_others test/example2_outliers_w200_changepoints.json.bz2 -o test/table2.tex
./bin/diff_results -r test/example1_outliers_w200_changepoints.json.bz2 test/example2_outliers_w200_changepoints.json.bz2 --tex test/diff.tex
