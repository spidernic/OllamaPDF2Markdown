'''
# PDF-to-Markdown Extractor with Multimodal Model Processing GUI Version

A Python script to convert PDFs to images and process each image with a multimodal model, extracting content as markdown. This tool is designed for efficient handling of large PDF files, enabling detailed extraction of tabular and textual information from the images generated from each page.

## Key Features
- **PDF to Image Conversion**: Converts each page of a PDF into an image format for further processing.
- **Multimodal Model Integration**: Utilizes a vision-capable model to extract the content of images in a structured markdown format.
- **Batch Processing**: Handles multiple PDFs and extracts data from each page, ensuring the preservation of content order and format.
- **Detailed Markdown Reports**: Generates consolidated markdown reports from the extracted content, maintaining easy readability and review.

## Author Information
- **Author**: Nic Cravino
- **Email**: spidernic@me.com 
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
import streamlit as st
from pdf2image import convert_from_path
import os
from datetime import datetime, timedelta
import time
import ollama

def convert_pdf_to_images(src_directory: str, tgt_directory: str = "./temp", fmt: str = "jpeg"):
    """
    Convert all PDFs in the source directory to images and save them in the target directory.
    Return a list of image files.
    """
    if not os.path.exists(tgt_directory):
        os.makedirs(tgt_directory)
    pdf_files = [file for file in os.listdir(src_directory) if file.endswith('.pdf')]
    image_files = []
    
    for pdf_file in pdf_files:
        prefix = pdf_file.replace('.pdf', '')
        images = convert_from_path(
            os.path.join(src_directory, pdf_file), 
            output_folder=tgt_directory, 
            fmt=fmt, 
            output_file=prefix,
            paths_only=True
        )
        image_files.extend(images)
    
    return image_files

def save_output(filename: str, content: str):
    """
    Save content to a specified file, ensuring the directory exists.
    """
    output_directory = os.path.dirname(filename)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    with open(filename, "a") as f:
        f.write(content)

def format_elapsed_time(seconds):
    """
    Format elapsed time in seconds to hours, minutes, and seconds.
    """
    tdelta = timedelta(seconds=seconds)
    return str(tdelta)

def process_images_with_model(image_files: list, model: str, progress_bar) -> str:
    """
    Process each image with a multimodal model and return the combined content.
    Update the progress bar as images are processed.
    """
    combined_content = ""
    total_images = len(image_files)
    
    for index, image in enumerate(sorted(image_files)):
        if not os.path.exists(image):
            st.error(f"File not found: {image}")
            continue
        
        start_time = time.time()
        with open(image, "rb") as image_file:
            response = ollama.chat(
                model=model,
                messages=[{
                    'role': 'user',
                    'content': 'message="Extract the content of this image as a markdown document. Do not wrap in a markdown code block. Ensure the order of content is preserved in the final output. Tables should be returned as a markdown table."',
                    'images': [image_file.read()]
                }]
            )
        # Debugging: Print the response to check its structure
        # st.write("API response:", response)
        # Extract content if response is in the expected format
        if isinstance(response, dict) and 'message' in response:
            combined_content += response['message']['content'] + "\n\n"
        else:
            st.error("Unexpected response format:", response)
            break
        
        elapsed_time = time.time() - start_time
        formatted_elapsed_time = format_elapsed_time(elapsed_time)
        st.write(f"{formatted_elapsed_time} - Processed {image}")
        
        # Update progress bar
        progress_bar.progress((index + 1) / total_images)  # Corrected here
    
    return combined_content

def main():
    st.title("PDF to Markdown Converter")
    
    src_directory = st.text_input("Source Directory", "/Users/spider/Desktop/inputpdf")
    tgt_directory = st.text_input("Target Directory (default: ./temp)", "./temp")
    output_directory = st.text_input("Output Directory (default: ./output)", "/Users/spider/Desktop/outputmd")
    
    if st.button("Start Conversion"):
        if not os.path.exists(src_directory):
            st.error("Source directory does not exist.")
            return
        
        # Step 1: Convert PDFs to images
        image_files = convert_pdf_to_images(src_directory, tgt_directory)
        
        if not image_files:
            st.info("No PDF files found in the source directory.")
            return
        
        model_name = 'llama3.2-vision:11b-instruct-q8_0'
        # Step 2: Process images with the model
        progress_bar = st.progress(0)  # Initialize progress bar
        combined_content = process_images_with_model(image_files, model_name, progress_bar)
        
        # Step 3: Save the combined content to a markdown file
        if combined_content:
            datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = os.path.join(output_directory, f"combined_output_{datetime_str}.md")
            save_output(output_filename, combined_content)
        
        st.success("Conversion completed successfully.")
    
if __name__ == "__main__":
    main()