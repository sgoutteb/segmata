#----------------------------------------------
# Segmata
#----------------------------------------------
#
# main function
#
# version 04.04.2025
# S.Gouttebroze
#----------------------------------------------

import os
import utils


# Exemple d'utilisation
obj_file_path = "C:\\Vesuvius\\20241207134906\\"
obj_filename = "20241207134906.obj"
renderer_path = r"C:\\Vesuvius\\vesuvius-render-v34-x86_64-pc-windows-msvc.exe"
output_image_path = r"C:\\Vesuvius\\20241207134906\\32.jpg"
image_reference = r"C:\\Vesuvius\\20241207134906\\32.jpg_ref.jpg"
log_path = os.path.join(obj_file_path, "segmata_log.txt")
if os.path.exists(log_path): os.remove(log_path)

render_arguments = [
    "--obj", os.path.join(obj_file_path, "temp_" + obj_filename),
    "--width", "2159",
    "--height", "684",
    "--target-dir", obj_file_path,
    "-v", "20241024131838",
    "--min-layer", "32",
    "--max-layer", "32",
    "--target-format", "jpg",
    "--data-directory", "C:\\Vesuvius"]

utils.log_print(log_path,"****************************")
utils.log_print(log_path,"  OPTIMIZATION START")
utils.log_print(log_path,"****************************")
for pass_number in range(3):
    utils.log_print(log_path,f"PASS {pass_number+1}")
    utils.segmata(log_path,obj_file_path, obj_filename, renderer_path, render_arguments, output_image_path, image_reference, 2,pass_number)
    utils.log_print(log_path,"****************************")

utils.display_result(output_image_path,image_reference)

