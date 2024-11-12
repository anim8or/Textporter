#BBD's Krita Script Starter Feb 2018
import os
from krita import Krita, DockWidgetFactory, DockWidgetFactoryBase, DockWidget
from PyQt5.QtWidgets import QPushButton, QWidget, QColorDialog, QVBoxLayout, QFontComboBox, QSpinBox
from PyQt5 import uic
from PyQt5.QtGui import QColor, QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QMessageBox
import configparser
import json
#import fitz  # PyMuPDF for PDF handling
import re


DOCKER_NAME = 'Textporter'
DOCKER_ID = 'pykrita_textporter'


class ColorSwatchButton(QPushButton):
    def __init__(self, color=[0, 0, 255], parent=None):
        super().__init__(parent)
        self.current_color = QColor(*color)
        self.update_icon()
        self.clicked.connect(self.open_color_dialog)

    def update_icon(self):
        """Updates the button icon with the current color."""
        pixmap = QPixmap(self.size())
        pixmap.fill(self.current_color)
        icon = QIcon(pixmap)
        self.setIcon(icon)

    def getRGB(self):
        return [self.current_color.red(), self.current_color.green(), self.current_color.blue()]

    def open_color_dialog(self):
        """Opens a QColorDialog to choose a new color."""
        color = QColorDialog.getColor(self.current_color, self, "Select Color")
        if color.isValid():
            self.current_color = color
            self.update_icon()

# Dialogue class to represent each dialogue entry
class Dialogue:
    def __init__(self, name, dialog_type, text, color):
        self.name = name
        self.dialog_type = dialog_type
        self.text = text
        self.color = color

class Textporter(DockWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(DOCKER_NAME)
        # Load the UI file and set up layout
        ui_file_path = os.path.join(os.path.dirname(__file__), "Textporter.ui")
        self.widget = PluginUIWidget(ui_file_path)

        # Set the widget to the Docker container
        self.setWidget(self.widget)

        # Set the size of the docker to ensure it displays properly
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

    def canvasChanged(self, canvas):
        pass

class PluginUIWidget(QWidget):
    def show_message(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)  # Choose an icon, e.g., Information, Warning, Critical
        msg.setText("This is an information message.")
        msg.setWindowTitle("Message Box Title")
        msg.setStandardButtons(QMessageBox.Ok)  # Adds a button to dismiss the message box
        msg.exec_()  # Show the message box
    
    def __init__(self, ui_file):
        super().__init__()
        uic.loadUi(ui_file, self)  # This loads the .ui file into the widget

        layout = self.horizontalLayout_2
        colorButton = ColorSwatchButton(color=[0,0,0])
        layout.addWidget(colorButton)
        
        layout = self.horizontalLayout_4
        colorButton2 = ColorSwatchButton(color=[0,0,0])
        layout.addWidget(colorButton)


        # Set initial default values
        self.setWindowTitle("My Custom Plugin with UI")
        DefaultColor = [0, 0, 0]
        self.fontComboBox.setCurrentFont(QFont('Arial'))
        self.spinBox.setValue(30)
        self.default_styles = self.load_default_styles_from_ini("settings.ini")
        
        
        #connect buttons to functions
        self.pushButton_3.clicked.connect(self.show_message)

    def replace_button(self, old_button, new_button):
        """Replace the old button with a new button in the layout."""
        parent = old_button.parentWidget()
        layout = parent.layout()

        if layout:
            index = layout.indexOf(old_button)
            if index != -1:
                layout.removeWidget(old_button)
                old_button.deleteLater()
                layout.insertWidget(index, new_button)
                new_button.show()  # Ensure the new button is visible
            else:
                print("Old button index not found in layout!")
        else:
            print("No layout found for the parent widget!")

    # Load default character styles from an .ini file
    def load_default_styles_from_ini(self,file_path):
        config = configparser.ConfigParser()
        config.read(file_path)
        character_styles = {}
        
        for section in config.sections():
            color_str = config.get(section, "color", fallback="0,0,0")
            color = [int(c) for c in color_str.split(",")]  # Store color as [R, G, B] list
            character_styles[section] = {
                "font": config.get(section, "font", fallback="Arial"),
                "size": config.getint(section, "size", fallback=14),
                "color": color
            }
        
        # Check if "default" is present, else add a default entry
        if "default" not in character_styles:
            character_styles["default"] = {
                "font": "Arial",
                "size": 14,
                "color": [0, 0, 0]
            }
        
        return character_styles

    # Save character styles dictionary to JSON file
    def save_character_styles_to_json(self,character_styles, json_file_path="character_styles.json"):
        """
        Saves the character styles dictionary to a JSON file.
        Args:
            character_styles (dict): Dictionary containing character styles and dialogues.
            json_file_path (str): Path to save the JSON file. Defaults to 'character_styles.json' in the current directory.
        """
        try:
            with open(json_file_path, "w") as json_file:
                json.dump(character_styles, json_file, indent=4)
            print(f"Character styles successfully saved to {json_file_path}")
        except Exception as e:
            print(f"Error saving character styles to {json_file_path}: {e}")


    # Load character styles dictionary from JSON file
    def load_character_styles_from_json(self,file_path):
        with open(file_path, "r") as file:
            return json.load(file)


instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(DOCKER_ID,
                                        DockWidgetFactoryBase.DockRight,
                                        Textporter)

instance.addDockWidgetFactory(dock_widget_factory)
