#----------------------------------------------
# Segmata
#----------------------------------------------
# utils.py
# ---------
#
# functions for segmata
#
# version 16.04.2025
# S.Gouttebroze
#----------------------------------------------

import os
import cv2
import numpy as np
import sys
import subprocess
import shutil
import matplotlib.pyplot as plt
from datetime import datetime
import re
import json

def calc_diff(image1_path, image2_path, display=False):
    image1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
    image2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)
    image_diff = image2.astype(np.int16) - image1.astype(np.int16)
    if display:
        print(f"Moy={np.mean(image_diff)}, min={np.min(image_diff)}; max={np.max(image_diff)}")

    if display:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        axes[0].imshow(image1, cmap='gray')
        axes[0].set_title('Image 1 (ref)')
        axes[0].axis('off')
        axes[1].imshow(image2, cmap='gray')
        axes[1].set_title('Image 2')
        axes[1].axis('off')
        axes[2].imshow(image_diff, cmap='gray')
        axes[2].set_title('Image diff')
        axes[2].axis('off')
        plt.tight_layout()
        plt.show()

    return np.mean(image_diff)

def load_obj(obj_file_path, obj_filename):
    vertices, normals, faces, comments, others = [], [], [], [], []
    with open(os.path.join(obj_file_path, obj_filename), "r") as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0] == "v":
                vertices.append([float(x) for x in parts[1:4]])
            elif parts[0] == "vn":
                normals.append([float(x) for x in parts[1:4]])
            elif parts[0] == "f":
                faces.append(line.strip())
            elif parts[0] == "#":
                comments.append(line.strip())
            else:
                others.append(line.strip())
    return vertices, normals, faces, comments, others

def save_obj(vertices, normals, faces, comments, others, path):
    with open(path, "w") as f:
        for line in comments:
            f.write(line + "\n")
        for v, n in zip(vertices, normals):
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            f.write(f"vn {n[0]} {n[1]} {n[2]}\n")
        for line in faces:
            f.write(line + "\n")
        for line in others:
            f.write(line + "\n")

def move_vertex(vertices, normals, index, distance):
    v = vertices[index]
    n = normals[index]
    return [
        v[0] + distance * n[0],
        v[1] + distance * n[1],
        v[2] + distance * n[2]
    ]

def log_print(log_path,msg):
    with open(log_path, "a") as log:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        full_msg = f"{timestamp} {msg}"
        print(full_msg)
        log.write(full_msg + "\n")
           
def display_result(output_image,image_reference):
    image1 = cv2.imread(image_reference, cv2.IMREAD_GRAYSCALE)
    image2 = cv2.imread(output_image + "_originale.jpg", cv2.IMREAD_GRAYSCALE)
    
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].imshow(image2, cmap='gray')
    axes[0].set_title('Image origin')
    axes[0].axis('off')
    axes[1].imshow(image1, cmap='gray')
    axes[1].set_title('Image optimized')
    axes[1].axis('off')
    plt.tight_layout()
    plt.show()
    
    
def display_result_vertex(vertex_number,vertex_disp):
    plt.figure(figsize=(10, 5))

    for i in range(len(vertex_number)):
        plt.plot(vertex_number[i], vertex_disp[i], marker='o', linestyle='-', label=f'Pass {i+1}')

    plt.xlabel("Vertex Number")
    plt.ylabel("Displacement")
    plt.title("Displacement vs Vertex Number")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
            
def segmata_process(log_path,obj_file_path, obj_filename, render_exe, render_args, output_image, image_reference, distance,pass_number):
    vertex_number=[]
    vertex_disp=[]
    vertices, normals, faces, comments, others = load_obj(obj_file_path, obj_filename)
    base_path = os.path.join(obj_file_path, obj_filename)
    shutil.copy(base_path, base_path + ".bak")
    
    # test
    #extract_faces_with_adjacency(vertices,normals, faces, comments, others, 10, obj_file_path+"extract_x.obj")

    save_obj(vertices, normals, faces, comments, others, os.path.join(obj_file_path, "temp_" + obj_filename))
    subprocess.run([render_exe] + render_args, stdout=sys.stdout, stderr=sys.stderr)
    shutil.copy(output_image, output_image + "_ref.jpg")
    if pass_number==0:
        # Only copy original file the first pass
        shutil.copy(output_image, output_image + "_originale.jpg")

    cpt = 0
    for i in range(len(vertices)):
        for direction in [+1, -1]:
            moved_vertices = vertices.copy()
            moved_vertices[i] = move_vertex(vertices, normals, i, direction * distance)

            temp_obj_path = os.path.join(obj_file_path, f"temp_{i}_{'p' if direction > 0 else 'm'}.obj")
            save_obj(moved_vertices, normals, faces, comments, others, temp_obj_path)

            render_args_mod = render_args.copy()
            render_args_mod[render_args_mod.index("--obj") + 1] = temp_obj_path
            subprocess.run([render_exe] + render_args_mod, stdout=sys.stdout, stderr=sys.stderr)

            diff = calc_diff(image_reference, output_image, False)
            
            #log_print(log_path,f"Sommet {i+1} ({'+' if direction > 0 else '-'}) : diff={diff}")

            if diff > 0:
                #shutil.copy(temp_obj_path, base_path + f"_{i}_{'p' if direction > 0 else 'm'}.obj")
                #shutil.copy(output_image, output_image + f"_ref_{i}_{'p' if direction > 0 else 'm'}.jpg")
                save_obj(moved_vertices, normals, faces, comments, others, base_path)
                shutil.copy(output_image, output_image + "_ref.jpg")
                vertices = moved_vertices
                log_print(log_path,f"Vertex {i+1}/{len(vertices)} moved by {'+' if direction > 0 else '-'}{distance} pixels)")
                cpt += 1
                vertex_number.append(i)
                vertex_disp.append(direction * distance)
                
                if os.path.exists(temp_obj_path): os.remove(temp_obj_path)  # Suppress file
                break
            if os.path.exists(temp_obj_path): os.remove(temp_obj_path)  # Suppress file
            
    shutil.copy(output_image, output_image + f"_opt_pass{pass_number+1}.jpg")

    log_print(log_path,"****************************")
    log_print(log_path,f"  OPTIMIZATION PASS {pass_number+1} DONE.")
    log_print(log_path,f"Vertex moved:")
    log_print(log_path,f"{cpt} of {len(vertices)} vertex")
    log_print(log_path,f"{round(100*cpt/len(vertices),0)} % of total")
    log_print(log_path,"****************************")
    
    return [vertex_number,vertex_disp]


def segmata(objfile,renderer_path,nbpass=3,display=False):
    """
    Exécute segmata pour traiter un fichier OBJ.

    Args:
        objfile (str): obj file path.
        renderer_path (str): exe file for vesuvius_render.
        nbpass (int): Total pass number. (default = 3)
        display (bool): Display or not the output curve (default=False)

    Returns:
        None
    """
    if os.path.exists(objfile):
        obj_file_path = os.path.dirname(objfile)
        obj_filename = os.path.basename(objfile)
        image_reference =os.path.join(obj_file_path,"32.jpg_ref.jpg")
        output_image_path = os.path.join(obj_file_path,"32.jpg")
        log_path = os.path.join(obj_file_path, "segmata_log.txt")
        if os.path.exists(log_path): os.remove(log_path)

        # Ouvrir et lire le fichier JSON
        jsonfile=os.path.join(obj_file_path,obj_filename.replace(".obj",".json"))
        with open(jsonfile, 'r') as file:
            data = json.load(file)

        # Récupérer les valeurs de st_width et st_height en utilisant la clé spécifiée
        key_name = os.path.splitext(obj_filename)[0]
        st_width = int(data[key_name]["st_width"])
        st_height = int(data[key_name]["st_height"])




        render_arguments = [
            "--obj", os.path.join(obj_file_path, "temp_" + obj_filename),
            "--width", str(st_width),
            "--height", str(st_height),
            "--target-dir", obj_file_path,
            "-v", "20241024131838",
            "--min-layer", "32",
            "--max-layer", "32",
            "--target-format", "jpg",
            "--data-directory", "C:\\Vesuvius"]

        log_print(log_path,"****************************")
        log_print(log_path,"  OPTIMIZATION START")
        log_print(log_path,f"  {obj_file_path} file: {obj_filename}")
        log_print(log_path,f"  width: {st_width}, height: {st_height}")
        log_print(log_path,"****************************")
        for pass_number in range(nbpass):
            log_print(log_path,f"PASS {pass_number+1}")
            segmata_process(log_path,obj_file_path, obj_filename, renderer_path, render_arguments, output_image_path, image_reference, 2,pass_number)
            log_print(log_path,"****************************")

        if display==True:
            display_result(output_image_path,image_reference)
        log_print(log_path,"****************************")
        log_print(log_path,"  OPTIMIZATION END")
        log_print(log_path,"****************************")
    else:
        print("ERROR")
        print(f"{objfile} does not exist...")
        print("END")
    