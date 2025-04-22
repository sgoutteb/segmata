#----------------------------------------------
# Segmata
#----------------------------------------------
# utils.py
# ---------
#
# functions for segmata
# Major improvement in speed
# Add stats for moved points
#
# version 22.04.2025
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
import smtplib
from scipy.spatial import cKDTree

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders



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
    
def display_result_best_points_number(bptab):
    plt.figure(figsize=(10, 5))

    plt.plot(bptab, marker='o', linestyle='none')

    plt.xlabel("pass nr")
    plt.ylabel("Moved vertex number")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
def display_result_vertex(vertex_number,vertex_disp,obj_file_path):
    plt.figure(figsize=(10, 5))

    plt.plot(vertex_number, vertex_disp, marker='o', linestyle='none')

    plt.xlabel("Vertex Number")
    plt.ylabel("Displacement")
    plt.title("Displacement vs Vertex Number")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    # Dictionnaire pour accumuler les valeurs par indice
    accumulated_values = {}

    # Parcourir les listes et accumuler les valeurs
    for indice, valeur in zip(vertex_number, vertex_disp):
        if indice in accumulated_values:
            accumulated_values[indice] += valeur
        else:
            accumulated_values[indice] = valeur

    # Convertir le dictionnaire en listes d'indices uniques et de valeurs cumulÃ©es
    unique_indices = list(accumulated_values.keys())
    cumulated_values = list(accumulated_values.values())

    # Trier les indices et les valeurs cumulÃ©es pour un traÃ§age correct
    unique_indices, cumulated_values = zip(*sorted(zip(unique_indices, cumulated_values)))

    # Tracer les valeurs cumulÃ©es en fonction des indices uniques
    plt.figure(figsize=(10, 6))
    plt.plot(unique_indices, cumulated_values, marker='o', linestyle='-')
    plt.xlabel('Vertex')
    plt.ylabel('Cumulated displacement (px)')
    plt.grid(True)
    plt.show()
    
    
    # Calcul des statistiques
    stats = {
        'mean': np.mean(cumulated_values),
        'median': np.median(cumulated_values),
        'sigma': np.std(cumulated_values),
        'minimum': np.min(cumulated_values),
        'maximum': np.max(cumulated_values),
        '1st_quartile': np.percentile(cumulated_values, 25),
        '3rd_quartile': np.percentile(cumulated_values, 75),
        'range': np.max(cumulated_values) - np.min(cumulated_values),
        'mean_abs': np.mean(np.abs(cumulated_values)),
        'median_abs': np.median(np.abs(cumulated_values)),
        'sigma_abs': np.std(np.abs(cumulated_values)),
    }
    
    
    # Charger le fichier CSV
    file_path = os.path.join(obj_file_path, 'points.csv')
    points = np.loadtxt(file_path, delimiter=',', skiprows=1)  # skiprows=1 pour ignorer l'en-tête

    image = cv2.imread(os.path.join(obj_file_path,"32.jpg_ref.jpg"))
    pts=points[vertex_number,0:2]
    for (x, y) in pts:
        #print(f"x,y = {int(image.shape[1]*x)},{int(image.shape[0]*y)}")
        cv2.circle(image, (int(image.shape[0]*x),int(image.shape[1]*y)), radius=5, color=(0, 0, 255), thickness=-1)
    cv2.imwrite(os.path.join(obj_file_path,"moved_points.jpg"), image)
    
    
    return stats
    


def send_email(subject, body, to_email, from_email, smtp_server, smtp_port, username, password, log_path,attachment_path=None,):
    """
    Envoie un email avec une pièce jointe optionnelle.

    Args:
        subject (str): Sujet de l'email.
        body (str): Corps de l'email.
        to_email (str): Adresse email du destinataire.
        from_email (str): Adresse email de l'expéditeur.
        smtp_server (str): Serveur SMTP.
        smtp_port (int): Port SMTP.
        username (str): Nom d'utilisateur pour l'authentification SMTP.
        password (str): Mot de passe pour l'authentification SMTP.
        log_path (str): log path name
        attachment_path (str, optional): Chemin du fichier à joindre. Par défaut, None.

    Returns:
        None
    """
    # Créer l'objet email
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Ajouter le corps de l'email
    msg.attach(MIMEText(body, 'plain'))

    # Ajouter la pièce jointe si un chemin de fichier est fourni
    if attachment_path:
        try:
            # Ouvrir le fichier en mode binaire
            with open(attachment_path, 'rb') as attachment:
                # Créer un objet MIMEBase
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())

                # Encoder le fichier en base64
                encoders.encode_base64(part)

                # Ajouter l'en-tête à la pièce jointe
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(attachment_path)}'
                )

                # Joindre le fichier à l'email
                msg.attach(part)
        except Exception as e:
            log_print(log_path,f"Erreur lors de l'ajout de la pièce jointe: {e}")
            return

    server = None
    try:
        # Établir une connexion sécurisée avec le serveur SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        # Se connecter au serveur SMTP
        server.login(username, password)

        # Envoyer l'email
        server.sendmail(from_email, to_email, msg.as_string())

        log_print(log_path,"Email successfully sent!")

    except smtplib.SMTPAuthenticationError:
        log_print(log_path,"Erreur d'authentification. Vérifiez votre nom d'utilisateur et votre mot de passe.")
    except smtplib.SMTPConnectError:
        log_print(log_path,"Erreur de connexion au serveur SMTP. Vérifiez les paramètres du serveur et du port.")
    except Exception as e:
        log_print(log_path,f"Erreur lors de l'envoi de l'email: {e}")

    finally:
        # Fermer la connexion au serveur SMTP si elle a été établie
        if server is not None:
            server.quit()
 
 
def calculate_average_distance(points):
    tree = cKDTree(points)
    distances, _ = tree.query(points, k=2)  # k=2 pour obtenir la distance au plus proche voisin
    return np.mean(distances[:, 1])  # On prend la colonne 1 car la colonne 0 est la distance à lui-même


def select_points_with_distance_constraint(points, fraction, distance_threshold):
    # Sélectionner aléatoirement  des points
    num_points_to_select = int(len(points) * fraction)
    selected_indices = np.random.choice(len(points), num_points_to_select, replace=False)
    selected_points = points[selected_indices]

    # Déterminer les limites de la grille
    min_x, max_x = np.min(points[:, 0]), np.max(points[:, 0])
    min_y, max_y = np.min(points[:, 1]), np.max(points[:, 1])
    
    

    # Calculer la taille des cellules de la grille
    cell_size = distance_threshold
    num_cells_x = int((max_x - min_x) / cell_size) + 1
    num_cells_y = int((max_y - min_y) / cell_size) + 1

    # Créer une grille pour suivre les points dans chaque cellule
    grid = {(i, j): [] for i in range(num_cells_x) for j in range(num_cells_y)}

    # Ajouter les indices des points sélectionnés à la grille
    for idx, point in zip(selected_indices, selected_points):
        cell_x = int((point[0] - min_x) / cell_size)
        cell_y = int((point[1] - min_y) / cell_size)
        grid[(cell_x, cell_y)].append(idx)

    # Filtrer les points pour éliminer ceux qui sont trop proches
    filtered_indices = []
    for cell, indices_in_cell in grid.items():
        if len(indices_in_cell) > 0:
            # Ajouter un point par cellule (ou aucun si tous les points sont trop proches)
            filtered_indices.append(indices_in_cell[0])
    
    return np.array(filtered_indices)


def segmata_process(log_path,obj_file_path, obj_filename, render_exe, render_args, output_image, image_reference, distance,pass_number):
    vertex_number=[]
    vertex_disp=[]
    best_points_nb=0
    vertices, normals, faces, comments, others = load_obj(obj_file_path, obj_filename)
    base_path = os.path.join(obj_file_path, obj_filename)
    shutil.copy(base_path, base_path + ".bak")
    
    # test
    #extract_faces_with_adjacency(vertices,normals, faces, comments, others, 10, obj_file_path+"extract_x.obj")

    #save_obj(vertices, normals, faces, comments, others, os.path.join(obj_file_path, "temp_" + obj_filename))
    render_args[render_args.index("--obj") + 1] = base_path
    #log_print(log_path,f"{render_args}")
    
    subprocess.run([render_exe] + render_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy(output_image, output_image + "_ref.jpg")
    if pass_number==0:
        # Only copy original file the first pass
        shutil.copy(output_image, output_image + "_originale.jpg")

    # Charger le fichier CSV
    file_path = os.path.join(obj_file_path, 'points.csv')
    points = np.loadtxt(file_path, delimiter=',', skiprows=1)  # skiprows=1 pour ignorer l'en-tête

    fraction = 0.2
    distance_moy=calculate_average_distance(points[:,0:2])
    if pass_number==0:
        log_print(log_path,f"Distance moyenne: {distance_moy}")
    distance_threshold = 5*distance_moy  # For ensuring no adjacent points
    cpt=0


    selected_points = select_points_with_distance_constraint(points, fraction, distance_threshold)
    
    log_print(log_path,f"{len(selected_points)} Selected points / {len(points)} total.")
    for direction in [-1,1]:
        #log_print(log_path,f"Direction: {direction}")
        #log_print(log_path,f"Chargement fichier {obj_file_path} {obj_filename}")
        vertices, normals, faces, comments, others = load_obj(obj_file_path, obj_filename)
        new_vertices=vertices.copy()
        moved_vertices = vertices.copy()
        
        for i in selected_points:  # on deplace tous les points selectionnés 
            moved_vertices[i][0]=moved_vertices[i][0]+direction*distance*normals[i][0]
            moved_vertices[i][1]=moved_vertices[i][1]+direction*distance*normals[i][1]
            moved_vertices[i][2]=moved_vertices[i][2]+direction*distance*normals[i][2]


        temp_obj_path = os.path.join(obj_file_path, f"temp_inter.obj")
        save_obj(moved_vertices, normals, faces, comments, others, temp_obj_path)
        #log_print(log_path,f"Sauvegarde fichier {temp_obj_path}")
        
        render_args_mod = render_args.copy()
        render_args_mod[render_args_mod.index("--obj") + 1] = temp_obj_path
        #log_print(log_path,f"{render_args_mod}")
        subprocess.run([render_exe] + render_args_mod, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        #diff = calc_diff(image_reference, output_image, False)
        image1 = cv2.imread(image_reference, cv2.IMREAD_GRAYSCALE)
        image2 = cv2.imread(output_image, cv2.IMREAD_GRAYSCALE)
        #image_diff = image2 - image1
        #cv2.imwrite(f"0_before.png", image1)
        #cv2.imwrite(f"0_intermediate.png", image2)
        #cv2.imwrite(f"0_diff.png", image_diff)
        image_diff = image2.astype(np.int16) - image1.astype(np.int16)
        
        # il faut maintenant aller regarder chaque point selectionné si le resultat est meilleur ou pas
        best_points=[]
        for i in selected_points:
            
            rayon=25 #distance in pixels
            xc=int(image_diff.shape[1]*points[i,0])
            yc=int(image_diff.shape[0]*points[i,1])
            #print(f"XC= {xc} - YC= {yc} - Valeur centre zone= {image_diff[yc,xc]}  image1: {image1[yc,xc]} image2: {image2[yc,xc]} ")
            x_min, x_max = max(0, xc - rayon), min(image_diff.shape[1], xc + rayon + 1)
            y_min, y_max = max(0, yc - rayon), min(image_diff.shape[0], yc + rayon + 1)
            # Calculer la moyenne
            if (x_max > x_min) & (y_max > y_min):
                moyenne = np.mean(image_diff[y_min:y_max,x_min:x_max ])
            else:
                moyenne=0
            #log_print(log_path,f"XC= {xc} - YC= {yc} - moy={moyenne}")
            
            if moyenne>0:
                best_points.append(i)
                
        cpt=cpt+len(best_points)
        log_print(log_path,f"Displ. {direction*distance}px / {len(best_points)} vertex moved")
        # On ecrit maintenant le nouveau fichier obj avec les best points
        #log_print(log_path,f"Chargement fichier {obj_file_path} {obj_filename}")
        vertices, normals, faces, comments, others = load_obj(obj_file_path, obj_filename)
        new_vertices=vertices.copy()
        if best_points:
            best_points_nb+=len(best_points)
            for i in best_points:  # on deplace tous les points selectionnés 
                new_vertices[i][0]=new_vertices[i][0]+direction*distance*normals[i][0]
                new_vertices[i][1]=new_vertices[i][1]+direction*distance*normals[i][1]
                new_vertices[i][2]=new_vertices[i][2]+direction*distance*normals[i][2]
                vertex_number.append(int(i))
                vertex_disp.append(direction * distance)
                

        temp_obj_path = os.path.join(obj_file_path, f"temp_after.obj")
        save_obj(new_vertices, normals, faces, comments, others, temp_obj_path)
        #log_print(log_path,f"Sauvegarde fichier {temp_obj_path}")
        render_args_mod = render_args.copy()
        render_args_mod[render_args_mod.index("--obj") + 1] = temp_obj_path
        #log_print(log_path,f"{render_args_mod}")
        subprocess.run([render_exe] + render_args_mod, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        # on met a jour le fichier
        #log_print(log_path,f"Update obj file {temp_obj_path}-->{base_path}")
        shutil.copy(temp_obj_path, base_path)
        #save_obj(new_vertices, normals, faces, comments, others, base_path)
            

        #shutil.copy(output_image, output_image + f"_opt_pass{pass_number+1}.jpg")

    log_print(log_path,"****************************")
    log_print(log_path,f"  OPTIMIZATION PASS {pass_number+1} DONE.")
    log_print(log_path,f"Vertex moved: {cpt}")
    log_print(log_path,"****************************")
        
    # send_email every 100 pass_number
    if pass_number>0 and pass_number % 100 == 0:
        send_email(
            subject="Segmata - results",
            body=f"""Fichier: {base_path}  OPTIMIZATION PASS {pass_number+1} DONE.
            """,
            to_email="xxx@yahoo.com",
            from_email="xxx@gmail.com",
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="xxx@gmail.com",
            password="xxxxxxxxxxx",
            attachment_path=output_image + "_ref.jpg",
            log_path=log_path)

    return vertex_number,vertex_disp,best_points_nb


def segmata(objfile,renderer_path,nbpass=30,display=False):
    """
    Exécute segmata pour traiter un fichier OBJ.

    Args:
        objfile (str): obj file path.
        renderer_path (str): exe file for vesuvius_render.
        nbpass (int): Total pass number. (default = 30)
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

        vertex_number=[]
        vertex_disp=[]
        bp_tab=[]

        render_arguments = [
            "--obj", os.path.join(obj_file_path, "temp_" + obj_filename),
            "--width", str(st_width),
            "--height", str(st_height),
            "--target-dir", obj_file_path,
            "-v", "20241024131838",
            "--min-layer", "32",
            "--max-layer", "32",
            "--target-format", "jpg",
            "--data-directory", "F:\\Vesuvius"]

        log_print(log_path,"****************************")
        log_print(log_path,"  OPTIMIZATION START")
        log_print(log_path,f"  {obj_file_path} file: {obj_filename}")
        log_print(log_path,f"  width: {st_width}, height: {st_height}")
        log_print(log_path,"****************************")
        for pass_number in range(nbpass):
            log_print(log_path,f"PASS {pass_number+1}")
            vn,vd,bp=segmata_process(log_path,obj_file_path, obj_filename, renderer_path, render_arguments, output_image_path, image_reference, 2,pass_number)
            vertex_number.append(vn)
            vertex_disp.append(vd)
            bp_tab.append(bp)
            log_print(log_path,"****************************")

        if display==True:
            vertex_number= [item for sublist in vertex_number for item in sublist]
            vertex_disp= [item for sublist in vertex_disp for item in sublist]
            display_result_best_points_number(bp_tab)
            display_result(output_image_path,image_reference)
            stats=display_result_vertex(vertex_number,vertex_disp,obj_file_path)
        log_print(log_path,"****************************")
        log_print(log_path,f"vertex moved {len(vertex_number)} ")
        log_print(log_path,stats)
        log_print(log_path," ")
        log_print(log_path,"  OPTIMIZATION END")
        log_print(log_path,"****************************")
    else:
        print("ERROR")
        print(f"{objfile} does not exist...")
        print("END")
    

