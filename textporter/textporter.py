#BBD's Krita Script Starter Feb 2018
import os
from krita import Krita, DockWidgetFactory, DockWidgetFactoryBase, DockWidget
from PyQt5.QtWidgets import QPushButton, QWidget, QColorDialog, QVBoxLayout, QFontComboBox, QSpinBox,QFileDialog,QApplication, QListView, QMainWindow
from PyQt5 import uic
from PyQt5.QtGui import QColor, QIcon, QPixmap, QFont,QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMessageBox
import configparser
import json
import fitz  # PyMuPDF for PDF handling
import re


DOCKER_NAME = 'Textporter'
DOCKER_ID = 'pykrita_textporter'



class MyParser(configparser.ConfigParser):
    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d
    
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
    def parse_dialogues_from_text(self,text):
        """
        Process text to extract individual dialogues. Replace this logic
        with your specific parsing rules for dialogue.

        :param text: The text to parse
        :return: A list of dialogue objects or dictionaries
        """
        lines = text.split("\n")
        dialogues = []
        for line in lines:
            if line.strip():  # Filter out empty lines
                dialogues.append({"name": "Character", "content": line.strip()})
        return dialogues

    def load_dialogues_from_pdf(self,pdf_file):
        """
        Extract dialogues from a PDF file. Assumes each page contains text
        representing dialogue and returns a list of dialogue objects.

        :param pdf_file: Path to the PDF file
        :return: List of dialogue objects or dictionaries
        """
        pdf_document = fitz.open(pdf_file)
        dialogues = []

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text = page.get_text("text")  # Extract plain text
            dialogues.extend(self.parse_dialogues_from_text(text))

        return dialogues

    # Add dialogues as vector layers in Krita
    def add_dialogue_to_krita(self):
        """
        Add dialogue extracted from the PDF file as text items to Krita.
        The pages parameter can be 
        A tuple: (1, 5) → [1, 2, 3, 4, 5]
        A list: [1, 3, 5] → [1, 3, 5]
        A single integer: 5 → [5]
        A string range: "1-5" → [1, 2, 3, 4, 5]
        A string list: "1,3,5" → [1, 3, 5]
        """
        # Load the Krita document
        doc = Krita.instance().activeDocument()
        root = doc.rootNode()
        if  self.pdfFile: 
            dialogues = self.load_dialogues_from_pdf(self.pdfFile)
            if self.num_pages != 0: 
                # Flatten page_ranges into a list of individual pages
                page_list = []
                page_ranges = self.lineEdit.text()
                if isinstance(page_ranges, str):  # Handle string-based input
                    if '-' in page_ranges:  # Example: "1-5"
                        start, end = map(int, page_ranges.split('-'))
                        page_list.extend(range(start, end + 1))
                    elif ',' in page_ranges:  # Example: "1,3,5"
                        page_list.extend(map(int, page_ranges.split(',')))
                    else:
                        raise ValueError(f"Invalid string format for page_ranges: {page_ranges}")
                elif isinstance(page_ranges, tuple):  # Handle tuple (start, end)
                    start, end = page_ranges
                    page_list.extend(range(start, end + 1))
                elif isinstance(page_ranges, list):  # Handle list of individual pages
                    page_list.extend(page_ranges)
                elif isinstance(page_ranges, int):  # Handle single page
                    page_list.append(page_ranges)
                else:
                    raise TypeError(f"Unsupported type for page_ranges: {type(page_ranges)}")

                # Ensure page_list is sorted and contains unique pages (optional but useful)
                page_list = sorted(set(page_list))

                page_number = 1
                for page_num in page_list:
                    # Load the specific page from the PDF
                    pdf_document = fitz.open(self.pdfFile)
                    page = pdf_document.load_page(page_num - 1)  # Page numbers in PyMuPDF are 0-indexed

                    # Create a new vector layer for this page
                    vector_layer = doc.createVectorLayer(f'Page {page_number}')
                    y_pos = 50 + (page_number * 100)  # Adjust the Y position for each new page

                    # Add the dialogues to the vector layer
                    for dialogue in dialogues:
                        #failing l 163 think characer styles need to be default_styles instead
                        style = character_styles.get(dialogue.name, character_styles["default"])["style"]
                        svg_text = create_svg(dialogue, 10, y_pos, font_size=style["size"], font_name=style["font"])
                        vector_layer.addShapesFromSvg(svg_text)
                        y_pos += 20  # Adjust Y position for the next dialogue

                    # Add the vector layer to the Krita document
                    root.addChildNode(vector_layer, None)
                    doc.setActiveNode(vector_layer)
                    page_number += 1

                doc.refreshProjection()
    
    def show_message(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)  # Choose an icon, e.g., Information, Warning, Critical
        msg.setText(message)
        msg.setWindowTitle("Message Box Title")
        msg.setStandardButtons(QMessageBox.Ok)  # Adds a button to dismiss the message box
        msg.exec_()  # Show the message box
    
    def parse_character_styles_from_pdf(self):
        # Load the PDF file
        options = QFileDialog.Options()
        pdf_file, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if pdf_file:
            self.pdfFile = pdf_file
            self.label_24.setText(pdf_file) 
            pdf_document = fitz.open(pdf_file)
            # Get the number of pages
            self.num_pages = pdf_document.page_count
            self.label_5.setText(str(self.num_pages ))
            # Copy default styles to prevent modifying the original
            # Get the number of pages
            self.updatePageCount()
            # Loop through each page of the PDF
            for page_num in range(pdf_document.page_count):
                page_text = pdf_document.load_page(page_num).get_text()
                
                for line in page_text.split("\n"):
                    match = re.match(r"([^:]+):\s*(.*)", line.strip())
                    if match:
                        name = re.sub(r"\(.*?\)", "", match.group(1)).strip()  # Remove parentheses in names
                        dialogue_text = match.group(2).strip()
                        
                        if name not in self.default_styles:
                            # Initialize a new entry for the character with the default style settings
                            self.default_styles[name] = self.default_styles["default"].copy()
                        
                        if "dialogues" not in self.default_styles[name]:
                            self.default_styles[name]["dialogues"] = []
                        
                        # Append the dialogue text to the character's dialogues
                        self.default_styles[name]["dialogues"].append(dialogue_text)
            # Update the list widget with the modified default_styles dictionary
            self.update_list_widget_from_dict(self.default_styles)
            return self.default_styles

        
    def update_list_widget_from_dict(self, dict_data):
        """Update the QListWidget with dictionary keys."""
        self.listWidget.clear()  # Clear any existing items
        for key in dict_data.keys():
            if key!="default":
                self.listWidget.addItem(key)  # Add each key as an item

    def add_item(self, dict,model,key, value):
        """Add an item to the dictionary and update the model."""
        dict[key] = value
        self.update_list_widget_from_dict(self.default_styles)

    def remove_item(self):
        """Remove an item from the dictionary and update the model."""
        selected_items = self.listWidget.selectedItems()
        # Check if any item is selected
        if selected_items:
            # Get the text of the first selected item (assuming single selection mode)
            selected_text = selected_items[0].text()
            # Check if the text exists as a key in the dictionary
            if selected_text in self.default_styles.keys():
                # Delete the key from the dictionary
                del self.default_styles[selected_text]
                print(f"Deleted '{selected_text}' from the dictionary.")
            # Update the QListWidget to reflect the changes in the dictionary
            self.update_list_widget_from_dict(self.default_styles)
        else:
            print("No item selected.")
            
    def updatePageCount(self):
        pagecount = ""
        if self.num_pages >0:
            self.label_5.text = str(self.num_pages)
        else:
            self.label_5.text = pagecount

    def populate_ui_from_dict(self):
        """
        Fetch the selected item from QListWidget, get its corresponding values from the dictionary,
        and update the UI elements.
        """
        selected_items = self.listWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "No item selected!")
            return
        selected_key = selected_items[0].text()  # Get the selected item's text
        if selected_key in self.default_styles:
            # Fetch the dictionary values for the selected key
            values = self.default_styles[selected_key]
            # Populate UI elements
            self.fontComboBox_2.setCurrentFont(QFont(values["font"]))
            self.spinBox_3.setValue(values["size"])
            rgb_list = values['color']
            # Convert to QColor
            color = QColor(*rgb_list)
            self.colorButton_2.current_color = color
            self.colorButton_2.update_icon()
            self.label_21.setText(selected_key)
        else:
            QMessageBox.warning(self, "Data Error", f"No data found for {selected_key}!")



    def update_dict_from_ui(self):
        """
        Collect data from UI elements and update the dictionary with the selected item's key.
        """
        selected_items = self.listWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "No item selected!")
            return
        selected_key = selected_items[0].text()  # Get the selected item's text
        # Collect values from UI elements
        font = self.fontComboBox_2.currentFont().family()
        size = self.spinBox_3.value()
        color = self.colorButton_2.current_color  # Assuming a method `getRGB()` in the color button
        # Convert to RGB list
        rgb_list = [color.red(), color.green(), color.blue()]
        # Update the dictionary
        self.default_styles[selected_key] = {
            "font": font,
            "size": size,
            "color": rgb_list,
        }




    def __init__(self, ui_file):
        super().__init__()
        uic.loadUi(ui_file, self)  # This loads the .ui file into the widget
        # Set initial default values
        self.setWindowTitle("My Custom Plugin with UI")
        self.default_styles = self.load_default_styles_from_ini(os.path.dirname(__file__)+"/settings.ini")
        layout_2 = self.horizontalLayout_2
        layout_4 = self.horizontalLayout_4
        self.pdfFile = None
        # Create two separate instances of ColorSwatchButton
        self.colorButton_1 = ColorSwatchButton(color= self.default_styles ['default']['color'])  # Red swatch
        self.colorButton_2 = ColorSwatchButton(color= self.default_styles ['default']['color'])  # Blue swatch

        # Add each color swatch button to its respective layout
        layout_2.addWidget(self.colorButton_1)
        layout_4.addWidget(self.colorButton_2)
        
        self.fontComboBox.setCurrentFont(QFont(self.default_styles ['default']['font']))
        self.spinBox.setValue(self.default_styles ['default']['size'])
        self.num_pages = 0
        self.updatePageCount()

        #connect buttons to functions
        self.pushButton.clicked.connect(self.parse_character_styles_from_pdf)
        self.pushButton_2.clicked.connect(self.remove_item)
        self.pushButton_3.clicked.connect(self.update_dict_from_ui)
        self.pushButton_4.clicked.connect(self.add_dialogue_to_krita)
        self.pushButton_6.clicked.connect(self.save_character_styles_to_json)
        self.pushButton_7.clicked.connect(self.load_character_styles_from_json)
        self.listWidget.itemClicked.connect(self.populate_ui_from_dict)


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
    def load_default_styles_from_ini(seelf,file_path):
        config = configparser.ConfigParser()
        config.read(file_path)
        character_styles = {}
        #QMessageBox.information(QWidget(),"popup example", str(config.sections()))
        for section in config.sections():
            #QMessageBox.information(QWidget(),"popup example", str(character_styles))          
            # Read font and size values
            font = config.get(section, "font", fallback="Arial")
            size = config.getint(section, "size", fallback=20)

            # Convert color to a list of integers
            color_str = config.get(section, "color", fallback="0,0,0")
            color = [int(c.strip()) for c in color_str.split(",")]

            character_styles[section] = {
                "font": font,
                "size": size,
                "color": color
            }
        # If "default" isn't in character_styles, add it with expected values
        if "default" not in character_styles:
            character_styles["default"] = {
                "font": "Arial",
                "size": 10,
                "color": [0, 255, 0]
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
        
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog  # This can be omitted if you want to use native dialogs

        # Show save file dialog
        json_file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",            # Dialog title
            "",                         # Default directory (empty for current)
            "JSON Files (*.JSON)",  # File filter
            options=options
        )

        # Check if the user selected a file path
        if json_file_path:
            try:
                with open(json_file_path, "w") as json_file:
                    json.dump(self.default_styles, json_file, indent=4)
                print(f"Character styles successfully saved to {json_file_path}")
            except Exception as e:
                print(f"Error saving character styles to {json_file_path}: {e}")

    # Load character styles dictionary from JSON file
    def load_character_styles_from_json(self):
        # Open file dialog and get selected file path
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open File",                     # Dialog title
            "",                              # Starting directory (empty for default)
            "JSON Files (*.json)",  # File types filter
            options=options
        )
        # Display the selected file path in the label
        if file_path:
            with open(file_path, "r") as file:
                self.default_styles =  json.load(file)
                self.update_list_widget_from_dict(self.default_styles)

instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(DOCKER_ID,
                                        DockWidgetFactoryBase.DockRight,
                                        Textporter)

instance.addDockWidgetFactory(dock_widget_factory)
