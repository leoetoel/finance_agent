"""YFinance data source helpers (OHLC only for now)."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

try:
    import yfinance as yf
except ModuleNotFoundError as e:
    raise RuntimeError(
        "yfinance is not installed. Install it in your env, e.g. `pip install yfinance`."
    ) from e


_RESOLUTION_MAP = {
    "1": "1m",
    "5": "5m",
    "15": "15m",
    "30": "30m",
    "60": "60m",
    "1D": "1d",
    "D": "1d",
    "1W": "1wk",
    "W": "1wk",
    "1M": "1mo",
    "M": "1mo",
}


def _normalize_interval(resolution: str) -> str:
    if not resolution:
        return "1d"
    res = str(resolution).strip()
    return _RESOLUTION_MAP.get(res, res)


def _calc_start_end(count: int, interval: str) -> tuple[datetime, datetime]:
    # Use a wider window to account for non-trading days.
    mult = max(count, 1) * 2
    if interval.endswith("m"):
        minutes = int(interval[:-1])
        delta = timedelta(minutes=minutes * mult)
    elif interval in ("1h", "60m"):
        delta = timedelta(hours=1 * mult)
    elif interval == "1wk":
        delta = timedelta(weeks=mult)
    elif interval == "1mo":
        delta = timedelta(days=31 * mult)
    else:
        delta = timedelta(days=mult)
    end = datetime.utcnow()
    start = end - delta
    return start, end


def get_yfinance_ohlc_data(
    stock_code: str,
    resolution: str = "1D",
    count: int = 30,
    start: Optional[int] = None,
    end: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Fetch OHLC data via yfinance, return a finhub-compatible payload.
    """
    interval = _normalize_interval(resolution)
    if start and end:
        start_dt = datetime.utcfromtimestamp(start)
        end_dt = datetime.utcfromtimestamp(end)
    else:
        start_dt, end_dt = _calc_start_end(count, interval)

    data = yf.download(
        tickers=stock_code,
        interval=interval,
        start=start_dt,
        end=end_dt,
        progress=False,
        auto_adjust=False,
    )
    if data is None or data.empty:
        raise RuntimeError(f"yfinance returned no data for {stock_code} ({interval}).")

    # Keep the last N rows to honor count.
    data = data.tail(count)
    timestamps = [int(ts.timestamp()) for ts in data.index.to_pydatetime()]

    def _to_list(col_name: str) -> list:
        col = data[col_name]
        # yfinance may return a DataFrame with multi-index columns; squeeze to 1D.
        if hasattr(col, "values") and col.ndim > 1:
            col = col.iloc[:, 0]
        return col.tolist()

    return {
        "stock_code": stock_code,
        "resolution": interval,
        "t": timestamps,
        "o": _to_list("Open"),
        "h": _to_list("High"),
        "l": _to_list("Low"),
        "c": _to_list("Close"),
        "v": _to_list("Volume"),
        "s": "ok",
        "source": "yfinance",
        "raw_data": data,
    }
