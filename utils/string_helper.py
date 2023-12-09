import re


def clean_string(input_string: str) -> str:
    # Remove all non-alphanumeric characters except commas and spaces in between
    cleaned_string = re.sub("[^a-zA-Z0-9, ]", "", input_string).strip()
    return cleaned_string
