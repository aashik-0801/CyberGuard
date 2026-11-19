import hashlib
from typing import BinaryIO


MAX_UPLOAD_BYTES = 16 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


class FileTooLargeError(ValueError):
    pass


def hash_stream(
    stream: BinaryIO,
    max_bytes: int = MAX_UPLOAD_BYTES,
    chunk_size: int = CHUNK_SIZE,
) -> tuple[str, int]:
    if max_bytes < 0:
        raise ValueError("The maximum file size cannot be negative.")
    if chunk_size < 1:
        raise ValueError("The hash chunk size must be positive.")

    digest = hashlib.sha256()
    size = 0

    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        size += len(chunk)
        if size > max_bytes:
            raise FileTooLargeError("Each file must be 16 MiB or smaller.")
        digest.update(chunk)

    return digest.hexdigest(), size