import glob
import os
import re
from datetime import datetime

import PySimpleGUI as sg
from loguru import logger
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk


def mm_to_pixels( width, height, dpi=300):
    """Convert a number of pixels in millimeters, based in DPI, 
    25.4 is simply the amount of millimeters in an inch:
    decimal_mm = (pixels * 25.4) / dpi
    pixels = (decimal_mm * dpi) / 25.4
    (width, height) - A4 size 210 x 297 mm
    
    Args:
        width (int): width in mm
        height (int): height in mm
        dpi (int, optional): DPI - dots per inch. Defaults to 300.

    Returns:
        turple: Return the pixel size based on dpi
    """
    new_size = ( int(round((width * dpi)/25.4)) , int(round((height * dpi)/25.4)) )
    return new_size

def create_empty_page(paper_size ,dpi=300):
    """Create a empty page A3 or A4 based on DPI.
    (width, height) - A3 size 297 x 420 mm
    (width, height) - A4 size 210 x 297 mm
    
    Args:
        paper_size (str): select values 'A3' or 'A4'
        dpi (int, optional): DPI - dots per inch. Defaults to 300.

    Raises:
        ValueError: Not supported paper size.
    Returns:"
        Image: Return a Pillow Image
    """

    if paper_size == "A3":
        a3_size = mm_to_pixels(297, 420, dpi)
        blankpage = Image.new('RGB', a3_size,(255, 255, 255))
    elif paper_size == "A4":
        a4_size = mm_to_pixels(210, 297, dpi)
        blankpage = Image.new('RGB', a4_size,(255, 255, 255))
    else:
        raise ValueError("Not supported paper size.")
    return blankpage

def add_legend(tag, text):
    width, height = tag.size
    text_background = Image.new("RGB", (width+10,height+int((height/10))), (255, 255, 255))

    text_background.paste(tag, (5,5,(width+5), (height+5)))
    draw = ImageDraw.Draw(text_background)
    fnt = ImageFont.truetype('GOTHICB.TTF',30) # FontType and FontSize
    w, h = fnt.getsize(text)
    
    #draw.text( ((width-w)/2, (height+(int((height/5)-h)/2))), text, (0,0,0),font=fnt)
    draw.text( (int((width-w)/4), height), text, (0,0,0),font=fnt)
    return text_background

def search_for_apriltag(ids, family, path=""):
    """Looks for apriltags in a path and returns a turple list with the object found.

    Args:
        ids (int or list): A list or a value from ids to search
        family (str): Apriltag family to search

    Raises:
        ValueError: IDs must be a list or a number.

    Returns:
        tuple: Returns a list of tuples, which include id, family and found image object.
    """

    if isinstance(ids, int):
        search_ids = [str(ids).zfill(5)]
    elif isinstance(ids,list):
        search_ids = [str(value).zfill(5) for value in ids] #  recursion for lists of ints/lists of ints
    elif len(ids) > 100:
        raise NameError("List must be small that 100 ids.")
    else:
        raise ValueError("IDs must be a list or a number.")

    path = path + f"\\{family}\\*.png"
    loaded_tags = []

    for filename in glob.glob(path):
        founded_id = re.search("[0-9]{5}", filename)
        if founded_id:
            if founded_id.group(0) in search_ids:
                logger.info(f"Founded ID: {founded_id.group(0)}\nFamily: { family }\nIn path: { filename }")
                #original_tag = Image.open(filename)
                loaded_tags.append((founded_id.group(0), family, filename))
    return loaded_tags

def load_image(path, window):
    try:
        image = Image.open(path)
        image = image.resize((300,300), Image.Resampling.NEAREST)
        image.thumbnail((400, 400))
        photo_img = ImageTk.PhotoImage(image)
        window["image"].update(data=photo_img)
    except:
        print(f"Unable to open {path}!")

def upscale_tags(loaded_tags, new_size=(100,100), with_legend=False, custom_text=''):
    upscaled_loaded_tags = []
    # Background size (width, height)         
    # Tagsize (width, height)
    tag_size = mm_to_pixels(new_size[0], new_size[1])
    for tag in loaded_tags:
        logger.debug(tag)
        image = Image.open(tag[2])
        new_resize_tag = image.resize(tag_size, Image.Resampling.NEAREST) # Need the Image.NEAREST to remove blur
        new_resize_tag = ImageOps.expand(new_resize_tag,border=50,fill='white')
        
        background = Image.new("RGB", (new_resize_tag.size[0],new_resize_tag.size[1]), (255, 255, 255))
        background.paste(new_resize_tag, ((background.size[0] - new_resize_tag.size[0]) // 2, (background.size[1] - new_resize_tag.size[1]) // 2), mask= new_resize_tag.split()[3])
        text = f"ID: { tag[0] }\nFamily: { tag[1] }" + f"\n{custom_text}"
        background = add_legend(background, text)
        
        background = ImageOps.expand(background,border=10,fill='black')
        
        upscaled_loaded_tags.append(background)
    return upscaled_loaded_tags

def export_to_PDF(resized_tags, output_name="tag",output_path='.//PDF//'):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    outputfile = output_path + f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{output_name}.pdf'
    resized_tags[0].save(outputfile, 'PDF', quality=100, save_all=True, append_images=resized_tags[1:])
    logger.info(f'PDF sucessful saved -- {outputfile}')

def main():
    #sg.theme('DarkGreen3')
    PATH = os.path.dirname(os.path.abspath(__file__))
    images = []
    selected_tags = []
    location = 0
    elements = [
        [
            sg.Text("Folder Path",font='GOTHICB'),
            sg.Input(size=(25, 1), enable_events=True, key="file"),
            sg.FolderBrowse(initial_folder=PATH)
        ],
        [sg.Text('Choose Tag Family',size=(20, 1), font='GOTHICB',justification='left')],
        [sg.Text('ID', size =(3, 1)), 
            sg.InputText(size =(10, 1), key='id'), 
            sg.Combo(['tag16h5','tag25h9','tag36h11','tagCircle21h7','tagCircle49h12','tagCustom48h12','tagStandard41h12','tagStandard52h13'],default_value='tag36h11',key='family'),
            sg.Button("Search")],
        [sg.Image(key="image")],
        [
            sg.Button("Prev"),
            sg.Button("Next"),
            sg.Button("Add"),
            sg.Button("Remove")
        ],
        [sg.Text('Selected Apriltags',size=(30, 1), font='GOTHICB',justification='left')],
        [sg.Listbox(values=selected_tags,select_mode='extended', enable_events=True, key="-Selected-", size=(30, 6))],
        [
            sg.Radio('PDF', "RADIO1", default=True, key='-PDF-'),
            sg.Radio('PNG', "RADIO1", key='-PNG-'),
            sg.Radio('JPEG', "RADIO1", key='-JPEG-')],
        [sg.Button("Generate Tags")]
    ]
    window = sg.Window("Apriltag Generate", elements)
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        
        if event == "file":
            logger.debug(values["file"])
            PATH = values["file"]

        if event == "Search":
            window["file"].update(PATH+"\\data")
            if values['id']:
                try:
                    int(values['id'])
                    logger.debug(f"Searching! {type(values['id'])} {values['family']}")
                    images = search_for_apriltag(int(values['id']), values['family'], path=str(values["file"]))
                    if images:
                        load_image(images[0][2], window)
                except:
                    pass
            else:
                window["id"].update(0)

        if event == "Next":
            if values['id']:
                try:
                    id = int(values['id']) + 1
                    window["id"].update(id)
                    logger.debug(f"Searching! {id} {values['family']}")
                    images = search_for_apriltag(id, values['family'], path=str(values["file"]))
                    if images:
                        load_image(images[0][2], window)
                except:
                    pass
        
        if event == "Prev":
            if values['id']:
                try:
                    id = int(values['id']) - 1
                    if id >= 0:
                        window["id"].update(id)
                        logger.debug(f"Searching! {id} {values['family']}")
                        images = search_for_apriltag(id, values['family'], path=str(values["file"]))
                        if images:
                            load_image(images[0][2], window)
                except:
                    pass
        
        if event == "Add" and images:
            logger.debug(images)
            selected_tags.append(images[0])
            logger.debug(values['-Selected-'])
            window["-Selected-"].update(selected_tags)
        
        if event == "Remove":
            logger.debug(type(window["-Selected-"].get_indexes()))
            for index in sorted(window["-Selected-"].get_indexes(), reverse=True):
                selected_tags.pop(int(index))
            logger.debug(values['-Selected-'])
            window["-Selected-"].update(selected_tags)
        
        if event == "Generate Tags":
            logger.debug(values)
            logger.debug(selected_tags)
            if selected_tags:
                upscales = upscale_tags(selected_tags, new_size=(100,100), with_legend=False, custom_text='')
                if values['-PDF-']:
                    logger.debug("Generating PDF!")
                    export_to_PDF(upscales, output_name="testtag",output_path='.//PDF//')
    
    window.close()

if __name__ == "__main__":
    main()
