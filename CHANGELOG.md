Changelog
=========

## v0.7.0

### Upgrade steps

- Implementations that communicate with parties that require that SLIP packets
  are preceded by an `END` byte must set
  `config.USE_LEADING_END_BYTE` to `True`.
- Implementations that use the `Driver` class directly must update their code
  with respect to handling received data and retrieving messages.
  Use `Driver.receive()` to receive data and add it to the internal buffer.
  Use `Driver.get()` to obtain the next message.

### Breaking Changes

- Changed the default behavior of sending SLIP packets to
  no longer send a leading `END` byte.
- Removed support for Python version 3.7 and lower.
- `Driver.receive()` no longer returns a list of messages.
  Instead, use `Driver.get()` to retrieve the next message.

### New Features

- Applications can decide if SLIP packets should be preceded by
  a leading `END` byte by setting the global parameter
  `config.USE_LEADING_END_BYTE`.
- Applications that need different behavior for sending a leading
  `END` byte for different `Driver` instances can use the
  `config.use_leading_end_byte()` context manager to reliably set the behavior.

### Bug Fixes

- Solved issue [45](https://github.com/rhjdjong/SlipLib/issues/45)

### Other Changes

- The SlipLib project now uses `hatch`.
- Added release and PyPI upload automation.
- `Driver` internal: moved `ProtocolError` handling from the `receive` method to the `get` method.
- Added Python 3.13 to the testing matrix.
- Monkeypatched a .css file to work around a formatting issue for `py:property` rendering.
  See [this RTD issue](https://github.com/readthedocs/sphinx_rtd_theme/issues/1301)
- Moved configuration settings into a new `config` object in the `slip` module.

## v0.6.0

### New Features

- Added support for unbuffered byte streams in SlipStream (issue #16).

### Breaking Changes

- Deprecated direct access to wrapped bytestream (SlipStream) and socket (SlipSocket)

### Other Changes

- Updated documentation and examples


## v0.5.0

### New Features

- Made SlipWrapper and its derived classes iterable (issue #18).

## v0.4.0

### Bug Fixes

- Removed sphinx as install dependency (issue #9).
  Sphinx is only required for documentation development.

### Other Changes

- Changes in automated testing:

  - Added testing against Python 3.8.
  - Added macOS testing.
  - Removed testing against Python 3.4.

## v0.3.0

- First general available beta release.
