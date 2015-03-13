# Literate

Literate is a simple python script for python 3 to create automated reports.

It is designed to help scientist to create reports to describe their scripts, including the printed output and figures created with matplotlib.

It employs the RestructuredText syntax to write the report, and try to be as non-intrusive as possible

## usage

i can be used as a library, imported by another script, or as a separate program:

    python literate.py yourscript.py -optionals -parameters -for -the -script

you can see an example of the results in the compiled_introduction.py directory.
For offline viewing the html file is suggested, [while for viewing online on GitHub the rst is more appropriate](https://github.com/EnricoGiampieri/literate/blob/master/compiled_introduction.py/introduction.rst).
The online visualization protocol of GitHub does not support math for rst, but with the html the visualization is correct for formulas.

## testing

the program executed without any paramters will launch the test suite, that is included in the source file (bad practice, I know)

## license

This code is under BSD license.

## origin

The concept is based on pyreport and pweave.pypublish, but takes a radically different approach.
Instead of using comments to write the report text, it uses simple multiline string.
they get converted using the docutils package, that is based on the RestructuredText syntax, and then
they get compiled as an html file for ease of presentation.

## known issues

* each figure can only be shown once, even with multiple call to the fig.show function.
* no configuration, the script work *as it it*
* the test suite is not yet complete
