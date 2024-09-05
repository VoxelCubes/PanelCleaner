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
        "es_ES": ("Español (ES)", True),
        "fr_FR": ("Français (FR)", False),
        "it_IT": ("Italiano (IT)", True),
        "tr_TR": ("Türkçe (TR)", False),
        "bg_BG": ("български (BG)", True),
    }
