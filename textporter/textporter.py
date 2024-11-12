#BBD's Krita Script Starter Feb 2018
import os
from krita import Krita, DockWidgetFactory, DockWidgetFactoryBase, DockWidget
from PyQt5.QtWidgets import QPushButton, QWidget, QColorDialog, QVBoxLayout, QFontComboBox, QSpinBox
from PyQt5 import uic
from PyQt5.QtGui import QColor, QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QMessageBox


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
        self.spinBox.setValue(30
        )
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



instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(DOCKER_ID,
                                        DockWidgetFactoryBase.DockRight,
                                        Textporter)

instance.addDockWidgetFactory(dock_widget_factory)
