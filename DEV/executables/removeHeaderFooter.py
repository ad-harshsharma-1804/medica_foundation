import os
import re

# Directory containing your HTML files
directory = "/Users/mac/Accelerating Digital/Scraping/Playwright/medicafoundation/medica_html_copy"

# Function to remove the entire div with class="header" and its contents
def remove_header_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Regex to remove the entire <div class="header"> along with its content
    content = re.sub(r'(<div[^>]*class="[^"]*header[^"]*"[^>]*>).*?(</div>)', '', content, flags=re.DOTALL)

    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

# Loop through all HTML files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".html"):
        file_path = os.path.join(directory, filename)
        remove_header_from_file(file_path)
        print(f"Removed header from {filename}")
