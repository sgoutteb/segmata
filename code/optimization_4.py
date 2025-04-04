#----------------------------------------------
# Segmata
#----------------------------------------------
#
#
# version 04.04.2025
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

def calc_diff(image1_path, image2_path, display=False):
    image1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
    image2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)
    image_diff = image2.astype(np.int16) - image1.astype(np.int16)
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
    vertices, normals, faces, others = [], [], [], []
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
            else:
                others.append(line.strip())
    return vertices, normals, faces, others

def save_obj(vertices, normals, faces, others, path):
    with open(path, "w") as f:
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
            
def segmata(log_path,obj_file_path, obj_filename, render_exe, render_args, output_image, image_reference, distance,pass_number):
    vertices, normals, faces, others = load_obj(obj_file_path, obj_filename)
    base_path = os.path.join(obj_file_path, obj_filename)
    shutil.copy(base_path, base_path + ".bak")

    save_obj(vertices, normals, faces, others, os.path.join(obj_file_path, "temp_" + obj_filename))
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
            save_obj(moved_vertices, normals, faces, others, temp_obj_path)

            render_args_mod = render_args.copy()
            render_args_mod[render_args_mod.index("--obj") + 1] = temp_obj_path
            subprocess.run([render_exe] + render_args_mod, stdout=sys.stdout, stderr=sys.stderr)

            diff = calc_diff(image_reference, output_image, False)
            log_print(log_path,f"Sommet {i+1} ({'+' if direction > 0 else '-'}) : diff={diff}")

            if diff > 0:
                shutil.copy(temp_obj_path, base_path + f"_{i}_{'p' if direction > 0 else 'm'}.obj")
                shutil.copy(output_image, output_image + f"_ref_{i}_{'p' if direction > 0 else 'm'}.jpg")
                save_obj(moved_vertices, normals, faces, others, base_path)
                shutil.copy(output_image, output_image + "_ref.jpg")
                vertices = moved_vertices
                log_print(log_path,f"Sommet {i+1} déplacé (direction: {'+' if direction > 0 else '-'})")
                cpt += 1
                break

    log_print(log_path,f"Optimisation terminée, {cpt} sommets déplacés")

# Exemple d'utilisation
obj_file_path = "C:\\Vesuvius\\segment_test\\"
obj_filename = "segment_test.obj"
renderer_path = r"C:\\Vesuvius\\vesuvius-render-v34-x86_64-pc-windows-msvc.exe"
output_image_path = r"C:\\Vesuvius\\segment_test\\32.jpg"
image_reference = r"C:\\Vesuvius\\segment_test\\32.jpg_ref.jpg"
log_path = os.path.join(obj_file_path, "segmata_log.txt")
if os.path.exists(log_path):
    os.remove(log_path)

render_arguments = [
    "--obj", os.path.join(obj_file_path, "temp_" + obj_filename),
    "--width", "593",
    "--height", "527",
    "--target-dir", obj_file_path,
    "-v", "20241024131838",
    "--min-layer", "32",
    "--max-layer", "32",
    "--target-format", "jpg",
    "--data-directory", "C:\\Vesuvius"
]

log_print(log_path,"****************************")
log_print(log_path,"  OPTIMIZATION START")
log_print(log_path,"****************************")
for pass_number in range(3):
    log_print(log_path,f"PASS {pass_number+1}")
    segmata(log_path,obj_file_path, obj_filename, renderer_path, render_arguments, output_image_path, image_reference, 2,pass_number)
    log_print(log_path,"****************************")

display_result(output_image_path,image_reference)

