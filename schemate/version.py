"""
Defines module and package information for schemate, specifically the version.
"""

# Module version and package information
__version_info__ = {
    "major": 0,
    "minor": 4,
    "micro": 0,
    "releaselevel": "beta",
    "post": 0,
    "serial": 1,
}


def get_version(short: bool = False) -> str:
    """
    Prints the version.
    """
    assert __version_info__["releaselevel"] in ("alpha", "beta", "final")
    vers = ["{major}.{minor}.{micro}".format(**__version_info__)]

    if __version_info__["releaselevel"] != "final" and not short:
        vers.append(
            "-{}.{}".format(
                __version_info__["releaselevel"],
                __version_info__["serial"],
            )
        )

    if __version_info__["post"]:
        vers.append(".post{}".format(__version_info__["post"]))

    return "".join(vers)
