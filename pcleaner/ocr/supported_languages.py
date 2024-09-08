# This file manages which languages are supported for OCR operations, not the user interface.
import sys
from enum import auto
from typing import Callable

from natsort import humansorted

# If using Python 3.10 or older, use the 3rd party StrEnum.
if sys.version_info < (3, 11):
    from strenum import StrEnum
else:
    from enum import StrEnum


class LanguageCode(StrEnum):
    detect_box = auto()
    detect_page = auto()
    jpn = auto()
    eng = auto()
    kor = auto()
    kor_vert = auto()
    chi_sim = auto()
    chi_tra = auto()
    sqi = auto()
    ara = auto()
    aze = auto()
    aze_cyrl = auto()
    ben = auto()
    bul = auto()
    mya = auto()
    cat = auto()
    hrv = auto()
    ces = auto()
    dan = auto()
    nld = auto()
    epo = auto()
    est = auto()
    fin = auto()
    fra = auto()
    kat = auto()
    deu = auto()
    ell = auto()
    heb = auto()
    hin = auto()
    hun = auto()
    ind = auto()
    ita = auto()
    kaz = auto()
    lat = auto()
    lit = auto()
    ltz = auto()
    msa = auto()
    mon = auto()
    nep = auto()
    nor = auto()
    fas = auto()
    pol = auto()
    por = auto()
    ron = auto()
    rus = auto()
    srp = auto()
    srp_latn = auto()
    slk = auto()
    slv = auto()
    spa = auto()
    swe = auto()
    tgl = auto()
    tam = auto()
    tel = auto()
    tha = auto()
    tur = auto()
    ukr = auto()
    vie = auto()

    def __str__(self):
        return self.value


def to_language_code(lang: str) -> LanguageCode | None:
    """
    Convert a language string to a LanguageCode enum.

    :param lang: The language string.
    :return: The LanguageCode enum or None if not found.
    """
    if lang in LanguageCode.__members__:
        return LanguageCode[lang]
    else:
        return None


LANGUAGE_CODE_TO_NAME: dict[LanguageCode, str] = {
    LanguageCode.detect_box: "Detect per box",
    LanguageCode.detect_page: "Detect per page",
    LanguageCode.jpn: "Japanese",
    LanguageCode.eng: "English",
    LanguageCode.kor: "Korean",
    LanguageCode.kor_vert: "Korean (vertical)",
    LanguageCode.chi_sim: "Chinese - Simplified",
    LanguageCode.chi_tra: "Chinese - Traditional",
    LanguageCode.sqi: "Albanian",
    LanguageCode.ara: "Arabic",
    LanguageCode.aze: "Azerbaijani",
    LanguageCode.aze_cyrl: "Azerbaijani - Cyrilic",
    LanguageCode.ben: "Bengali",
    LanguageCode.bul: "Bulgarian",
    LanguageCode.mya: "Burmese",
    LanguageCode.cat: "Catalan; Valencian",
    LanguageCode.hrv: "Croatian",
    LanguageCode.ces: "Czech",
    LanguageCode.dan: "Danish",
    LanguageCode.nld: "Dutch; Flemish",
    LanguageCode.epo: "Esperanto",
    LanguageCode.est: "Estonian",
    LanguageCode.fin: "Finnish",
    LanguageCode.fra: "French",
    LanguageCode.kat: "Georgian",
    LanguageCode.deu: "German",
    LanguageCode.ell: "Greek",
    LanguageCode.heb: "Hebrew",
    LanguageCode.hin: "Hindi",
    LanguageCode.hun: "Hungarian",
    LanguageCode.ind: "Indonesian",
    LanguageCode.ita: "Italian",
    LanguageCode.kaz: "Kazakh",
    LanguageCode.lat: "Latin",
    LanguageCode.lit: "Lithuanian",
    LanguageCode.ltz: "Luxembourgish",
    LanguageCode.msa: "Malay",
    LanguageCode.mon: "Mongolian",
    LanguageCode.nep: "Nepali",
    LanguageCode.nor: "Norwegian",
    LanguageCode.fas: "Persian",
    LanguageCode.pol: "Polish",
    LanguageCode.por: "Portuguese",
    LanguageCode.ron: "Romanian; Moldavian",
    LanguageCode.rus: "Russian",
    LanguageCode.srp: "Serbian",
    LanguageCode.srp_latn: "Serbian - Latin",
    LanguageCode.slk: "Slovak",
    LanguageCode.slv: "Slovenian",
    LanguageCode.spa: "Spanish; Castilian",
    LanguageCode.swe: "Swedish",
    LanguageCode.tgl: "Tagalog",
    LanguageCode.tam: "Tamil",
    LanguageCode.tel: "Telugu",
    LanguageCode.tha: "Thai",
    LanguageCode.tur: "Turkish",
    LanguageCode.ukr: "Ukrainian",
    LanguageCode.vie: "Vietnamese",
}

LANGUAGES_RTL_BOX_ORDER: set[LanguageCode] = {
    LanguageCode.jpn,
    LanguageCode.chi_sim,
    LanguageCode.chi_tra,
    LanguageCode.ara,
    LanguageCode.fas,
    LanguageCode.heb,
}


def language_code_name_sorted(
    include_detect: bool = True,
    pin_important: bool = True,
    translate: Callable[[str], str] = lambda x: x,
) -> list[tuple[LanguageCode, str]]:
    """
    Sort the languages by their (translated) name.

    :param include_detect: Include the detection settings as "languages".
    :param pin_important: Pin important languages to the top.
    :param translate: [Optional] The translation function.
    """
    if include_detect:
        langs = list(LanguageCode)
    else:
        langs = list(LanguageCode)
        langs.remove(LanguageCode.detect_box)
        langs.remove(LanguageCode.detect_page)

    important_langs = []
    if pin_important:
        # Pull out the important languages.
        important_langs = [
            LanguageCode.jpn,
            LanguageCode.eng,
            LanguageCode.kor,
            LanguageCode.kor_vert,
            LanguageCode.chi_sim,
            LanguageCode.chi_tra,
        ]
        if include_detect:
            important_langs = [LanguageCode.detect_box, LanguageCode.detect_page] + important_langs
        # Remove the important languages from the list.
        langs = [lang for lang in langs if lang not in important_langs]

    # Apply the translation.
    langs = [(lang, translate(LANGUAGE_CODE_TO_NAME[lang])) for lang in langs]

    sorted_langs = humansorted(langs, key=lambda x: x[1])

    if pin_important:
        # Put the important languages at the top.
        important_langs = [
            (lang, translate(LANGUAGE_CODE_TO_NAME[lang])) for lang in important_langs
        ]
        sorted_langs = important_langs + sorted_langs

    return sorted_langs
