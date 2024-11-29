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

def process_images_with_model(image_files: list, model: str, progress_bar, status_text, progress_text, time_text) -> str:
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
        status_text.write(f"Processed {image} in {formatted_elapsed_time}")
        progress_text.write(f"Progress: {(index + 1) / total_images * 100:.2f}%")
        time_text.write(f"Time elapsed: {formatted_elapsed_time}")
        
        # Update progress bar
        progress_bar.progress((index + 1) / total_images)  # Corrected here
    
    return combined_content

def main():
    # Page configuration
    st.set_page_config(
        page_title="PDF to Markdown Converter",
        page_icon="📄",
        layout="wide"
    )

    # Header section with styling
    st.markdown("""
    <h1 style='text-align: center;'>PDF to Markdown Converter 📄</h1>
    <p style='text-align: center;'>Convert your PDF documents to well-formatted Markdown with AI-powered content extraction</p>
    """, unsafe_allow_html=True)

    # File upload section
    st.subheader("📤 Upload PDF Files")
    uploaded_files = st.file_uploader("Drop your PDF files here", type=['pdf'], accept_multiple_files=True)

    # Settings section in an expander
    with st.expander("⚙️ Advanced Settings"):
        col1, col2 = st.columns(2)
        with col1:
            model_name = st.selectbox(
                "Select Model",
                ["llama3.2-vision:11b-instruct-q8_0", "llava", "bakllava"],
                index=0
            )
            image_format = st.selectbox(
                "Image Format",
                ["jpeg", "png"],
                index=0
            )
        with col2:
            image_quality = st.slider("Image Quality", 0, 100, 75)
            output_directory = st.text_input("Output Directory", "/Users/spider/Desktop/outputmd")

    # Start conversion button
    if st.button("🚀 Start Conversion", type="primary"):
        try:
            # Validate inputs
            if not uploaded_files:
                st.error("Please upload at least one PDF file.")
                return

            # Create temporary and output directories
            temp_dir = os.path.join(os.getcwd(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            os.makedirs(output_directory, exist_ok=True)

            # Process uploaded files
            st.info("Processing uploaded files...")
            pdf_paths = []
            for uploaded_file in uploaded_files:
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                pdf_paths.append(temp_path)

            # Convert PDFs to images with progress bar
            with st.spinner("Converting PDFs to images..."):
                image_files = []
                for pdf_path in pdf_paths:
                    images = convert_from_path(
                        pdf_path,
                        output_folder=temp_dir,
                        fmt=image_format,
                        output_file=os.path.splitext(os.path.basename(pdf_path))[0],
                        paths_only=True
                    )
                    image_files.extend(images)

            if not image_files:
                st.warning("No pages found in the uploaded PDF files.")
                return

            # Display number of pages to process
            st.info(f"Found {len(image_files)} pages to process")

            # Process images with the model
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Create two columns for progress tracking
            prog_col1, prog_col2 = st.columns(2)
            with prog_col1:
                progress_text = st.empty()
            with prog_col2:
                time_text = st.empty()

            combined_content = process_images_with_model(
                image_files,
                model_name,
                progress_bar,
                status_text,
                progress_text,
                time_text
            )

            # Save the combined content
            if combined_content:
                datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = os.path.join(output_directory, f"combined_output_{datetime_str}.md")
                save_output(output_filename, combined_content)

                # Show preview of the generated markdown
                with st.expander("📝 Preview Generated Markdown"):
                    st.markdown(combined_content)

                # Add download button for the generated file
                with open(output_filename, 'r') as f:
                    st.download_button(
                        label="📥 Download Markdown File",
                        data=f.read(),
                        file_name=f"combined_output_{datetime_str}.md",
                        mime="text/markdown"
                    )

            # Cleanup temporary files
            try:
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        st.warning(f"Error removing temporary file {file}: {str(e)}")
                os.rmdir(temp_dir)
            except Exception as e:
                st.warning(f"Error cleaning up temporary directory: {str(e)}")

            st.success("✅ Conversion completed successfully!")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    main()