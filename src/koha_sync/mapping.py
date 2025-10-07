from __future__ import annotations

from typing import Dict, List, Optional

from .config import Settings, get_settings

REQUIRED_FIELDS = ("reg_no", "first_name", "surname")


def to_koha_patron(
    record: Dict[str, object],
    settings: Settings | None = None,
) -> Dict[str, object]:
    """
    Transform a student record into a Koha-compatible patron payload.

    The incoming record is expected to contain the fields described in REQUIRED_FIELDS.
    Optional fields will be passed through when present.
    """
    settings = settings or get_settings()
    _validate_required_fields(record)

    cardnumber = str(record.get("reg_no")).strip()

    payload: Dict[str, object] = {
        "cardnumber": cardnumber,
        "categorycode": settings.koha_category,
        "branchcode": settings.koha_branch,
        "surname": _safe_strip(record.get("surname")),
        "firstname": _safe_strip(record.get("first_name")),
    }

    optional_scalar_fields = {
        "email": "email",
        "phone": "phone",
        "address": "address",
        "userid": "userid",
        "dateofbirth": "dateofbirth",
    }

    for source_key, target_key in optional_scalar_fields.items():
        value = record.get(source_key)
        if value is not None and str(value).strip():
            payload[target_key] = str(value).strip()

    extended_attributes: List[Dict[str, str]] = []
    if course := _safe_strip(record.get("course")):
        extended_attributes.append({"type": "course", "value": course})
    if level := _safe_strip(record.get("level")):
        extended_attributes.append({"type": "level", "value": level})
    if faculty := _safe_strip(record.get("faculty")):
        extended_attributes.append({"type": "faculty", "value": faculty})

    for attr_type, value in settings.koha_static_attributes.items():
        extended_attributes.append({"type": attr_type, "value": value})

    if extended_attributes:
        payload["extended_attributes"] = extended_attributes

    return payload


def _validate_required_fields(record: Dict[str, object]) -> None:
    missing = [name for name in REQUIRED_FIELDS if not record.get(name)]
    if missing:
        raise KeyError(f"Missing required field(s) in record: {', '.join(missing)}")


def _safe_strip(value: Optional[object]) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
