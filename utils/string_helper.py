import re
from typing import List


def clean_string(input_string: str) -> str:
    # Remove all non-alphanumeric characters except commas and spaces in between
    return re.sub("[^a-zA-Z0-9, ]", "", input_string).strip()


def get_newline_separated_strings(string_list: List[str]) -> str:
    return "\n".join(string_list)
