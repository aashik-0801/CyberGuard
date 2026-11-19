import csv
import io
from collections.abc import Iterable
from datetime import datetime

from backend.models import Activity


def _safe_csv_value(value: object) -> str:
    text = str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + text
    return text


def build_report(
    title: str,
    rows: Iterable[tuple[str, object]],
    file_format: str,
) -> tuple[str, str]:
    if file_format == "csv":
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(("Field", "Value"))
        for key, value in rows:
            writer.writerow((_safe_csv_value(key), _safe_csv_value(value)))
        return output.getvalue(), "text/csv; charset=utf-8"
    if file_format == "txt":
        lines = [title, "=" * len(title)]
        lines.extend(f"{key}: {value}" for key, value in rows)
        return "\n".join(lines) + "\n", "text/plain; charset=utf-8"
    raise ValueError("Choose CSV or text format.")


def build_activity_report(
    activities: Iterable[Activity],
    file_format: str,
) -> tuple[str, str]:
    records = list(activities)
    if file_format == "csv":
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(("Timestamp", "Category", "Description"))
        for activity in records:
            writer.writerow(
                (
                    _safe_csv_value(_format_timestamp(activity.timestamp)),
                    _safe_csv_value(activity.activity_type),
                    _safe_csv_value(activity.description),
                )
            )
        return output.getvalue(), "text/csv; charset=utf-8"
    if file_format == "txt":
        lines = ["CyberGuard activity export", "=========================="]
        lines.extend(
            f"{_format_timestamp(item.timestamp)} | {item.activity_type} | {item.description}"
            for item in records
        )
        return "\n".join(lines) + "\n", "text/plain; charset=utf-8"
    raise ValueError("Choose CSV or text format.")


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat(sep=" ", timespec="seconds") + " UTC"
    return value.isoformat(sep=" ", timespec="seconds")