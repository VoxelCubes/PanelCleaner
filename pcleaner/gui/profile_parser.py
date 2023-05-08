from pathlib import Path
from typing import get_type_hints, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import re

import configupdater as cu
from logzero import logger
import PySide6.QtWidgets as qw
import PySide6.QtGui as qg
import PySide6.QtCore as qc
from PySide6.QtCore import Slot

from pcleaner import config as cfg
from pcleaner.config import GreaterZero
from pcleaner.gui.CustomQ.CColorButton import ColorButton
from pcleaner.gui.CustomQ.CComboBox import CComboBox


class EntryTypes(Enum):
    """
    The different types of entries in a profile.
    """

    Bool = auto()
    Int = auto()
    Float = auto()
    IntGreater0 = auto()
    FloatGreater0 = auto()
    Str = auto()
    StrNone = auto()
    Color = auto()
    MimeSuffixIMG = auto()
    MimeSuffixMASK = auto()


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


class ProfileOptionWidget(qw.QHBoxLayout):
    """
    A layout widget that contains some data widget and a reset button.
    """

    _data_widget: qw.QWidget
    _reset_button: qw.QPushButton
    _entry_type: EntryTypes

    _default_value: Any
    _data_setter: Callable[[Any], None]
    _data_getter: Callable[[], Any]

    valueChanged = qc.Signal()

    def __init__(self, entry_type: EntryTypes):
        super().__init__()
        self.create_data_widget(entry_type)
        self.create_reset_button()
        self.addWidget(self._data_widget)
        self.addWidget(self._reset_button)

    def create_reset_button(self):
        self._reset_button = qw.QPushButton()
        self._reset_button.setSizePolicy(qw.QSizePolicy.Fixed, qw.QSizePolicy.Fixed)
        self._reset_button.setIcon(qg.QIcon.fromTheme("edit-reset"))
        self._reset_button.setToolTip("Reset to default")
        self._reset_button.clicked.connect(self.reset)
        self.set_reset_button_enabled(False)

    def create_data_widget(self, entry_type: EntryTypes):
        if entry_type == EntryTypes.Bool:
            self._data_widget: qw.QCheckBox = qw.QCheckBox()
            self._data_widget.stateChanged.connect(self._value_changed)
            self._data_setter = self._data_widget.setChecked
            self._data_getter = self._data_widget.isChecked

        elif entry_type == EntryTypes.Int or entry_type == EntryTypes.IntGreater0:
            self._data_widget: qw.QSpinBox = qw.QSpinBox()
            self._data_widget.setMaximum(999999999)  # Can't go much higher due to int32 limits.
            self._data_setter = self._data_widget.setValue
            self._data_getter = self._data_widget.value
            if entry_type == EntryTypes.IntGreater0:
                self._data_widget.setMinimum(1)
            self._data_widget.valueChanged.connect(self._value_changed)

        elif entry_type == EntryTypes.Float or entry_type == EntryTypes.FloatGreater0:
            self._data_widget: qw.QDoubleSpinBox = qw.QDoubleSpinBox()
            self._data_widget.setStepType(qw.QAbstractSpinBox.AdaptiveDecimalStepType)
            self._data_setter = self._data_widget.setValue
            # Round to 2 decimal places.
            self._data_getter = lambda: round(self._data_widget.value(), 2)
            if entry_type == EntryTypes.FloatGreater0:
                self._data_widget.setMinimum(0.01)
            self._data_widget.valueChanged.connect(self._value_changed)

        elif entry_type == EntryTypes.Str:
            self._data_widget: qw.QLineEdit = qw.QLineEdit()
            self._data_widget.textChanged.connect(self._value_changed)
            self._data_setter = self._data_widget.setText
            self._data_getter = self._data_widget.text

        elif entry_type == EntryTypes.StrNone:
            # Convert empty strings to None and vice versa.
            self._data_widget: qw.QLineEdit = qw.QLineEdit()
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
            self._data_widget.addTextItemLinkedData("Same as image", None)
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

    def reset(self):
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

    def set_value(self, value: Any):
        """
        Set the value of the data widget, which is the new default value.
        Does not emit the valueChanged signal.
        """
        self._default_value = value
        self._data_setter(value)
        self.set_reset_button_enabled(False)

    def get_value(self) -> Any:
        """
        Get the value of the data widget.

        :return: The value of the data widget.
        """
        return self._data_getter()

    def _value_changed(self):
        """
        Called when the value of the data widget changes.
        """
        self.set_reset_button_enabled(not self.value_is_default())
        self.valueChanged.emit()

    def set_reset_button_enabled(self, enabled: bool):
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
                    elif value_type == float:
                        entry_type = EntryTypes.Float
                    elif value_type == int | GreaterZero:
                        entry_type = EntryTypes.IntGreater0
                    elif value_type == float | GreaterZero:
                        entry_type = EntryTypes.FloatGreater0
                    elif value_type == str:
                        entry_type = EntryTypes.Str
                    elif value_type == str | None:
                        entry_type = EntryTypes.StrNone
                    elif value_type == tuple[int, int, int, int]:
                        entry_type = EntryTypes.Color
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


class ProfileToolBox(qw.QToolBox):

    # A subclass that tracks the mapping of widgets to profile options.
    # This is used to save/load the values of the widgets to the profile.

    values_changed = qc.Signal()  # When False, all values are default.
    values_initialized: bool = (
        False  # This prevents lookups to the default values before they are set.
    )

    def __init__(self, parent=None):
        qw.QToolBox.__init__(self, parent)
        self._widgets: dict[str, dict[str, ProfileOptionWidget]] = {}

    def load_profile_structure(self, structure: list[ProfileSection]) -> None:
        """
        Populate the toolbox widget with the given profile structure.
        No values are set, only the structure is replicated with widgets.

        :param structure: The structure to use.
        """

        for section in structure:
            section_widget = qw.QWidget()
            layout = qw.QFormLayout()
            section_widget.setLayout(layout)
            self.addItem(section_widget, to_display_name(section.name))
            self._widgets[section.name] = {}

            for item in section.items:
                if isinstance(item, ProfileComment):
                    item: ProfileComment
                    label = qw.QLabel(parent=self, text=item.comment)
                    label.setOpenExternalLinks(True)
                    label.setWordWrap(True)
                    layout.addRow(label)

                elif isinstance(item, ProfileSpace):
                    layout.addRow(qw.QLabel(parent=self, text=""))

                elif isinstance(item, ProfileEntry):
                    item: ProfileEntry
                    label = qw.QLabel(parent=self, text=to_display_name(item.key))
                    label.setToolTip(to_display_name(item.key))
                    layout.addRow(label)
                    option_widget = ProfileOptionWidget(item.entry_type)
                    layout.addRow(label, option_widget)
                    option_widget.valueChanged.connect(self._on_value_changed)

                    self._widgets[section.name][item.key] = option_widget

    def set_profile_values(self, profile: cfg.Profile) -> None:
        """
        Load the values from the given profile into the widgets.

        :param profile: The profile to load.
        """
        logger.debug("Setting profile values")
        # Assign the value and connect the reset functionality for each widget.
        for section_name, section in self._widgets.items():
            for key, option_widget in section.items():
                # Get the value from the profile.
                value = profile.get(section_name, key)
                option_widget.set_value(value)

        self.values_initialized = True

    def get_profile_values(self, profile: cfg.Profile) -> None:
        """
        Save the values from the widgets to the given profile.
        Update in place.

        :param profile: The profile to save to.
        """
        logger.debug("Getting profile values")
        # Assign the value and connect the reset functionality for each widget.
        for section_name, section in self._widgets.items():
            for key, option_widget in section.items():
                # Get the value from the widget.
                value = option_widget.get_value()
                profile.set(section_name, key, value)

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

    :param name: The name to convert.
    :return: The converted name.
    """
    name = name.replace("_", " ")
    # https://stackoverflow.com/a/1176023
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1 \2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1 \2", s1)
    return " ".join(word.capitalize() for word in s2.split(" "))
