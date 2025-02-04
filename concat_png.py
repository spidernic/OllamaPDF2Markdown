from PIL import Image
import os
import argparse

def concatenate_images(path, mode='horizontal'):
    # List all PNG files in the given path
    png_files = [f for f in os.listdir(path) if f.endswith('.png')]
    
    # Sort the files to ensure a consistent order
    png_files.sort()
    
    # Open images and store them in a list
    images = []
    for file in png_files:
        img_path = os.path.join(path, file)
        image = Image.open(img_path)
        images.append(image)
        
    # Check if there are any images
    if not images:
        print("No PNG files found in the directory.")
        return
    
    # Concatenate images
    if mode == 'horizontal':
        result = Image.new('RGBA', (sum(i.width for i in images), max(i.height for i in images)))
        x_offset = 0
        for img in images:
            result.paste(img, (x_offset, 0))
            x_offset += img.width
    elif mode == 'vertical':
        result = Image.new('RGBA', (max(i.width for i in images), sum(i.height for i in images)))
        y_offset = 0
        for img in images:
            result.paste(img, (0, y_offset))
            y_offset += img.height
    
    # Save the resulting image
    result.save('output.png')
    
    print(f"Images concatenated and saved as output.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Concatenate PNG files in a directory.')
    parser.add_argument('-p', '--path', help='Path to the folder containing PNG files.', required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-x', '--horizontal', action='store_true', help='Concatenate images horizontally.')
    group.add_argument('-v', '--vertical', action='store_true', help='Concatenate images vertically.')
    
    args = parser.parse_args()
    
    if args.horizontal:
        concatenate_images(args.path, 'horizontal')
    elif args.vertical:
        concatenate_images(args.path, 'vertical')
    else:
        # Default to horizontal if neither -x nor -v is specified
        concatenate_images(args.path)