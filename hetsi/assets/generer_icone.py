"""Génère assets/hetsi.ico. Lancer une fois : py -m pip install pillow && py hetsi/assets/generer_icone.py"""
import os
from PIL import Image, ImageDraw

TAILLE = 256
img = Image.new("RGBA", (TAILLE, TAILLE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
# disque bleu + flèche de déplacement (design simple, sobre)
d.rounded_rectangle([28, 28, 228, 228], radius=48, fill=(55, 138, 221, 255))
d.polygon([(96, 84), (176, 128), (96, 172)], fill=(255, 255, 255, 255))
d.rectangle([70, 116, 116, 140], fill=(255, 255, 255, 255))
chemin = os.path.join(os.path.dirname(__file__), "hetsi.ico")
img.save(chemin, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
print("écrit", chemin)
