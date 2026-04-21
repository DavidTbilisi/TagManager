"""Process-wide CLI flags (verbosity, JSON output, optional log file)."""

import json
import logging
import os
import sys
from typing import Any, Optional

_JSON_MODE = False
_QUIET = False


def init_cli(
    verbose: bool = False,
    quiet: bool = False,
    log_file: Optional[str] = None,
    json_output: bool = False,
) -> None:
    global _JSON_MODE, _QUIET
    _JSON_MODE = bool(json_output) or os.environ.get("TM_JSON", "").lower() in ("1", "true", "yes")
    _QUIET = bool(quiet) and not verbose

    root = logging.getLogger()
    root.handlers.clear()
    level = logging.DEBUG if verbose else (logging.WARNING if quiet else logging.INFO)
    root.setLevel(level)

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    root.addHandler(sh)

    if log_file:
        try:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(fmt)
            root.addHandler(fh)
        except OSError as e:
            root.warning("Could not open log file %s: %s", log_file, e)

    logging.debug("TagManager CLI initialized (verbose=%s quiet=%s json=%s)", verbose, quiet, _JSON_MODE)


def json_mode() -> bool:
    return _JSON_MODE


def quiet_mode() -> bool:
    return _QUIET


def log_debug(msg: str, *args: Any) -> None:
    logging.getLogger("tagmanager").debug(msg, *args)


def emit_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def echo(msg: str = "", err: bool = False) -> None:
    if _QUIET and not err:
        return
    print(msg, file=sys.stderr if err else sys.stdout)
