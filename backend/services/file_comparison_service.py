import hmac
from typing import BinaryIO

from backend.services.hash_service import hash_stream


def compare_streams(
    original: BinaryIO,
    comparison: BinaryIO,
    max_bytes: int | None = None,
) -> dict[str, str | int | bool]:
    if max_bytes is None:
        original_hash, original_size = hash_stream(original)
        comparison_hash, comparison_size = hash_stream(comparison)
    else:
        original_hash, original_size = hash_stream(original, max_bytes)
        comparison_hash, comparison_size = hash_stream(comparison, max_bytes)
    matches = hmac.compare_digest(original_hash, comparison_hash)
    return {
        "original_hash": original_hash,
        "original_size": original_size,
        "comparison_hash": comparison_hash,
        "comparison_size": comparison_size,
        "match": matches,
        "matches": matches,
    }