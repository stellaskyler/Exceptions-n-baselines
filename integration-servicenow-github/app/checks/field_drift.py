def check(sn: dict, gh: dict, fields: list[str]) -> list[str]:
    return [field for field in fields if sn.get(field) != gh.get(field)]
