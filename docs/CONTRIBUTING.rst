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

`Install Pants`_.

Run lints and formatters with `pants fix lint ::`.

Run tests with `pants test ::` . Many of the tests will rely on a test Docker container to integrate with a Grafana instance. By default this only runs on Linux, but can be forced by setting "do_containertest" to "True"

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

**Before submitting a Pull Request, verify your development branch passes all tests **. If you are developing new code you should also implement new test cases.**

.. _Install Pants: https://www.pantsbuild.org/2.18/docs/getting-started/installing-pants
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
