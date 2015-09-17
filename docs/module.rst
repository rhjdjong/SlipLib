Module contents
===============

.. module:: slip

The module :mod:`slip` exports the following elements.

Exceptions
^^^^^^^^^^

.. autoexception:: slip.SlipDecodingError

Constants
^^^^^^^^^

.. data:: END
          ESC
          ESC_END
          ESC_ESC
          
   These constants represent the byte values for the
   special SLIP bytes.
   
Functions
^^^^^^^^^

.. function:: slip.encode(obj)

   Encode a message (*obj*) as a SLIP packet.
   *obj* must be an iterable that produces byte values.
   Returns a :code:`bytes` object

.. function:: slip.decode(obj)

   Decode a SLIP packet (*obj*) into a message.
   Returns a :code:`bytes` object.
   Raises :exc:`SlipDecodingError` when the slip packet *obj* cannot be decoded.


