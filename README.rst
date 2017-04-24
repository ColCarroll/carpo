|Build Status| |Coverage Status|

========
Carpo
========


*An irregular satellite of Jupyter.*

A command line utility to run, profile, and save Jupyter notebooks.

Installation
============
Carpo may be installed `from pypi <https://pypi.python.org/pypi/carpo>`_:
::

    pip install carpo

Tested against python 2.7, 3.4, 3.5, 3.6.

Quickstart
==========
Use
::

    carpo run path/to_notebook.ipynb

to run a notebook.
::

    carpo show path/to_notebook.ipynb

will show data from past runs.


More depth
==========
Carpo plays nicely with shell expansion:

.. image:: https://colindcarroll.com/img/carpo/carpo_show.png

Carpo has gives helpful messages when successfully running notebooks:

.. image:: https://colindcarroll.com/img/carpo/carpo_run.png

Carpo shows the cell and the error when a run fails:

.. image:: https://colindcarroll.com/img/carpo/carpo_error.png

Also, carpo plays nicely with git, and will remember if a notebook has been run:

.. image:: https://colindcarroll.com/img/carpo/carpo_git.png


Help
=====
Includes help messages:
::

  $ carpo --help
  Usage: carpo [OPTIONS] COMMAND [ARGS]...

    Base for cli commands.

  Options:
    --help  Show this message and exit.

  Commands:
    run   Try to re-run all notebooks.
    show  View status of notebooks


.. |Build Status| image:: https://travis-ci.org/ColCarroll/carpo.svg?branch=master
   :target: https://travis-ci.org/ColCarroll/carpo
.. |Coverage Status| image:: https://coveralls.io/repos/github/ColCarroll/carpo/badge.svg?branch=master
   :target: https://coveralls.io/github/ColCarroll/carpo?branch=master
