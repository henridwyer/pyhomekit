PyHomeKit - Python interface to control HomeKit accessories.
============================================================

:Author: Henri Dwyer

.. image:: https://api.travis-ci.org/henridwyer/pyhomekit.png
	   :target: https://travis-ci.org/henridwyer/pyhomekit


PyHomeKit let's you control HomeKit accessories using a pythonic interface. Supports both BLE and HTTP devices.

Warning
-------

PyHomeKit is a work in progress. Many features are not yet implemented.

Installation
------------

.. code-block:: shell

    pip install pyhomekit

For development, clone the repository and:

.. code-block:: shell

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

- Python 3.6
- bluepy python package for interacting with BLE HomeKit devices.

Usage
------------------

.. code-block:: python

    import pyhomekit

    device_mac = "aa:aa:aa:aa:aa"
    device = pyhomekit.ble.HapAccessory(mac=device_mac)
    characteristics = device.discover_characteristics()

    print(characteristics)

