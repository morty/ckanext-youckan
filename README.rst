YouCKAN CKAN extension
======================

The YouCKAN extension is a YouCKAN connector for CKAN.

NOTE: This extension requires ckan version 1.7 or higher.

Activating and Installing
-------------------------

To install the plugin, enter your virtualenv and load the source:

.. code-block:: bash

    $ pip install ckanext-youckan

Add the following to your CKAN .ini file:

.. code-block:: ini

    ckan.plugins = youckan oauth2 <other-plugins>
