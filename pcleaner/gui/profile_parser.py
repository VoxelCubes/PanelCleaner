import os
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import get_type_hints, Any, Callable

import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
import configupdater as cu
from PySide6.QtCore import Slot
from loguru import logger

import pcleaner.gui.gui_utils as gu
import pcleaner.ocr.supported_languages as osl
from pcleaner import config as cfg
from pcleaner.config import (
    GreaterZero,
    Pixels,
    PixelsSquared,
    LongString,
    RegexPattern,
    Percentage,
    OCREngine,
    ReadingOrder,
    ThreadLimit,
    LayeredExport,
)
from pcleaner.gui.CustomQ.CColorButton import ColorButton
from pcleaner.gui.CustomQ.CComboBox import CComboBox
from pcleaner.gui.CustomQ.CRegexLineEdit import RegexLineEdit
from pcleaner.helpers import tr
from pcleaner.ocr.supported_languages import LanguageCode


class EntryTypes(Enum):
    """
    The different types of entries in a profile.
    """

    Bool = auto()
    Int = auto()
    Float = auto()
    IntGreater0 = auto()
    Pixels = auto()
    PixelsSquared = auto()
    PixelsGreater0 = auto()
    ThreadLimit = auto()
    FloatGreater0 = auto()
    Percentage = auto()
    Str = auto()
    LongString = auto()
    StrNone = auto()
    RegexPattern = auto()
    Color = auto()
    MimeSuffixIMG = auto()
    MimeSuffixMASK = auto()
    OCREngine = auto()
    ReadingOrder = auto()
    LanguageCode = auto()
    LayeredExport = auto()


@dataclass(frozen=True)
class ProfileComment:
    comment: str


@dataclass(frozen=True)
class ProfileEntry:
    key: str
    entry_type: EntryTypes


@dataclass(frozen=True)
class ProfileSpace:
    pass


@dataclass(frozen=True)
class ProfileSection:
    name: str
    items: list[ProfileComment | ProfileEntry] = field(default_factory=list)


class ProfileOptionWidget(Qw.QHBoxLayout):
    """
    A layout widget that contains some data widget and a reset button.
    """

    _data_widget: Qw.QWidget
    _reset_button: Qw.QPushButton
    _entry_type: EntryTypes

    _default_value: Any
    _data_setter: Callable[[Any], None]
    _data_getter: Callable[[], Any]

    valueChanged = Qc.Signal()

    def __init__(self, entry_type: EntryTypes) -> None:
        super().__init__()
        self.create_data_widget(entry_type)
        self.create_reset_button()
        self.addWidget(self._data_widget)
        self.addWidget(self._reset_button)

    def create_reset_button(self) -> None:
        self._reset_button = Qw.QPushButton()
        self._reset_button.setSizePolicy(Qw.QSizePolicy.Fixed, Qw.QSizePolicy.Fixed)
        self._reset_button.setIcon(Qg.QIcon.fromTheme("edit-reset"))
        self._reset_button.setToolTip(self.tr("Reset to default", "Generic reset button tooltip"))
        self._reset_button.clicked.connect(self.reset)
        self.set_reset_button_enabled(False)
        # Don't shift focus to next widget after pressing the button.
        self._reset_button.setFocusPolicy(Qc.Qt.NoFocus)

    def create_data_widget(self, entry_type: EntryTypes) -> None:
        if entry_type == EntryTypes.Bool:
            self._data_widget: Qw.QCheckBox = Qw.QCheckBox()
            self._data_widget.stateChanged.connect(self._value_changed)
            self._data_setter = self._data_widget.setChecked
            self._data_getter = self._data_widget.isChecked

        elif entry_type == EntryTypes.Int or entry_type == EntryTypes.IntGreater0:
            self._data_widget: Qw.QSpinBox = Qw.QSpinBox()
            self._data_widget.setMaximum(999999999)  # Can't go much higher due to int32 limits.
            self._data_setter = self._data_widget.setValue
            self._data_getter = self._data_widget.value
            if entry_type == EntryTypes.IntGreater0:
                self._data_widget.setMinimum(1)
            self._data_widget.valueChanged.connect(self._value_changed)

        elif entry_type == EntryTypes.Pixels or entry_type == EntryTypes.PixelsGreater0:
            self._data_widget: Qw.QSpinBox = Qw.QSpinBox()
            self._data_widget.setMaximum(999999999)  # Can't go much higher due to int32 limits.
            self._data_widget.setSuffix(self.tr(" px", "Pixel unit"))
            self._data_setter = self._data_widget.setValue
            self._data_getter = self._data_widget.value
            if entry_type == EntryTypes.PixelsGreater0:
                self._data_widget.setMinimum(1)
            self._data_widget.valueChanged.connect(self._value_changed)

        elif entry_type == EntryTypes.PixelsSquared:
            self._data_widget: Qw.QSpinBox = Qw.QSpinBox()
            self._data_widget.setMaximum(999999999)  # Can't go much higher due to int32 limits.
            self._data_widget.setSuffix(self.tr(" px²", "Pixel squared unit"))
            self._data_setter = self._data_widget.setValue
            self._data_getter = self._data_widget.value
            self._data_widget.valueChanged.connect(self._value_changed)

        elif entry_type == EntryTypes.ThreadLimit:
            self._data_widget: CComboBox = CComboBox()
            self._data_widget.addTextItemLinkedData(
                self.tr(
                    "All Cores", "The limit on the number of CPU cores to use, or here, no limit."
                ),
                0,
            )
            for i in range(1, os.cpu_count() + 1):
                self._data_widget.addTextItemLinkedData(str(i), i)
            self._data_setter = self._data_widget.setCurrentIndexByLinkedData
            self._data_getter = self._data_widget.currentLinkedData
            self._data_widget.currentIndexChanged.connect(self._value_changed)

        elif entry_type == EntryTypes.Float or entry_type == EntryTypes.FloatGreater0:
            self._data_widget: Qw.QDoubleSpinBox = Qw.QDoubleSpinBox()
            self._data_widget.setStepType(Qw.QAbstractSpinBox.AdaptiveDecimalStepType)
            self._data_setter = self._data_widget.setValue
            # Round to 2 decimal places.
            self._data_getter = lambda: round(self._data_widget.value(), 2)
            if entry_type == EntryTypes.FloatGreater0:
                self._data_widget.setMinimum(0.01)
            self._data_widget.valueChanged.connect(self._value_changed)

        elif entry_type == EntryTypes.Percentage:
            self._data_widget: Qw.QDoubleSpinBox = Qw.QDoubleSpinBox()
            self._data_widget.setRange(0.0, 100.0)
            self._data_widget.setDecimals(1)
            self._data_widget.setSuffix("%")
            self._data_setter = self._data_widget.setValue
            self._data_getter = self._data_widget.value
            self._data_widget.valueChanged.connect(self._value_changed)

        elif entry_type == EntryTypes.Str:
            self._data_widget: Qw.QLineEdit = Qw.QLineEdit()
            self._data_widget.textChanged.connect(self._value_changed)
            self._data_setter = self._data_widget.setText
            self._data_getter = self._data_widget.text

        elif entry_type == EntryTypes.RegexPattern:
            self._data_widget: RegexLineEdit = RegexLineEdit()
            self._data_widget.textChanged.connect(self._value_changed)
            self._data_setter = self._data_widget.setRegex
            self._data_getter = self._data_widget.regex

        elif entry_type == EntryTypes.LongString:
            self._data_widget: Qw.QPlainTextEdit = Qw.QPlainTextEdit()
            # Limit the data widget to a height of 3 lines.
            self._data_widget.setMaximumHeight(self._data_widget.fontMetrics().lineSpacing() * 6)
            size_policy = self._data_widget.sizePolicy()
            size_policy.setVerticalPolicy(Qw.QSizePolicy.Fixed)
            self._data_widget.setSizePolicy(size_policy)
            self._data_widget.textChanged.connect(self._value_changed)
            self._data_setter = self._data_widget.setPlainText
            self._data_getter = self._data_widget.toPlainText

        elif entry_type == EntryTypes.StrNone:
            # Convert empty strings to None and vice versa.
            self._data_widget: Qw.QLineEdit = Qw.QLineEdit()
            self._data_widget.textChanged.connect(self._value_changed)

            def _set_text(text: str | None) -> None:
                if text is None:
                    self._data_widget.setText("")
                else:
                    self._data_widget.setText(text)

            def _get_text() -> str | None:
                text = self._data_widget.text()
                if text == "":
                    return None
                else:
                    return text

            self._data_setter = _set_text
            self._data_getter = _get_text

        elif entry_type == EntryTypes.Color:
            self._data_widget: ColorButton = ColorButton()
            self._data_widget.colorChanged.connect(self._value_changed)
            self._data_setter = self._data_widget.setColor
            self._data_getter = self._data_widget.color

        elif entry_type == EntryTypes.MimeSuffixIMG:
            # Use a spinbox and populate it with the mime suffixes from the config.
            # Use "Same as image" as the default value, with a linked data of None.
            # The other suffixes just store the suffix as the linked data.
            self._data_widget: CComboBox = CComboBox()
            self._data_widget.addTextItemLinkedData(
                self.tr("Same as image", "Profile default option for the file type"), None
            )
            for suffix in cfg.SUPPORTED_IMG_TYPES:
                self._data_widget.addTextItemLinkedData(suffix, suffix)

            self._data_widget.currentIndexChanged.connect(self._value_changed)
            self._data_setter = self._data_widget.setCurrentIndexByLinkedData
            self._data_getter = self._data_widget.currentLinkedData

        elif entry_type == EntryTypes.MimeSuffixMASK:
            # Use a spinbox and populate it with the mime suffixes from the config.
            # Use png as the default value.
            self._data_widget: CComboBox = CComboBox()
            for suffix in cfg.SUPPORTED_MASK_TYPES:
                self._data_widget.addTextItemLinkedData(suffix, suffix)
            self._data_widget.setCurrentIndexByLinkedData(cfg.SUPPORTED_MASK_TYPES[0])
            self._data_widget.currentIndexChanged.connect(self._value_changed)
            self._data_setter = self._data_widget.setCurrentIndexByLinkedData
            self._data_getter = self._data_widget.currentLinkedData

        elif entry_type in (
            EntryTypes.OCREngine,
            EntryTypes.ReadingOrder,
            EntryTypes.LayeredExport,
        ):
            # Use a combobox and populate it with the enum members from the config.
            self._data_widget: CComboBox = CComboBox()
            name_mapper: dict[Enum, str] | None = None
            match entry_type:
                case EntryTypes.OCREngine:
                    enum_class = OCREngine
                case EntryTypes.ReadingOrder:
                    enum_class = ReadingOrder
                case EntryTypes.LayeredExport:
                    enum_class = LayeredExport
                    name_mapper = {
                        LayeredExport.NONE: self.tr("None", "Layered export option"),
                        LayeredExport.PSD_BULK: self.tr("PSD Bulk", "Layered export option"),
                        LayeredExport.PSD_PER_IMAGE: self.tr(
                            "PSD Per Image", "Layered export option"
                        ),
                    }
                case _:
                    raise NotImplementedError(f"Unknown entry type {entry_type}")

            for member in enum_class.__members__.values():
                if name_mapper is not None:
                    self._data_widget.addTextItemLinkedData(name_mapper[member], member)
                else:
                    self._data_widget.addTextItemLinkedData(member.value, member)
            self._data_widget.setCurrentIndex(0)
            self._data_widget.currentIndexChanged.connect(self._value_changed)
            self._data_setter = self._data_widget.setCurrentIndexByLinkedData
            self._data_getter = self._data_widget.currentLinkedData

        elif entry_type == EntryTypes.LanguageCode:
            # Use a combobox and populate it with the enum members from the config.
            self._data_widget: CComboBox = CComboBox()
            for code, lang_name in osl.language_code_name_sorted(
                include_detect=True, pin_important=True, translate=tr
            ):
                self._data_widget.addTextItemLinkedData(lang_name, code)
            self._data_widget.setCurrentIndex(0)
            self._data_widget.currentIndexChanged.connect(self._value_changed)
            self._data_setter = self._data_widget.setCurrentIndexByLinkedData
            self._data_getter = self._data_widget.currentLinkedData

        else:
            raise NotImplementedError(f"Unknown entry type {entry_type}")

    def reset(self) -> None:
        """
        Reset the data widget to the default value.
        """
        self._data_setter(self._default_value)
        self.set_reset_button_enabled(False)

    def value_is_default(self) -> bool:
        """
        Check if the current value is the default value.
        """
        return self._data_getter() == self._default_value

    def set_value(self, value: Any, no_new_default: bool) -> None:
        """
        Set the value of the data widget, which is the new default value.
        Does not emit the valueChanged signal.
        """
        if not no_new_default:
            self._default_value = value
            self.set_reset_button_enabled(False)
        self._data_setter(value)

    def get_value(self) -> Any:
        """
        Get the value of the data widget.

        :return: The value of the data widget.
        """
        return self._data_getter()

    def _value_changed(self) -> None:
        """
        Called when the value of the data widget changes.
        """
        self.set_reset_button_enabled(not self.value_is_default())
        self.valueChanged.emit()

    def set_reset_button_enabled(self, enabled: bool) -> None:
        self._reset_button.setEnabled(enabled)
        self._reset_button.setFlat(not enabled)


def parse_profile_structure(profile: cfg.Profile) -> list[ProfileSection]:
    """
    Parse the given profile and return an intermediate representation,
    Such that it can be used by the GUI.

    This relies on the Profile class exporting to a configupdater object,
    which is then parsed to extract the structure of the profile, including
    comments and section, option names.

    This is done, so that the GUI can reflect the structure of the profile used
    in the CLI, without having to duplicate the structure in the GUI code.

    This representation doesn't contain any values, only the structure.

    :param profile:
    :return: A list of ProfileSection objects.
    """
    sections = []
    conf_updater = profile.bundle_config(gui_mode=True)
    for block in conf_updater.iter_blocks():
        if isinstance(block, cu.Section):
            section_name = to_snake_case(block.name)
            section_items = []
            for section_block in block.iter_blocks():
                if isinstance(section_block, cu.Space):
                    section_block: cu.Space
                    section_items.append(ProfileSpace())

                elif isinstance(section_block, cu.Comment):
                    section_block: cu.Comment
                    comment = str(section_block)
                    comment = comment.replace("#", "").strip().replace("\n", "").strip()
                    section_items.append(ProfileComment(comment))

                elif isinstance(section_block, cu.Option):
                    section_block: cu.Option
                    key = to_snake_case(section_block.key)
                    # Figure out what the type of the value is, referring to the profile class.
                    # This digs into the specific attribute of the profile, since each section
                    # is its own dataclass.
                    value_type = get_type_hints(profile.__getattribute__(section_name).__class__)[
                        key
                    ]
                    if value_type == bool:
                        entry_type = EntryTypes.Bool
                    elif value_type == int:
                        entry_type = EntryTypes.Int
                    elif value_type == Pixels:
                        entry_type = EntryTypes.Pixels
                    elif value_type == Pixels | GreaterZero:
                        entry_type = EntryTypes.PixelsGreater0
                    elif value_type == PixelsSquared:
                        entry_type = EntryTypes.PixelsSquared
                    elif value_type == float:
                        entry_type = EntryTypes.Float
                    elif value_type == int | GreaterZero:
                        entry_type = EntryTypes.IntGreater0
                    elif value_type == float | GreaterZero:
                        entry_type = EntryTypes.FloatGreater0
                    elif value_type == Percentage:
                        entry_type = EntryTypes.Percentage
                    elif value_type == str:
                        entry_type = EntryTypes.Str
                    elif value_type == LongString:
                        entry_type = EntryTypes.LongString
                    elif value_type == str | None:
                        entry_type = EntryTypes.StrNone
                    elif value_type == RegexPattern:
                        entry_type = EntryTypes.RegexPattern
                    elif value_type == tuple[int, int, int, int]:
                        entry_type = EntryTypes.Color
                    elif value_type == OCREngine:
                        entry_type = EntryTypes.OCREngine
                    elif value_type == ReadingOrder:
                        entry_type = EntryTypes.ReadingOrder
                    elif value_type == LanguageCode:
                        entry_type = EntryTypes.LanguageCode
                    elif value_type == LayeredExport:
                        entry_type = EntryTypes.LayeredExport
                    elif value_type == ThreadLimit:
                        entry_type = EntryTypes.ThreadLimit
                    else:
                        raise NotImplementedError(f"Unknown value type {value_type}")

                    # Override the entry type if it's a mime suffix.
                    # This is a special case, applied to keys that contain "file_type" and "mask_file_type".
                    if "mask_file_type" in key:
                        entry_type = EntryTypes.MimeSuffixMASK
                    elif "file_type" in key:
                        entry_type = EntryTypes.MimeSuffixIMG

                    section_items.append(ProfileEntry(key, entry_type))

            # Trim spacers from both ends.
            if isinstance(section_items[0], ProfileSpace):
                section_items.pop(0)
            if isinstance(section_items[-1], ProfileSpace):
                section_items.pop(-1)
            sections.append(ProfileSection(section_name, section_items))

    return sections


class ProfileToolBox(Qw.QToolBox):
    # A subclass that tracks the mapping of widgets to profile options.
    # This is used to save/load the values of the widgets to the profile.

    values_changed = Qc.Signal()  # When False, all values are default.
    values_initialized: bool = (
        False  # This prevents lookups to the default values before they are set.
    )

    def __init__(self, parent=None) -> None:
        Qw.QToolBox.__init__(self, parent)
        self._widgets: dict[str, dict[str, ProfileOptionWidget]] = {}

    def load_profile_structure(self, structure: list[ProfileSection]) -> None:
        """
        Populate the toolbox widget with the given profile structure.
        No values are set, only the structure is replicated with widgets.

        :param structure: The structure to use.
        """

        # Because we need to re-create the form layout after the
        # notes field, we extract this into a function to ensure the
        # same layout settings are applied.
        def make_form_layout() -> Qw.QFormLayout:
            w = Qw.QFormLayout()
            w.setContentsMargins(0, 0, 0, 0)
            w.setSpacing(6)
            return w

        for section in structure:
            section_widget = Qw.QWidget()
            layout = Qw.QVBoxLayout()
            current_layout_form = make_form_layout()
            section_widget.setLayout(layout)
            # Mark the inpainting section as experimental.
            if section.name == "inpainter":
                self.addItem(section_widget, tr("Inpainter (experimental)"))
            else:
                self.addItem(section_widget, tr(to_display_name(section.name), context="Profile"))

            self._widgets[section.name] = {}

            last_was_entry = False
            for item in section.items:
                if isinstance(item, ProfileComment):
                    # Ensure we get large spaces after the settings and before the comments explaining
                    # the next setting.
                    if last_was_entry:
                        spacer = Qw.QSpacerItem(0, 18, Qw.QSizePolicy.Fixed, Qw.QSizePolicy.Fixed)
                        current_layout_form.addItem(spacer)

                    item: ProfileComment
                    label = Qw.QLabel(parent=self, text=tr(item.comment, context="Profile"))
                    label.setOpenExternalLinks(True)
                    label.setWordWrap(True)
                    # Allow copying the text for people to use machine translation.
                    label.setTextInteractionFlags(Qc.Qt.TextSelectableByMouse)
                    current_layout_form.addRow(label)

                    last_was_entry = False

                elif isinstance(item, ProfileSpace):
                    # We don't actually care about these anymore.
                    continue

                elif isinstance(item, ProfileEntry):
                    last_was_entry = True
                    item: ProfileEntry
                    # Make a special exception for the notes field, which needs to take up
                    # the entire width of the form, otherwise it is really narrow and looks
                    # rather retarded.
                    # The solution here is to break up the usual form layout and insert just
                    # the options widget, not even a label. After that, resume with a new form layout.
                    if item.key == "notes":
                        layout.addLayout(current_layout_form)

                        notes_widget = ProfileOptionWidget(item.entry_type)
                        layout.addLayout(notes_widget)
                        self._widgets[section.name][item.key] = notes_widget
                        notes_widget.valueChanged.connect(self._on_value_changed)

                        current_layout_form = make_form_layout()
                        continue

                    label = Qw.QLabel(
                        parent=self, text=tr(to_display_name(item.key), context="Profile")
                    )
                    label.setToolTip(to_display_name(item.key))
                    option_widget = ProfileOptionWidget(item.entry_type)
                    current_layout_form.addRow(label, option_widget)
                    option_widget.valueChanged.connect(self._on_value_changed)

                    self._widgets[section.name][item.key] = option_widget

            # Add the form layout to the section widget.
            layout.addLayout(current_layout_form)
            # Tell the vbox layout to stretch the last item to fill the space.
            layout.addStretch(1)

    def set_profile_values(self, profile: cfg.Profile, no_new_defaults: bool = False) -> None:
        """
        Load the values from the given profile into the widgets.
        Sometimes we just want to change the value currently being displayed, as
        as result of automatic fixes, not as the ground truth of the current profile.

        :param profile: The profile to load.
        :param no_new_defaults: If True, don't update the default values.
        """
        logger.debug("Setting profile values")
        # Assign the value and connect the reset functionality for each widget.
        for section_name, section in self._widgets.items():
            for key, option_widget in section.items():
                # Get the value from the profile.
                value = profile.get(section_name, key)
                option_widget.set_value(value, no_new_defaults)

        self.values_initialized = True

    def get_profile_values(self, profile: cfg.Profile, no_validation: bool = False) -> None:
        """
        Save the values from the widgets to the given profile.
        Update in place.

        The only value validated here is the model path. We don't want to interrupt the user while
        typing.

        We also need to validate that the regex compiles.

        :param profile: The profile to save to.
        :param no_validation: If True, skip validation of the values.
        """
        found_model_path = False
        # Assign the value and connect the reset functionality for each widget.
        for section_name, section in self._widgets.items():
            for key, option_widget in section.items():
                # Get the value from the widget.
                value = option_widget.get_value()
                profile.set(section_name, key, value)
                # Special case: model path
                # Warn if it's an invalid path.
                if key == "model_path":
                    found_model_path = True
                    if value is not None and not Path(value).exists():
                        if no_validation:
                            continue
                        logger.error(
                            f"Model path {value} does not exist. Please check your profile."
                        )
                        gu.show_warning(
                            self,
                            "Invalid model path",
                            self.tr(
                                "<html>The Text Detector model path {value} does not exist, reverting to default."
                                "\nYou can download the model manually from <a href="
                                '"https://github.com/zyddnys/manga-image-translator/releases/latest">here</a>'
                                " or continue using the default model.</html>"
                            ).format(value=value),
                        )
                if key == "ocr_blacklist_pattern":
                    try:
                        re.compile(value)
                    except re.error as e:
                        if no_validation:
                            continue
                        logger.error(
                            f"Invalid regex pattern {value} for {key}. Please check your profile."
                        )
                        gu.show_warning(
                            self,
                            "Invalid regex pattern",
                            self.tr(
                                'The regex pattern "{value}" for {key} is invalid, reverting to default.'
                            ).format(value=value, key=key),
                            detailedText=str(e),
                        )
        # Sanity check to guard against future breakage.
        if not found_model_path:
            logger.error("No model path found in profile.")

    @Slot()
    def _on_value_changed(self) -> None:
        """
        Check if all values are default, then re-emit the signal.
        """
        if not self.values_initialized:
            return

        self.values_changed.emit()

    def reset_all(self) -> None:
        """
        Reset all widgets to their default values.
        """
        for section in self._widgets.values():
            for widget in section.values():
                widget.reset()

    def is_modified(self) -> bool:
        """
        Check if any values have been modified.

        :return: True if any values have been modified.
        """
        return not all(
            w.value_is_default() for section in self._widgets.values() for w in section.values()
        )


def to_snake_case(name: str) -> str:
    """
    Convert the given name to snake case.

    Example:
        "ThisIsATest" -> "this_is_a_test"

    :param name: The name to convert.
    :return: The converted name.
    """
    # https://stackoverflow.com/a/1176023
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def to_display_name(name: str) -> str:
    """
    Convert the given name to a display name.
    Split on underscores or CamelCase and capitalize each word.

    Example:
        "this_is_a_test" -> "This Is A Test"

    :param name: The name to convert.
    :return: The converted name.
    """
    name = name.replace("_", " ")
    # https://stackoverflow.com/a/1176023
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1 \2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1 \2", s1)
    return (
        " ".join(word.capitalize() for word in s2.split(" "))
        .replace("Ai ", "AI ")
        .replace("Ocr", "OCR")
    )
