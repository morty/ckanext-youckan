YouCKAN CKAN extension
======================

The YouCKAN extension is a YouCKAN connector for CKAN.

NOTE: This extension has only been texted with CKAN 2.1.

Activating and Installing
-------------------------

To install the plugin, enter your virtualenv and load the source:

.. code-block:: bash

    $ pip install ckanext-youckan

Add the following to your CKAN .ini file:

.. code-block:: ini

    ckan.plugins = youckan <other-plugins>

To use YouCKAN users and authentification, set you who.ini like this:

.. code-block:: ini

    [plugin:youckan]
    use = ckanext.youckan.repozewho:plugin
    session_cookie_name = youckan_session
    auth_cookie_name = youckan_auth
    login_url = http://sso.etalab.dev/login/
    secret = YOUR_DJANGO_SECRET_KEY

    [general]
    request_classifier = repoze.who.classifiers:default_request_classifier
    challenge_decider = repoze.who.classifiers:default_challenge_decider

    [identifiers]
    plugins = youckan

    [authenticators]
    plugins = youckan

    [challengers]
    plugins = youckan

and configure the YouCKAN plugin to use authentication:

.. code-block::

    ckan.plugins = youckan <other-plugins>
    youckan.use_auth = true
    youckan.logout_url = https://youckan/logout
