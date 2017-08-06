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

Connect to a HAP characteristics and view its signature:

.. code-block:: python

    import pyhomekit
    import bluepy

    device_mac = "aa:aa:aa:aa:aa"

    characteristic_uuid = "00000000-0000-0000-0000-000000000000"

    device = bluepy.btle.Peripheral()
    device.connect(device_mac)
    bluepy_characteristic = device.getCharacteristics(uuid=characteristic_uuid)[0]

    hap_characteristic = pyhomekit.ble.HapCharacteristic(bluepy_characteristic)

    print(hap_characteristic.signature)

View the debug logs in stdout:

.. code-block:: python

    import logging

    logging.basicConfig()
    logging.getLogger('pyhomekit').setLevel(logging.DEBUG)


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
