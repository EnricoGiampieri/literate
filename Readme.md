# Literate

Literate is a simple python script for python 3 to create automated reports.

It is designed to help scientist to create reports to describe their scripts, including the code, resulting output and figures created with matplotlib.

It employs the RestructuredText syntax to write the report, and try to be as non-intrusive as possible.

The script is executed in a sandbox (or as close as possible to a proper sandbox) that capture all the output to terminal or plot.
From this it does create a Restructured Text file and a series of images.
The rst is then compiled to a static html file.
All the resulting files are stored in a directory in the same location of the script to be analyzed, with the same name fo the script with **compiled** as prefix.

## Usage

i can be used as a library, imported by another script, or as a separate program:

    python literate.py yourscript.py -optionals -parameters -for -the -script

you can see an example of the results in the compiled_introduction.py directory.
For offline viewing the html file is suggested, [while for viewing online on GitHub the rst is more appropriate](https://github.com/EnricoGiampieri/literate/blob/master/compiled_introduction.py/introduction.rst).
The online visualization protocol of GitHub does not support math for rst, but with the html the visualization is correct for formulas.

## Testing

the program executed without any paramters will launch the test suite, that is included in the source file (bad practice, I know)

## Licensing

This code is under BSD license.

## Rationale
The aim of this library is to give python programmers a tool vaguely corresponding to the PUBLISH function of MATLAB, but with more smartness and using a more cool language!

Right now for the python scientific environment the two main tools for literate programming are pweave and the IPyhton notebook.
Both are exceptional tools, but they do not respond to the requirements of my usual workflow, and I think that I'm not the only one left unsatisfied by those approaches.

### Pweave
PWeave use a specific file format that is not a python executable. To obtain a script the file has to be pre-preocessed with a **Tangle** procedure, while the text for the documentation should be generated
with a **Weave** procedure. This approach is powerful to write an article that contains some code in it, but I find it very uncomfortable to the first phase ot development, when modifying the code
should be as fast and painless as possible.

The cost of opportunity of using this instrument is noticeable, and that is why **Literate** tries to get in your way as little as possible.
Code as much as you want, write the notes as you go as simple docstrings and in the end compile it all.

### IPython notebook

The IPython Notebook (or Jupyter notebook, as they are called right now) are an amazing tool for everyday hacking, but keeping them in order can be hard, and they are prone to chaos if not properly managed.
They also require the programmer to go to an environment that is not comfortable for everyone.


## Origin

The concept is based on pyreport and pweave.pypublish, but takes a radically different approach.
Instead of using comments to write the report text, it uses simple multiline string.
they get converted using the docutils package, that is based on the RestructuredText syntax, and then
they get compiled as an html file for ease of presentation.

## Known issues

* each figure can only be shown once, even with multiple call to the fig.show function.
* no configuration, the script work *as it is*
* the test suite is not yet complete
* it should intercept also savefigs commands from pylab
