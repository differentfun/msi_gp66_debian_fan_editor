#!/usr/bin/env python3

import copy
import json
import pathlib
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import controller  # noqa: E402

CONFIG_DIR = pathlib.Path("/etc/gp66-fancontrol")
CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_PROFILE = {
    "flag": 13,
    "cpu": [45, 50, 60, 72, 80, 85, 100],
    "gpu": [0, 50, 60, 72, 80, 85, 100],
}


def _ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_profile():
    _ensure_config_dir()
    if not CONFIG_PATH.exists():
        save_profile(DEFAULT_PROFILE)
        return copy.deepcopy(DEFAULT_PROFILE)

    with CONFIG_PATH.open("r", encoding="ascii") as handle:
        data = json.load(handle)

    return _normalize_profile(data)


def save_profile(profile):
    _ensure_config_dir()
    normalized = _normalize_profile(profile)
    with CONFIG_PATH.open("w", encoding="ascii") as handle:
        json.dump(normalized, handle, indent=2)
        handle.write("\n")


def _normalize_profile(profile):
    result = {
        "flag": int(profile.get("flag", DEFAULT_PROFILE["flag"])),
        "cpu": _normalize_curve(profile.get("cpu", DEFAULT_PROFILE["cpu"])),
        "gpu": _normalize_curve(profile.get("gpu", DEFAULT_PROFILE["gpu"])),
    }
    _validate_profile(result)
    return result


def _normalize_curve(values):
    curve = list(values)
    if len(curve) != 7:
        raise ValueError("each curve must contain exactly 7 values")
    return [int(v) for v in curve]


def _validate_profile(profile):
    flag = profile["flag"]
    if not 0 <= flag <= 255:
        raise ValueError("flag must be between 0 and 255")

    for label in ("cpu", "gpu"):
        for value in profile[label]:
            if not 0 <= value <= 255:
                raise ValueError(f"{label} values must be between 0 and 255")


def profile_to_vr(profile):
    data = _normalize_profile(profile)
    return [data["flag"], *data["cpu"], *data["gpu"]]


def apply_profile(profile):
    vr_values = profile_to_vr(profile)
    controller.enable_mode(
        mode=controller.MODE_ADVANCED,
        vr=vr_values,
        offset=controller.DEFAULT_OFFSET,
    )


if __name__ == "__main__":
    profile = load_profile()
    apply_profile(profile)
