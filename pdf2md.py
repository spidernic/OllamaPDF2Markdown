'''
# PDF-to-Markdown Extractor with Multimodal Model Processing

A Python script to convert PDFs to images and process each image with a multimodal model, extracting content as markdown. This tool is designed for efficient handling of large PDF files, enabling detailed extraction of tabular and textual information from the images generated from each page.

## Key Features
- **PDF to Image Conversion**: Converts each page of a PDF into an image format for further processing.
- **Multimodal Model Integration**: Utilizes a vision-capable model to extract the content of images in a structured markdown format.
- **Batch Processing**: Handles multiple PDFs and extracts data from each page, ensuring the preservation of content order and format.
- **Detailed Markdown Reports**: Generates consolidated markdown reports from the extracted content, maintaining easy readability and review.

## Author Information
- **Author**: Nic Cravino
- **Email**: spidernic@me.com / ncravino@mac.com
- **LinkedIn**: [Nic Cravino](https://www.linkedin.com/in/nic-cravino)
- **Date**: October 30, 2024

## License: Apache License 2.0 (Open Source)
This script is licensed under the Apache License, Version 2.0. You are free to use, distribute, and modify the software, subject to certain conditions:

- **Freedom of Use**: Use the software for personal, academic, or commercial purposes.
- **Modification and Distribution**: Modify and distribute the software, provided you include a copy of the Apache 2.0 license and state any significant changes made.
- **Attribution**: Acknowledge original authorship when redistributing the software or modified versions of it.
- **Liability Disclaimer**: The software is provided "as is," without warranties or conditions of any kind.
For full details, see the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
'''
  
import ollama
from pdf2image import convert_from_path
import os
from datetime import datetime
import time

def convert_pdf_to_images(src_directory: str, tgt_directory: str = "./temp", fmt: str = "jpeg"):
    """
    Convert all PDFs in the source directory to images and save them in the target directory.
    """
    if not os.path.exists(tgt_directory):
        os.makedirs(tgt_directory)

    pdf_files = [file for file in os.listdir(src_directory) if file.endswith('.pdf')]
    for file in pdf_files:
        prefix = file.replace('.pdf', '')
        convert_from_path(
            os.path.join(src_directory, file), 
            output_folder=tgt_directory, 
            fmt=fmt, 
            output_file=prefix
        )

def save_output(filename: str, content: str):
    """
    Save content to a specified file, ensuring the directory exists.
    """
    output_directory = os.path.dirname(filename)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    with open(filename, "a") as f:
        f.write(content)

def process_images_with_model(image_files: list, model: str) -> str:
    """
    Process each image with a multimodal model and return the combined content.
    """
    combined_content = ""
    for image in sorted(image_files):
        start_time = time.time()
        image_path = os.path.abspath(image)
        with open(image_path, "rb") as image_file:
            response = ollama.chat(
                model=model,
                messages=[{
                    'role': 'user',
                    'content': 'message="Extract the content of this image as a markdown document. Do not wrap in a markdown code block. Ensure the order of content is preserved in the final output. Tables should be returned as a markdown table."',
                    'images': [image_file.read()]
                }]
            )

        # Debugging: Print the response to check its structure
        print("API response:", response)

        # Extract content if response is in the expected format
        if isinstance(response, dict) and 'message' in response:
            combined_content += response['message']['content'] + "\n\n"
        else:
            print("Unexpected response format:", response)
            break

        print(f"{time.time() - start_time} seconds - Processed {image}")
    
    return combined_content

def main():
    src_directory = "./data"
    tgt_directory = "./temp"
    output_directory = "./output"
    model_name = 'llama3.2-vision:11b-instruct-q8_0'

    # Step 1: Convert PDFs to images
    convert_pdf_to_images(src_directory, tgt_directory)

    # Step 2: Process images with the model
    image_files = [os.path.join(tgt_directory, file) for file in os.listdir(tgt_directory) if file.endswith(".jpg")]
    combined_content = process_images_with_model(image_files, model_name)

    # Step 3: Save the combined content to a markdown file
    if combined_content:
        datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join(output_directory, f"combined_output_{datetime_str}.md")
        save_output(output_filename, combined_content)

    print("******************** Done ********************")

if __name__ == "__main__":
    main()
