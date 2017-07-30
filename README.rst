PyHomeKit - HomeKit for Python
==============================

:Author: Henri Dwyer

.. image:: https://api.travis-ci.org/henridwyer/pyhomekit.png
	   :target: https://travis-ci.org/henridwyer/pyhomekit
.. image:: http://img.shields.io/pypi/v/pyhomekit.svg
   :target: https://pypi.python.org/pypi/pyhomekit
   :alt: Latest Version
.. image:: https://img.shields.io/pypi/pyversions/pyhomekit.svg
   :target: https://pypi.python.org/pypi/pyhomekit
   :alt: Python Versions

PyHomeKit is a set of python libraries that let you control HomeKit compatible accessories, both BLE and HTTP.

For more information about HomeKit, see the `Apple Developper HomeKit <https://developer.apple.com/homekit/>`_ page.

Bluetooth Low Energy device compatibility is provided by `bluepy <https://ianharvey.github.io/bluepy-doc/>`_, which uses bluez.

.. important:: PyHomeKit is currently in pre-alpha. Many features are not yet implemented or broken.

Getting Started
+++++++++++++++

Usage
------------------

Connect to a HAP accessory view its HAP characteristics:

.. code-block:: python

    import pyhomekit

    device_mac = "aa:aa:aa:aa:aa"
    device = pyhomekit.ble.HapAccessory(mac=device_mac)
    characteristics = device.discover_characteristics()

    print(characteristics)

Interact with HAP characteristics:

.. code-block:: python

    # View the value of a characteristic
    device.lock_target_state()
    >>> 0

    # Set the value of a characteristic
    device.lock_target_state(value=1)

Installation
------------

``pyHomeKit`` is on Pypi, so you can ``pip`` install it:

.. code-block:: shell

    pip install pyhomekit

If you want to install from source, clone the repository:

.. code-block:: shell

    git clone git://github.com/henridwyer/pyhomekit.git
    cd pyhomekit
    pip install -r requirements.txt
    pip install -e .

Then you can build the documentation: 

.. code-block:: shell

    make doc

And run the tests:

.. code-block:: shell

    make tests

Requirements
############

pyHomeKit is only compatible with python 3.6 for the moment.
