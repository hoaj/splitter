import re


class LocalUtil:
    @staticmethod
    def format_header_retsinformation(input_text):
        formatted_text = re.sub(
            r"(Kapitel (?:\d+|[IVXLCDM]+))\n\n_(.*?)_", r"### \1: \2", input_text
        )
        return formatted_text
