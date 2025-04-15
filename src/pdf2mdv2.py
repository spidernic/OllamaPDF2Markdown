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
- **Email**: spidernic@me.com 
- **LinkedIn**: [Nic Cravino](https://www.linkedin.com/in/nic-cravino)
- **Date**: October 30, 2024
- Bugfix: 20 February 2025 - Thanks @https://github.com/mmol67 !

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
import gc
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def process_images_with_model(image_files: list, model: str, output_filename: str = None) -> str:
    """
    Process each image with a multimodal model and return the combined content.
    Memory-efficient version with proper cleanup.
    """
    combined_content = ""
    total_images = len(image_files)
    
    for idx, image in enumerate(sorted(image_files), 1):
        start_time = time.time()
        image_path = os.path.abspath(image)
        
        try:
            print(f"Processing image {idx}/{total_images}: {image}")
            logging.info(f"Processing image {idx}/{total_images}: {image}")
            
            # Read image in a controlled block
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            logging.info("Sending image to ollama...")
            print("Sending image to ollama...")
            try:
                response = ollama.chat(
                    model=model,
                    messages=[{
                        'role': 'user',
                        'content': 'message="Extract the content of this image as a markdown document. Do not wrap in a markdown code block. Ensure the order of content is preserved in the final output. Tables should be returned as a markdown table."',
                        'images': [image_data]
                    }]
                )
                print("Received response from ollama.")
                logging.info("Received response from ollama.")
            except Exception as e:
                logging.error(f"Error during ollama.chat: {e}")
                continue

            # Clear the image data from memory
            del image_data
            
            # Extract content if response is in the expected format
            print("Extracting content...")
            logging.info("Extracting content...")
            if isinstance(response, dict) and 'message' in response:
                content = response['message']['content']
                combined_content += content + "\n\n"
                
                # Clear response data
                del content
                del response
            else:
                logging.error(f"Unexpected response format for image {image}: {response}")
                continue

            process_time = time.time() - start_time
            logging.info(f"Processed {image} in {process_time:.2f} seconds")
            
            # Force garbage collection after each image
            gc.collect()
            
            # Add a small delay between processing to allow system cleanup
            time.sleep(1)

            # I want to append the combined content to a file every 5 images
            if idx % 5 == 0 and output_filename:
                print(f"Saving intermediate results after image {idx}...")
                save_output(output_filename, combined_content)
                combined_content = ""
        except Exception as e:
            logging.error(f"Error processing image {image}: {str(e)}")
            continue
            
    return combined_content

def main():
    src_directory = "./data"
    tgt_directory = "./temp"
    output_directory = "./output"
    # model_name = 'llama3.2-vision'
    model_name = 'mistral-small3.1:24b-instruct-2503-fp16'

    try:
        # Step 1: Convert PDFs to images
        print("Starting PDF to image conversion...")
        logging.info("Starting PDF to image conversion...")
        convert_pdf_to_images(src_directory, tgt_directory)
        gc.collect()  # Cleanup after conversion

        # Step 2: Process images with the model
        print("Starting image processing...")
        logging.info("Starting image processing...")
        # Get all files in the target directory
        all_files = os.listdir(tgt_directory)
        
        # Filter only JPG files
        jpg_files = [file for file in all_files if file.endswith(".jpg")]
        
        # Create full paths
        image_files = []
        for file in jpg_files:
            full_path = os.path.join(tgt_directory, file)
            image_files.append(full_path)
            
        print(f"Found {len(image_files)} images to process")
        
        # Create output filename first so it can be passed to process_images_with_model
        datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join(output_directory, f"combined_output_{datetime_str}.md")
        
        combined_content = process_images_with_model(image_files, model_name, output_filename)

        # Step 3: Save the combined content to a markdown file
        if combined_content:
            # Using the same output_filename that was passed to process_images_with_model
            save_output(output_filename, combined_content)
            logging.info(f"Final output saved to {output_filename}")

        logging.info("******************** Done ********************")
    except Exception as e:
        logging.error(f"An error occurred during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
