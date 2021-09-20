Contributing
============

How to contribute to this project.

Fork this repository
--------------------

`Fork this repository before contributing`_. 

Next, clone your fork to your local machine, keep it `up to date with the upstream`_, and update the online fork with those updates.

::

    git clone https://github.com/YOUR-USERNAME/grafanarmadillo.git
    cd grafanarmadillo
    git pull origin main

Install for developers
----------------------

Create a dedicated Python environment where to develop the project.

If you are using :code:`pip` follow the official instructions on `Installing packages using pip and virtual environments`_, most likely what you want is:

::

    python3 -m venv .venv
    source .venv/bin/activate

Install the package in :code:`develop` mode, and also :ref:`tox<Uniformed Tests with tox>`.

::

    python setup.py develop
    pip install dev_requirements.txt

Make a new branch
-----------------

From the ``main`` branch create a new branch where to develop the new code.

::

    git checkout main
    git checkout -b new_branch


Develop the feature and keep regular pushes to your fork with comprehensible commit messages.

::

    git status
    git add (the files you want)
    git commit (add a nice commit message)
    git push origin new_branch

While you are developing, you can execute ``tox`` as needed to run your unittests or inspect lint, etc. See the last section of this page. If you want things to build a bit faster, you can set the pythonpath and run pytest directly.

::

    export PYTHONPATH=./src
    python3 -m pytest tests

Many of the tests will rely on a test Docker container to integrate with a Grafana instance. By default this only runs on Linux, but can be forced by setting "do_containertest" to "True"

Update CHANGELOG
~~~~~~~~~~~~~~~~

Update the changelog file under :code:`docs/CHANGELOG.rst` with an explanatory bullet list of your contribution. Add that list right after the main title and before the last version subtitle::

    Changelog
    =========

    * here goes my new additions
    * explain them shortly and well

    vX.X.X (1900-01-01)
    -------------------

Also add your name to the authors list at :code:`docs/AUTHORS.rst`.

Pull Request
~~~~~~~~~~~~

Once you are finished, you can Pull Request you additions to the main repository, and engage with the community. Please read the ``PULLREQUEST.rst`` guidelines first, you will see them when you open a PR.

**Before submitting a Pull Request, verify your development branch passes all tests as** :ref:`described bellow<Uniformed Tests with tox>` **. If you are developing new code you should also implement new test cases.**


Uniformed Tests with tox
------------------------

Thanks to `Tox`_ we can have a unified testing platform where all developers are forced to follow the same rules and, above all, all tests occur in a controlled Python environment.

With *Tox*, the testing setup can be defined in a configuration file, the `tox.ini`_, which contains all the operations that are performed during the test phase. Therefore, to run the unified test suite, developers just need to execute ``tox``, provided `tox is installed`_ in the Python environment in use.

::

    pip install tox


One of the greatest advantages of using Tox together with the :ref:`src layout<The src layout>` is that unittest actually perform on the installed source (our package) inside an isolated deployment environment. In order words, tests are performed in an environment simulating a post-installation state instead of a pre-deploy/development environment. Under this setup, there is no need, in general cases, to distribute test scripts along with the actual source, in my honest opinion - see `MANIFEST.in`_.

Before creating a Pull Request from your branch, certify that all the tests pass correctly by running:

::

    tox

These are exactly the same tests that will be performed online in the Github Actions.

Also, you can run individual environments if you wish to test only specific functionalities, for example:

::

    tox -e lint  # code style
    tox -e build  # packaging
    tox -e docs  # only builds the documentation
    tox -e prreqs  # special requirements before Pull Request
    tox -e py38


.. _tox.ini: https://github.com/lilatomic/grafanarmadillo/blob/latest/tox.ini
.. _Tox: https://tox.readthedocs.io/en/latest/
.. _tox is installed: https://tox.readthedocs.io/en/latest/install.html
.. _MANIFEST.in: https://github.com/lilatomic/grafanarmadillo/blob/main/MANIFEST.in
.. _Fork this repository before contributing: https://github.com/lilatomic/grafanarmadillo/network/members
.. _up to date with the upstream: https://gist.github.com/CristinaSolana/1885435
.. _contributions to the project: https://github.com/lilatomic/grafanarmadillo/network
.. _Gitflow Workflow: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
.. _Pull Request: https://github.com/lilatomic/grafanarmadillo/pulls
.. _PULLREQUEST.rst: https://github.com/lilatomic/grafanarmadillo/blob/main/docs/PULLREQUEST.rst
.. _1: https://git-scm.com/docs/git-merge#Documentation/git-merge.txt---no-ff
.. _2: https://stackoverflow.com/questions/9069061/what-is-the-difference-between-git-merge-and-git-merge-no-ff
.. _Installing packages using pip and virtual environments: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment
.. _Anaconda: https://www.anaconda.com/
