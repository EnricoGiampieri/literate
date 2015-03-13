# -*- coding: utf-8 -*-
"""
Introduction to literate.py
===========================
:Authors: Enrico Giampieri

*Literate.py* is a simple python library that is used to compile
normal python script into scienfic reports, with an approach
similar to that commonly refered as **literate programming**.

*Literate.py* is based on a simple idea: the isolated string
in your program get turned into the text of the report, while
the code is reported as evidenced.
The usage of long strings in python allows to write the text
in a comfortable way. The syntax used to parse the text is the
ReStructured Text, the language of markup chosen for the python
documentation.

Any output from the code is captured and printed in the report as verbatim.
It also tries its best to capture and insert any figure created with
matplotlib and pylab.


.. math::

    \lambda = x_0^2

"""

print("capture this line!")

"""The library execute the script as the main script, even if for now it
does not support any external parameters (but it is soon to come).
"""

"""if you need to insert a string literally, you can just put a semicolon ;
at the end of it. It is equivalnt from the syntax point of view, but
it will not be recognized as a piece of documentation.
"""

if __name__ == '__main__':
    print("this is inside the main loop")

"""the library should be able to distinguish regulare output (stdout)
and error output (stderr) and represent them accordingly
"""

import sys
print("capture this line!", file=sys.stderr)

"""It does not catch exceptions. Your code is supposed to work correctly.
If your code run, then it should be compiled without any problems.
Debugging an error from the sandboxed code it extremely hard,
so to discourage the practice it raises the exception without any filtering,
only with a reference to the code source that generate the error.

the proper docstrings of functions or classes are not processed right now
"""

def my_fun():
    """this function does nothing
    """
    pass

"""it can also capture matplotlib figures on the fly, maintaining all the
configurazione in the appropriate way"""

import pylab
fig, ax = pylab.subplots(1, 1, figsize=(8, 4))
x = pylab.linspace(0, 10, 101)
ax.plot(x, x**2)
fig.show()

"""if external libraries are used, they interact in the expected way
"""


#import seaborn as sns
#sns.set(style="ticks")

#df = sns.load_dataset("anscombe")
#sns.lmplot("x", "y", col="dataset", hue="dataset", data=df,
#           col_wrap=2, ci=None, palette="muted", size=4,
#           scatter_kws={"s": 50, "alpha": 1})

"""to show the plot it is necessary to explicitly call the show method,
no shortcut available!
"""
pylab.show()


"""how does it behave toward continued groups?
""";

a = False
if a:
    print('True')


else:
    print('False')




