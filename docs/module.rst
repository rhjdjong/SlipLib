.. Copyright (c) 2017 Ruud de Jong
   This file is part of the SlipLib project which is released under the MIT license.
   See https://github.com/rhjdjong/SlipLib for details.

.. automodule:: sliplib

Module contents
===============

Constants
---------

.. data:: END
.. data:: ESC
.. data:: ESC_END
.. data:: ESC_ESC

   These constants represent the special bytes
   used by SLIP for delimiting and encoding messages.

Functions
---------

The following are lower-level functions, that should normally not be used directly.

.. autofunction:: encode
.. autofunction:: decode
.. autofunction:: is_valid

Classes
-------

.. autoclass:: Driver

   Class :class:`Driver` offers the following methods:

   .. automethod:: send
   .. automethod:: receive

   To enable recovery from a :exc:`ProtocolError`, the
   :class:`Driver` class offers the following attribute and method:

   .. autoattribute:: messages
   .. automethod:: flush

.. autoclass:: SlipWrapper

   Class :class:`SlipWrapper` offers the following methods and attributes:

   .. automethod:: send_msg
   .. automethod:: recv_msg

   .. attribute:: driver

      The :class:`SlipWrapper`'s :class:`Driver` instance.

   .. attribute:: stream

      The :class:`SlipWrapper`'s :class:`stream` instance.

   In addition, :class:`SlipWrapper` requires that derived classes implement the following methods:

   .. automethod:: send_bytes
   .. automethod:: recv_bytes



.. autoclass:: SlipStream(stream)
   :show-inheritance:


.. autoclass:: SlipSocket(sock)
   :show-inheritance:

   Class :class:`SlipSocket` offers the following methods in addition to the methods
   offered by its base class :class:`SlipWrapper`:

   .. automethod:: create_connection

   A :class:`SlipSocket` instance has the following attributes in addition to the attributes
   offered by its base class :class:`SlipWrapper`:

   .. attribute:: socket

      The :class:`SlipSocket`'s :class:`socket` instance.
      This is actually just an alias for the :attr:`stream` attribute in the base class.


.. autoclass:: SlipRequestHandler
   :show-inheritance:

Exceptions
----------

.. autoexception:: ProtocolError
