import re


def clean_string(input_string: str) -> str:
    # Remove all non-alphanumeric characters except commas
    cleaned_string = re.sub("[^a-zA-Z0-9,]", "", input_string)
    return cleaned_string
