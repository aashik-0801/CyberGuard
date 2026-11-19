import hashlib
from typing import BinaryIO


MAX_UPLOAD_BYTES = 16 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


class FileTooLargeError(ValueError):
    pass


def hash_stream(stream: BinaryIO, max_bytes: int = MAX_UPLOAD_BYTES) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0

    while True:
        chunk = stream.read(CHUNK_SIZE)
        if not chunk:
            break
        size += len(chunk)
        if size > max_bytes:
            raise FileTooLargeError("Each file must be 16 MiB or smaller.")
        digest.update(chunk)

    return digest.hexdigest(), size