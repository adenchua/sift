import re
from typing import List


def clean_string(input_string: str) -> str:
    # Remove all non-alphanumeric characters except commas and spaces in between
    return re.sub("[^a-zA-Z0-9, ]", "", input_string).strip()


def format_bullet_point_newline_separated_string(string_list: List[str]) -> str:
    bullet_point = "•"
    return f"{bullet_point} " + f"\n{bullet_point} ".join(string_list)
