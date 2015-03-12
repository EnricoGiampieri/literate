# -*- coding: utf-8 -*-
"""
Introduction to literate.py
===========================
:Authors: Enrico Giampieri

Literate.py is a simple python library that is used to compile
normal python script into scienfic reports, with an approach
similar to that commonly refered as **literate programming**.

.. math::

    \lambda = x_0^2

"""

print("capture this line!")

import pylab
fig, ax = pylab.subplots(1, 1, figsize=(8, 4))
x = pylab.linspace(0, 10, 101)
ax.plot(x, x**2)
fig.show()
