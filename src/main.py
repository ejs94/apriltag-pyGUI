import glob
from msilib.schema import Error
import os
import re
from unittest import result
from loguru import logger
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

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

def create_empty_A4_page(dpi=300):
    """Create a empty A4 page based on DPI. 
    (width, height) - A4 size 210 x 297 mm

    Args:
        dpi (int, optional): DPI - dots per inch. Defaults to 300.

    Returns:
        Image: Return a Pillow Image
    """
    a4_size = mm_to_pixels(210, 297, dpi)
    blankpage = Image.new('RGB',a4_size,(255, 255, 255))
    return blankpage

def search_for_apriltag(ids,family):
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
        raise Error("List must be small that 100 ids.")
    else:
        raise ValueError("IDs must be a list or a number.")

    path = f"..\\data\\{family}\\*.png"
    loaded_tags = []

    for filename in glob.glob(path):
        founded_id = re.search("[0-9]{5}", filename)
        if founded_id:
            if founded_id.group(0) in search_ids:
                logger.info(f"Founded ID: {founded_id.group(0)}\nFamily: { family }\nIn path: { filename }")
                original_tag = Image.open(filename)
                loaded_tags.append((founded_id.group(0), family, original_tag))
    return loaded_tags

def upscale_tags(loaded_tags, new_size=(100,100), custom_text=""):
    upscaled_loaded_tags = []
    # Background size (width, height)         
    # Tagsize (width, height)
    tag_size = mm_to_pixels(new_size[0], new_size[1])
    for image in loaded_tags:
        new_blankpage = create_empty_A4_page()
        new_resize_tag = image[2].resize(tag_size, Image.Resampling.NEAREST) # Need the Image.NEAREST to remove blur
        new_position_tag = ((new_blankpage.size[0] - new_resize_tag.size[0]) // 2, (new_blankpage.size[1] - new_resize_tag.size[1]) // 2) # To center the tag
        new_blankpage.paste(new_resize_tag, new_position_tag) # Not centered, top-left corner

        draw = ImageDraw.Draw(new_blankpage)
        fnt = ImageFont.truetype('arial',100) # FontType and FontSize
        
        text = f"ID: { image[0] }\nFamily: { image[1] }\nProject: Smart ForkLift - FIT" + f"\n{custom_text}"
        
        position_text = (new_blankpage.size[0]/4, ((new_blankpage.size[1] - new_resize_tag.size[1]) / 2) + new_resize_tag.size[1] + 100 ) # Labeling location, need a better aproach 
 
        draw.text(position_text, text, (0,0,0),font=fnt)
        
        upscaled_loaded_tags.append(new_blankpage)
    return upscaled_loaded_tags

def export_to_PDF(resized_tags, output_name="tag",output_path='..//PDF//'):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    outputfile = output_path + f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{output_name}.pdf'
    resized_tags[0].save(outputfile, 'PDF', quality=100, save_all=True, append_images=resized_tags[1:])
    logger.info(f'PDF sucessful saved -- {outputfile}')

### START My use case only
def generate_id(id):
    if id >= 0 and id <=99:
        min_level = 100
        max_level = 900
        step = 100
        result = []
        for i in range(min_level, max_level+step, step):
            result.append((i+id))
        return result
    else:
        raise ValueError("ID Must be a value between 0 to 99")

def generate_street(street_list, start_id):
    warehouses = []
    for name in street_list:
        warehouses.append((name, generate_id(start_id)))
        start_id +=1
    return warehouses


def generate_warehouse_dict():
    family= "tagStandard41h12"
    W10A = {"name":"W10A", "streets":["JC", "JD", "JE", "JF", "JG", "JH", "JI", "JJ", "JK"], "start_id": 0}
    W10B = {"name":"W10B", "streets":["JL","JM","JN","JO","JP","JQ","JR","JS","JT","JU","JV","JW","JX","JY","JZ"], "start_id": 9}
    W11A = {"name":"W11A", "streets":["WA","WB","WC","WD","WE","WF","WG","WH","WI","WJ","WK","WM","WN","WO","WP","WQ","WR"], "start_id": 24}
    W11B = {"name":"W11B", "streets":["CA","CB","CC","CD","CE","CF","CG","CH","CI","CJ","CK","CL","CM","CN"], "start_id": 41}
    for warehouse_dict in [W10A, W10B, W11A, W11B]:
        for street in generate_street(warehouse_dict['streets'], warehouse_dict['start_id']):
            strt_name, list_id = street
            result_tags = search_for_apriltag( list_id, family)
            resized_tags = upscale_tags( result_tags, custom_text=f"Warehouse: {warehouse_dict['name']} Rua: {strt_name}" )
            export_to_PDF(resized_tags, strt_name)
## END My use case only

def main():
    # Families: 'tag16h5', 'tagStandard41h12', etc..
    family= "tagStandard41h12"
    result_tags = search_for_apriltag( [100, 200], family)
    resized_tags = upscale_tags( result_tags )
    export_to_PDF(resized_tags)

if __name__ == "__main__":
    with logger.catch():
        #main()
        generate_warehouse_dict()
