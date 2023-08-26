import re
from io import StringIO
import PySide6.QtWidgets as Qw


# For all show functions, pad the dialog message, so that the dialog is not too narrow for the window title.
MIN_MSG_LENGTH = 50


def show_critical(parent, title: str, msg: str):
    msg = msg.ljust(MIN_MSG_LENGTH)
    return Qw.QMessageBox.critical(parent, title, msg, Qw.QMessageBox.Yes, Qw.QMessageBox.Abort)


def show_warning(parent, title: str, msg: str):
    msg = msg.ljust(MIN_MSG_LENGTH)
    Qw.QMessageBox.warning(parent, title, msg, Qw.QMessageBox.Ok)


def show_info(parent, title: str, msg: str):
    msg = msg.ljust(MIN_MSG_LENGTH)
    Qw.QMessageBox.information(parent, title, msg, Qw.QMessageBox.Ok)


def show_question(
    parent, title: str, msg: str, buttons=Qw.QMessageBox.Yes | Qw.QMessageBox.Cancel
) -> int:
    msg = msg.ljust(MIN_MSG_LENGTH)
    dlg = Qw.QMessageBox(parent)
    dlg.setWindowTitle(title)
    dlg.setText(msg)
    dlg.setStandardButtons(buttons)
    dlg.setIcon(Qw.QMessageBox.Question)
    return dlg.exec()


def ansi_to_html(input_text: str) -> str:
    """
    Convert ansi escape sequences to html.

    Analytics HTML template
    <html><head><meta name="qrichtext" content="1" /><style type="text/css">
    p, li { white-space: pre-wrap; font-family: Noto Mono, Monospace; size: 12pt}
    </style></head><body>
    <p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;
     -qt-block-indent:0; text-indent:0px;"><span style=" ">Mask Fitment Analytics
     <br />---------------------- <br />Total boxes: 5 | Masks succeeded: 5 (100%)
     | Masks failed: </span><span style="color:#b21818;">0</span><span style=" ">
     <br />Perfect masks: </span><span style="color:#18b2b2;">5</span><span style=" ">
     (100%) | Average border deviation: 0.00 <br /><br />Mask usage by mask size
     (smallest to largest): <br />Mask 0  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 1  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 2  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 3  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 4  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 5  :  </span><span style="color:#18b2b2;">0</span>
     <span style=" "> / 0 <br />Mask 6  : </span><span style="color:#18b2b2;">
     ████████████████████████████████████████</span><span style=" "> </span>
     <span style="color:#18b2b2;">1</span><span style=" "> / 1 <br />Mask 7  :  </span>
     <span style="color:#18b2b2;">0</span><span style=" "> / 0 <br />Mask 8  :  </span>
     <span style="color:#18b2b2;">0</span><span style=" "> / 0 <br />Mask 9  :  </span>
     <span style="color:#18b2b2;">0</span><span style=" "> / 0 <br />Mask 10 :  </span>
     <span style="color:#18b2b2;">0</span><span style=" "> / 0 <br />Box mask: </span>
     <span style="color:#18b2b2;">████████████████████████████████████████</span>
     <span style=" "> </span><span style="color:#18b2b2;">4</span><span style=" ">
     / 4 <br /><br /></span><span style="color:#18b2b2;">█ Perfect</span><span style=" ">
     | █ Total<br /><br /></span></p></body></html>
    """
    # Define ANSI escape sequences and corresponding Qt HTML color codes
    ansi_to_html_lut = {
        "31": "color:#eb514f;",
        "32": "color:#00ff00;",
        "33": "color:#ffff00;",
        "34": "color:#0000ff;",
        "35": "color:#a771bf;",
        "36": "color:#00a3a3;",
        "37": "color:#ffffff;",
        "39": " ",  # Default color
    }

    # Initialize HTML header and footer
    html_header = """<html><head><meta name="qrichtext" content="1" /><style type="text/css">
        p, li { white-space: pre-wrap; font-family: Noto Mono, Monospace; size: 12pt}
        </style></head><body>
        <p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">"""
    html_footer = "</p></body></html>"

    # Initialize output HTML with header
    buffer = StringIO()
    buffer.write(html_header)

    # Initialize current_style
    current_style = ""

    # Strip leading and trailing whitespace.
    input_text = input_text.strip()

    # Use regex to find all ANSI sequences and split text
    for plain_text, ansi_code in re.findall(r"(.*?)(?:\x1b\[(\d+)m|$)", input_text, re.DOTALL):
        # Add plain text
        newline = "\n"
        buffer.write(
            f'<span style="{current_style}">{plain_text.replace(newline, "<br />")}</span>'
        )

        # Update the style for the next span based on ANSI code
        if ansi_code:
            current_style = ansi_to_html_lut.get(ansi_code, "")

    # Add HTML footer
    buffer.write(html_footer)

    return buffer.getvalue()
