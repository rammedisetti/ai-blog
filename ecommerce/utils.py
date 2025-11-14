"""Reusable filtering helpers for ecommerce catalog views."""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable


def _to_bool(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    value_str = str(value).strip().lower()
    if value_str in {"1", "true", "yes", "on"}:
        return True
    if value_str in {"0", "false", "no", "off"}:
        return False
    return None


def _to_decimal(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _split_csv(value: Any) -> Iterable[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        iterable = value
    else:
        iterable = str(value).split(",")
    return [slug.strip() for slug in iterable if str(slug).strip()]


def normalize_product_filters(params: Dict[str, Any]) -> Dict[str, Any]:
    getter = params.get if hasattr(params, "get") else params.__getitem__

    def _safe_get(key: str, default: Any = None) -> Any:
        try:
            return getter(key, default)
        except KeyError:
            return default

    if hasattr(params, "getlist"):
        raw_categories = params.getlist("category") or _safe_get("category")
    else:
        raw_categories = _safe_get("category")
    categories = _split_csv(raw_categories)
    is_free = _to_bool(_safe_get("is_free"))
    price_min = _to_decimal(_safe_get("price_min"))
    price_max = _to_decimal(_safe_get("price_max"))
    sort = (_safe_get("sort") or "newest").lower()
    if sort not in {"newest", "oldest", "price_asc", "price_desc", "popular"}:
        sort = "newest"

    search = (_safe_get("q") or "").strip()

    try:
        page = int(_safe_get("page") or 1)
    except (TypeError, ValueError):
        page = 1
    page = max(page, 1)

    try:
        per_page = int(_safe_get("per_page") or 12)
    except (TypeError, ValueError):
        per_page = 12
    per_page = min(max(per_page, 1), 48)

    only_active_raw = _safe_get("only_active")
    only_active = _to_bool(only_active_raw) if only_active_raw is not None else True

    return {
        "categories": categories,
        "is_free": is_free,
        "price_min": price_min,
        "price_max": price_max,
        "sort": sort,
        "search": search,
        "page": page,
        "per_page": per_page,
        "only_active": only_active,
    }
