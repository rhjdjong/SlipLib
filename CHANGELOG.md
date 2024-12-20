Changelog
=========

## Unpublished

### Upgrade steps

- Implementations that use the `Driver` class directly must update their code
  with respect to handling received data and retrieving messages.
  Use `Driver.receive()` to receive data and add it to the internal buffer.
  Use `Driver.get()` to obtain the next message.

### Breaking Changes

- Removed support for Python version 3.6 and lower.
- `Driver.receive()` no longer returns a list of messages.
  Instead, use `Driver.get()` to retrieve the next message.

### New Features

### Bug Fixes

### Improvements

### Other Changes

- Converted project to use `hatch`.
- Added release and PyPI upload automation.
- `Driver` internal: moved `ProtocolError` handling from the `receive` method to the `get` method.
- Added Python 3.13 to the testing matrix.

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
