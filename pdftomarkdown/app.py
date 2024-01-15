import pdfplumber
import copy
import fitz  # PyMuPDF
import glob
import os

def extract_text_tables_images(pdf_path,image_output_path="."):
    doc = fitz.open(pdf_path)
    result = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_number in range(len(pdf.pages)):
            page_result = {"page": page_number + 1, "images": [], "text": [], "tables": []}
            page = pdf.pages[page_number]
            paged = doc[page_number]

            # Save the image as PNG
            # Extract images
            image_list = paged.get_images(full=True)
            
            for img_info in image_list:
                image_index = img_info[0]
                base_image = doc.extract_image(image_index)

                image_bytes = base_image["image"]

                # Save the image
                image_filename = f"image_page{page_number + 1}_img{image_index + 1}.png"
                with open(image_filename, "wb") as img_file:
                    img_file.write(image_bytes)

                # page_result["images"].append(('image', image_filename))
                 # Extract images width and height
                images = page.images
                for image_data in images:
                    image_info = { "src":image_filename}
                    page_result["images"].append(image_info)
            
            # Extract text
            text = page.extract_text()
            sentences = [sentence.strip() for sentence in text.split('\n') if sentence.strip()]
            page_result["text"] = sentences
            
            # Extract tables
            tables = page.extract_tables()
            for table in tables:
                table_data = []
                for row in table:
                    table_data.append([str(cell.strip()) if cell is not None else '' for cell in row])
                page_result["tables"].append(table_data)
                    
            result.append(page_result)
    
    return result

def remove_tables_from_text(extraction_result): # remove table data from text that was as text
    prepositions_list = [ #list of prepositions to avoid removing matching
    'aboard', 'about', 'above', 'across', 'after', 'against', 'along', 'amid', 'among', 'around',
    'as', 'at', 'and', 'before', 'behind', 'below', 'beneath', 'beside', 'between', 'beyond', 'but',
    'by', 'concerning', 'considering', 'despite', 'down', 'during', 'except', 'for', 'from', 'in',
    'inside', 'into', 'like', 'near', 'of', 'off', 'on', 'onto', 'out', 'outside', 'over', 'past',
    'regarding', 'round', 'since', 'through', 'to', 'toward', 'under', 'until', 'unto', 'with',
    'within', 'without'
]
    page_index=0
    for page_result in extraction_result:
        #to avoid mutation
        page_text=copy.deepcopy(page_result)
        page_index=extraction_result.index(page_result)
        removed_sentences=[]
        for sentence in page_result['text']:
           
            for table in page_result['tables']:
                for row in table:
                    result_string=' '.join(row) 
                    if sentence.strip() == result_string.strip():
                        
                        index=page_text['text'].index(sentence)
                        removed_sentences.append(page_text['text'][index])
                        del page_text['text'][index]
        extraction_result[page_index]['text']=page_text['text']
    
    
def remove_tables_from_text_extra(extraction_result): #second pass to account case where an exact match could not be found

    prepositions_list = [ #list of prepositions to avoid removing matching
    'aboard', 'about', 'above', 'across', 'after', 'against', 'along', 'amid', 'among', 'around',
    'as', 'at', 'and', 'before', 'behind', 'below', 'beneath', 'beside', 'between', 'beyond', 'but',
    'by', 'concerning', 'considering', 'despite', 'down', 'during', 'except', 'for', 'from', 'in',
    'inside', 'into', 'like', 'near', 'of', 'off', 'on', 'onto', 'out', 'outside', 'over', 'past',
    'regarding', 'round', 'since', 'through', 'to', 'toward', 'under', 'until', 'unto', 'with',
    'within', 'without'
]
    page_index=0
    count=0
    for page_result in extraction_result:
        #to avoid mutation
        page_text=copy.deepcopy(page_result)
        page_index=extraction_result.index(page_result)
        
        for sentence in page_result['text']:
           
            for table in page_result['tables']:
                for row in table:

                    row_string=" ".join(row).split(' ')
                    for word in row_string:
                         if word not in prepositions_list and len(word) >3:
                            if word in sentence:
                             
                                index=page_result['text'].index(sentence)
                               
                                if len(page_text['text']) <= index:
                                    break
                                else:
                                    # print(page_result['text'][index])
                                    # print(word)
                                    if page_text['text'][index] == page_result['text'][index]:
                                        del page_text['text'][index]
                                        
                                            
                                   
        extraction_result[page_index]['text']=page_text['text']
    # print(count)
        

def gen_markdown(extraction_result,output_file_path,filecount):
    
    
    print(output_file_path+f' file {filecount}.md')
    with open(output_file_path+f' file {filecount}.md', 'w', encoding='utf-8') as markdown_file:
        # for each page in document
        for page in extraction_result:
            
            for key, value in page.items():
                if key=='page':
                    markdown_file.write(f"# ")
                if key=='text':
                    for line in value:
                        markdown_file.write(f"{line}\n")
                    markdown_file.write('\n')
                if key=='tables':
                    # print(value)
                    for tables in value:
                        count=0 
                        for table in tables:
                            
                            while count<1:
                                
                                markdown_file.write("| "*len(table)+"|\n")
                                markdown_file.write("| " + " | ".join(["-"] * len(table)) + " |\n")
                                print('done')
                                count+=1

                            markdown_file.write("| " + " | ".join(table) + " |\n")
                    
    
                if key=='images':
                    # quick fix for duplicate images
                    previous_value=['']
                    if value!=[]:
                             for image in value:
                                if previous_value[0] == image:
                                    pass
                                else:
                                    markdown_file.write(f"![alt text]({image['src']})\n")
                                    previous_value.pop()
                                    previous_value.append(image)
                                    
                
                markdown_file.write("\n")
    
            

def get_pdf_files(directory):
    pdf_files = []
    search_pattern = os.path.join(directory, '*.pdf')

    # Use glob to find all files matching the pattern
    pdf_files.extend(glob.glob(search_pattern))

    return pdf_files

# Replace 'your_directory_path' with the path to the directory you want to search
directory_path = '.'
pdf_files_list = get_pdf_files(directory_path)

print("List of PDF files:")
for pdf_file in pdf_files_list:
    print(pdf_file)

def print_result(extraction_result):
    for page_result in extraction_result:
        page_number = page_result["page"]
        print(f"\nPage {page_number}:")
        
        print("Text:")
        for sentence in page_result["text"]:
            print(f"  - {sentence}")
        
        print("\nTables:")
        for table_data in page_result["tables"]:
            print("  - Table:")
            for row in table_data:
                print(f"    - {row}")
        
        print("\nImages:")
        for image_info in page_result["images"]:
            print(f"  - Image: {image_info}")


def main(count):
    
    # folder to save output files
    output_file_path =r"C:\Users\hp450\Desktop\coding_assignment\pdftomarkdown\markdown"
    # folder to find pdf documents
    directory_path = '.\pdfs'
    pdf_files_list = get_pdf_files(directory_path)
    for files in pdf_files_list:
        count+=1 #for numbering output documents
        extraction_result = extract_text_tables_images(files,image_output_path=".")
        remove_tables_from_text(extraction_result)
        remove_tables_from_text_extra(extraction_result)
        gen_markdown(extraction_result,output_file_path,count)
        # print_result(extraction_result) 
    
if __name__ == "__main__":
    count=0
    main(count)
