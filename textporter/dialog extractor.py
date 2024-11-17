import configparser
import json
import fitz  # PyMuPDF for PDF handling
import re


# Load default character styles from an .ini file
def load_default_styles_from_ini( file_path):
    Krita.instance().messageBox(f"file_path")
    
    with open("/home/dave/.local/share/krita/pykrita/textporter/log_file.txt", "a") as log_file:
    log_file.write(log_file)
    #log_file.write(f"{character_styles}\n")
    
    config = configparser.ConfigParser()
    config.read(file_path)
    character_styles = {}
    
    for section in config.sections():
        color_str = config.get(section, "color", fallback="[255,0,0]")
        color = json.loads(color_str)  # Convert string to list

        character_styles[section] = {
            "font": config.get(section, "font", fallback="Arial"),
            "size": config.getint(section, "size", fallback=20),
            "color": color
        }
    #self.show_message(self,character_styles)
    # If "default" isn't in character_styles, add it with expected values
    if "default" not in character_styles:
        character_styles["default"] = {
            "font": "Arial",
            "size": 10,
            "color": [0, 255, 0]
        }
    
    return character_styles

# Save character styles dictionary to JSON file

def save_character_styles_to_json(character_styles, json_file_path="character_styles.json"):
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
def load_character_styles_from_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

# Dialogue class to represent each dialogue entry
class Dialogue:
    def __init__(self, name, dialog_type, text, color):
        self.name = name
        self.dialog_type = dialog_type
        self.text = text
        self.color = color

def parse_character_styles_from_pdf(pdf_file, default_styles):
    # Copy the default styles to prevent modification of the original dictionary
    character_styles = {"default": default_styles["default"].copy()}
    
    pdf_document = fitz.open(pdf_file)

    # Loop through each page of the PDF
    for page_num in range(pdf_document.page_count):
        page_text = pdf_document.load_page(page_num).get_text()
        
        for line in page_text.split("\n"):
            match = re.match(r"([^:]+):\s*(.*)", line.strip())
            if match:
                name = re.sub(r"\(.*?\)", "", match.group(1)).strip()  # Remove parentheses in names
                dialogue_text = match.group(2).strip()
                
                if name not in character_styles:
                    # Initialize a new entry for the character with the default style settings
                    character_styles[name] = default_styles["default"].copy()
                
                if "dialogues" not in character_styles[name]:
                    character_styles[name]["dialogues"] = []
                
                # Append the dialogue text to the character's dialogues
                character_styles[name]["dialogues"].append(dialogue_text)
    
    return character_styles



# Create SVG for Krita text object
def create_svg(dialogue, x_pos, y_pos, font_size, font_name):
    color_rgb = f"rgb({dialogue.color[0]},{dialogue.color[1]},{dialogue.color[2]})"
    return f"""
    <svg height="200" width="500">
        <text x="{x_pos}" y="{y_pos}" font-size="{font_size}" font-family="{font_name}" fill="{color_rgb}">
            {dialogue.text}
        </text>
    </svg>
    """

# Add dialogues as vector layers in Krita
def add_dialogue_to_krita(pdf_file, page_ranges):
    """
    Add dialogue extracted from the PDF file as text items to Krita.
    The pages parameter can be a single page, a list of individual pages, or a range of pages.
    """
    # Load the Krita document
    doc = Krita.instance().activeDocument()
    root = doc.rootNode()

    dialogues = load_dialogues_from_pdf(pdf_file)

    # Flatten page_ranges into a list of individual pages
    page_list = []

    if isinstance(page_ranges, tuple):  # Handle page range (start, end)
        start, end = page_ranges
        page_list.extend(range(start, end + 1))  # Add pages in the range
    elif isinstance(page_ranges, list):  # Handle list of individual pages
        page_list.extend(page_ranges)
    else:  # Handle a single page
        page_list.append(page_ranges)

    page_number = 1
    for page_num in page_list:
        # Load the specific page from the PDF
        pdf_document = fitz.open(pdf_file)
        page = pdf_document.load_page(page_num - 1)  # Page numbers in PyMuPDF are 0-indexed

        # Create a new vector layer for this page
        vector_layer = doc.createVectorLayer(f'Page {page_number}')
        y_pos = 50 + (page_number * 100)  # Adjust the Y position for each new page
        
        # Add the dialogues to the vector layer
        for dialogue in dialogues:
            style = character_styles.get(dialogue.name, character_styles["default"])["style"]
            svg_text = create_svg(dialogue, 10, y_pos, font_size=style["size"], font_name=style["font"])
            vector_layer.addShapesFromSvg(svg_text)
            y_pos += 20  # Adjust Y position for the next dialogue

        # Add the vector layer to the Krita document
        root.addChildNode(vector_layer, None)
        doc.setActiveNode(vector_layer)
        page_number += 1

    doc.refreshProjection()

# Example usage:

# For a single page (e.g., page 5):
#add_dialogue_to_krita(pdf_file, 5)
# For a list of individual pages (e.g., pages 1, 3, 5):
#add_dialogue_to_krita(pdf_file, [1, 3, 5])
# For a range of pages (e.g., pages 5 to 10):
#add_dialogue_to_krita(pdf_file, (5, 10))


# Main usage example
if __name__ == "__main__":
    # Load default styles from .ini file
    default_styles = load_default_styles_from_ini("settings.ini")
    print(default_styles['default'])
    print("------------------------")
    # Path to the PDF file
    pdf_file = "/home/dave/Documents/Comic Jams/366_DungeonsAndBreakfast/Mimosa_FernNorfolk.docx.pdf"
    
    # read in the text file an populate the characters
    #default_styles = parse_character_styles_from_pdf(pdf_file, default_styles)
    
    # Define page ranges for dialogues
    #page_ranges = [(0, 1), (1, 2)]

    # Add dialogues to Krita
    #add_dialogue_to_krita(pdf_file, page_ranges, default_styles)

    # Save parsed character styles to JSON for future use
    #save_character_styles_to_json(default_styles, "/home/dave/Documents/Comic Jams/366_DungeonsAndBreakfast/character_styles.json")
    #load parsed character styles from JSON 
    default_styles = load_character_styles_from_json("/home/dave/Documents/Comic Jams/366_DungeonsAndBreakfast/character_styles.json")
    print(default_styles.keys())