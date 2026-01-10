import base64


def encode_line_name(line_name: str) -> str:
    utf8_bytes = line_name.encode("utf-8")
    base64_encoded = base64.b64encode(utf8_bytes).decode("ascii")
    url_safe = base64_encoded.replace("+", "-").replace("/", "_").rstrip("=")

    return url_safe


print(encode_line_name("st:1413087"))
