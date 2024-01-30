"""
Keep track of supported languages, affecting both the UI and the Makefile.
The Makefile parses this file to generate the language files.
"""


def supported_languages() -> dict[str, tuple[str, bool]]:
    """
    Return a dictionary of supported languages.
    language code -> (language name, enabled)
    A disabled language won't show up in the UI, but the language file will still be generated.

    :return: Supported languages
    """
    return {
        "en_US": ("English (US)", True),  # Default language, locale C
        "de_DE": ("Deutsch (DE)", True),
        "es_ES": ("Spanish (ES)", False),
        "fr_FR": ("French (FR)", False),
        "tr_TR": ("Turkish (TR)", False),
    }
