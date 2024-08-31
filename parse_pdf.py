import fitz  # PyMuPDF
import re

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text


def remove_after_substring(text, substring):
    """
    Removes the part of the text starting from the specified substring.
    
    :param text: The original text from which to remove content.
    :param substring: The substring from which to start removing content.
    :return: The text with the substring and all content after it removed.
    """
    # Find the position of the substring
    position = text.find(substring)
    
    # If the substring is found, slice the text up to its position
    if position != -1:
        return text[:position]
    else:
        # If the substring is not found, return the original text
        return text

def clean_parsed_pdf(text):
    text = remove_page_numbers(text)
    text = remove_timestamps(text)
    return remove_extra_whitespace(text)

def remove_page_numbers(text):
    return remove_regex(text, r'Page \d+ of \d+')

# Parsing the text from the PDF leaves behind timestamps where page breaks used to be.
def remove_timestamps(text):
    return remove_regex(text, r'\b\d{2}/\d{2}/\d{4} \d{2}:\d{2}\b')

# Remove double spaces and empty lines.
def remove_extra_whitespace(text):
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text

def remove_regex(text, pattern):
    # Substitute all matches with an empty string
    return re.sub(pattern, '', text)

def extract_sections_by_horizontal_lines(input_pdf):
    # Open the PDF document
    doc = fitz.open(input_pdf)
    text_sections = {}
    current_section = ""

    for page_number in range(len(doc)):
    #for page_number in range(0,6):
        page = doc.load_page(page_number)
        rect = page.rect
        
        # Extract all drawing objects on the page
        drawing_objects = page.get_drawings()
        
        # Find horizontal lines
        horizontal_lines = []
        for obj in drawing_objects:
            for item in obj['items']:
                if item[0] == 'l':
                    start = item[1]
                    end = item [2]
                    if abs(end.y - start.y) < 1:  # Check if the line is horizontal
                        line_coordinates = (start, end)
                        horizontal_lines.append(line_coordinates)
            
        # Sort lines by their y-coordinates
        horizontal_lines.sort(key=lambda x: x[0].y)

        # Extract text based on the horizontal lines
        previous_y = rect.y0
        for i, line in enumerate(horizontal_lines):
            y = line[0].y
            clip_rect = fitz.Rect(rect.x0, previous_y, rect.x1, y)
            text = page.get_text("text", clip=clip_rect)
            if text:  # Only add non-empty text
                cleaned_text = clean_parsed_pdf(current_section + text) 
                # Split the string into lines and find the first non-empty line
                title = next((line for line in cleaned_text.splitlines() if line.strip()), None)
                text_sections[title] = cleaned_text 
                current_section = ""
            previous_y = y
        
        # Capture text below the last line (or whole page, if there are no lines)
        clip_rect = fitz.Rect(rect.x0, previous_y, rect.x1, rect.y1)
        text = page.get_text("text-with-newlines", clip=clip_rect)
        if text:
            current_section = current_section + text

    doc.close()
    return text_sections

def document_from_sections(sections: dict):
    combined_document = ""
    for title, content in sections.items():
        combined_document += f"{title}\n{content}\n\n" 
    return combined_document