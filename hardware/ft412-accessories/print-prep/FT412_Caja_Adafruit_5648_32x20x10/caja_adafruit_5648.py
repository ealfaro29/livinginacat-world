"""Caja de dos piezas para el Adafruit 5648. Dimensiones en mm.

Dependencias: numpy, trimesh, manifold3d.
Ejecutar: python caja_adafruit_5648.py
Los dos STL salen orientados con su cara plana sobre la cama.
"""
from pathlib import Path
from math import cos, pi, sin

from manifold3d import CrossSection, Manifold
import numpy as np
import trimesh

LARGO_INTERIOR = 32.0
ANCHO_INTERIOR = 20.0
ALTO_INTERIOR = 10.0
PARED = 2.2
PISO = 1.6
TECHO = 1.6
RADIO_ESQUINA = 2.0

DIAMETRO_CABLE = 6.0
CENTRO_PASACABLE = 4.5
SALIENTE_PASACABLE = 1.6
HOLGURA_CIERRE = 0.20

BASE_STL = 'FT412_Adafruit_5648_Base.stl'
TAPA_STL = 'FT412_Adafruit_5648_Tapa.stl'


def bloque(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def carcasa_exterior(z0, z1):
    x = LARGO_INTERIOR / 2 + PARED
    y = ANCHO_INTERIOR / 2 + PARED
    r = RADIO_ESQUINA
    contorno = []
    for cx, cy, angle in [(x-r, y-r, 0), (-x+r, y-r, pi/2),
                          (-x+r, -y+r, pi), (x-r, -y+r, 3*pi/2)]:
        for step in range(9):
            t = angle + step * pi / 16
            contorno.append((cx+r*cos(t), cy+r*sin(t)))
    return CrossSection([contorno]).extrude(z1-z0).translate((0, 0, z0))


def prisma_yz(contorno, x0, x1, lado):
    # Rotación que pasa el plano local XY a YZ y su extrusión al eje X.
    points = np.asarray([(lado*y, z) for y, z in contorno])
    if lado < 0:
        points = points[::-1]
    prism = CrossSection([points.tolist()]).extrude(x1-x0)
    return prism.transform(((0, 0, 1, x0), (1, 0, 0, 0), (0, 1, 0, 0)))


def cilindro_x(lado, x0, x1, r0, r1=None):
    if r1 is None:
        r1 = r0
    return (Manifold.cylinder(x1-x0, r0, r1, 96)
            .rotate((0, 90*lado, 0)).translate((lado*x0, 0, CENTRO_PASACABLE)))


def construir():
    x = LARGO_INTERIOR / 2
    y = ANCHO_INTERIOR / 2
    ox = x + PARED
    z = CENTRO_PASACABLE
    h = HOLGURA_CIERRE
    r = DIAMETRO_CABLE / 2
    if not 2.0 <= r <= 3.2:
        raise ValueError('Este labio admite pasacables de Ø4,0 a Ø6,4 mm.')

    # El piso termina en Z=0. Toda la altura entre 0 y ALTO_INTERIOR queda libre.
    base = carcasa_exterior(-PISO, 0)
    tapa = carcasa_exterior(0, ALTO_INTERIOR + TECHO)
    tapa -= bloque(-x, x, -y, y, -0.10, ALTO_INTERIOR)

    for side in (-1, 1):
        for center in (-8.0, 8.0):
            half = 3.2
            tongue = [(y, -0.08), (y+1.10, -0.08), (y+1.10, 2.50),
                      (y+0.74, 3.0), (y, 3.0)]
            tooth = [(y+1.03, 0.66), (y+1.45, 1.29),
                     (y+1.45, 1.68), (y+1.03, 2.30)]
            pocket = [(y-0.05, -0.10), (y+1.10+h, -0.10),
                      (y+1.10+h, 2.50), (y+0.79+h, 3.22), (y-0.05, 3.22)]
            tooth_relief = [(y+1.15, 0.38), (y+1.65, 0.98),
                            (y+1.65, 2.05), (y+1.15, 2.66)]
            base += prisma_yz(tongue, center-half, center+half, side)
            base += prisma_yz(tooth, center-1.45, center+1.45, side)
            tapa -= prisma_yz(pocket, center-half-h, center+half+h, side)
            tapa -= prisma_yz(tooth_relief, center-1.65, center+1.65, side)

    # Cada extremo forma un pasacables partido que se cierra con el equipo cableado.
    total_x = ox + SALIENTE_PASACABLE
    for side in (-1, 1):
        xa, xb = sorted((side*x, side*(total_x+0.2)))
        x0, x1 = sorted((side*x, side*(ox-0.08)))
        base += bloque(x0, x1, -5.42, 5.42, -0.08, z)
        tapa -= bloque(xa-0.001, xb+0.001, -5.62, 5.62, -0.10, z+h)
        collar = cilindro_x(side, ox-0.20, total_x, 5.63, 3.80)
        base += collar ^ bloque(xa-0.01, xb+0.01, -5.42, 5.42, -PISO, z)
        tapa += collar ^ bloque(xa-0.01, xb+0.01, -5.62, 5.62, z+h, ALTO_INTERIOR+TECHO)
        paso = cilindro_x(side, x-0.10, total_x+0.10, r)
        bisel = cilindro_x(side, x-0.05, x+0.45, r+0.28, r)
        base -= paso + bisel
        tapa -= paso + bisel

    return base, tapa


def convertir(solido):
    if len(solido.decompose()) != 1:
        raise ValueError('La geometría tiene componentes separados.')
    data = solido.to_mesh64()
    mesh = trimesh.Trimesh(vertices=data.vert_properties[:, :3],
                           faces=data.tri_verts, process=True)
    if not mesh.is_volume or not mesh.is_watertight:
        raise ValueError('La geometría exportada no representa un sólido cerrado.')
    return mesh


def orientar(base, tapa):
    base_cama = base.translate((0, 0, PISO))
    tapa_cama = tapa.rotate((180, 0, 0)).translate((0, 0, ALTO_INTERIOR+TECHO))
    return convertir(base_cama), convertir(tapa_cama)


def verificar(base, tapa):
    x = LARGO_INTERIOR/2
    y = ANCHO_INTERIOR/2
    interior = bloque(-x, x, -y, y, 0, ALTO_INTERIOR)
    if (base ^ interior).volume() > 0.00001 or (tapa ^ interior).volume() > 0.00001:
        raise ValueError('El cierre invade el espacio interior de la caja.')
    if (base ^ tapa).volume() > 0.00001:
        raise ValueError('Las dos piezas se superponen al quedar cerradas.')
    for side in (-1, 1):
        canal = cilindro_x(side, x, x+PARED+SALIENTE_PASACABLE, DIAMETRO_CABLE/2)
        if ((base + tapa) ^ canal).volume() > 0.00001:
            raise ValueError('El pasacables está obstruido.')


def main():
    base, tapa = construir()
    verificar(base, tapa)
    for filename, piece in zip((BASE_STL, TAPA_STL), orientar(base, tapa)):
        path = Path(__file__).parent / filename
        piece.export(path)
        exported = trimesh.load_mesh(path)
        if not exported.is_volume or not exported.is_watertight:
            raise ValueError(f"{filename} no es una malla cerrada al volver a abrirlo.")


if __name__ == '__main__':
    main()
