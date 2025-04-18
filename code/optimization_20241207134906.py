#----------------------------------------------
# Segmata
#----------------------------------------------
#
# main function
#
# version 16.04.2025
# S.Gouttebroze
#----------------------------------------------

import os
import utils



###########################################################

# Exemple d'utilisation
objfile=r"C:\\Vesuvius\\20241207134906\\20241207134906.obj"
renderer_path = r"C:\\Vesuvius\\vesuvius-render-v34-x86_64-pc-windows-msvc.exe"

utils.segmata(objfile,renderer_path,30,True)

