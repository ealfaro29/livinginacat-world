"""Remate y adaptador del FT412. Unidades en milímetros."""
from pathlib import Path

from manifold3d import CrossSection, Manifold
import trimesh

TUBO_DIAMETRO_EXTERIOR = 5.0
HOLGURA_TUBO = 0.22
ARO_DIAMETRO = 8.83
ARO_ALTO = 4.55
MALLA_DIAMETRO = 7.90
ARO_ASIENTO_DIAMETRO = 9.30
APERTURA_MALLA = 8.30

REMATE = 'FT412_Remate_Tubo_5mm.stl'
ADAPTADOR = 'FT412_Adaptador_Tubo_5mm_Punta_Malla.stl'


def tornear(profile):
    return CrossSection([profile]).revolve(96)


def remate():
    radio = (TUBO_DIAMETRO_EXTERIOR+HOLGURA_TUBO)/2
    return tornear([
        (4.13, 0), (4.39, .26), (4.39, 1.10), (4.13, 1.36),
        (4.13, 7.60), (3.95, 8.00),
        (radio+.27, 8.00), (radio, 7.70), (radio, 3.02),
        (2.0, 2.39), (2.0, .48), (2.27, 0),
    ])


def ranura(ancho, radio_boca, z0, z1):
    y = ancho/2
    return CrossSection([[(-.05,-y),(2.9,-y),(7.5,-radio_boca),
                          (7.5,radio_boca),(2.9,y),(-.05,y)]]).extrude(z1-z0).translate((0,0,z0))


def adaptador():
    radio_tubo = (TUBO_DIAMETRO_EXTERIOR+HOLGURA_TUBO)/2
    radio_aro = ARO_ASIENTO_DIAMETRO/2
    radio_salida = APERTURA_MALLA/2
    cuerpo = tornear([
        (4.30, 0), (4.50, .20), (4.50, 4.00), (6.19, 6.17),
        (6.19, 17.20), (5.96, 17.50),
        (radio_salida+.15, 17.50), (radio_salida, 17.34), (radio_salida, 16.95),
        (radio_aro, 16.45), (radio_aro, 11.50), (2.73, 11.50),
        (2.73, 6.25), (1.86, 6.25), (1.86, 5.66),
        (radio_tubo, 4.90), (radio_tubo, .28), (radio_tubo+.25, 0),
    ])
    # El aro entra de costado. El escalón de 8,30 mm sujeta el metal y deja libre la malla.
    cuerpo -= ranura(5.56, 3.00, 6.15, 11.55)
    cuerpo -= ranura(8.70, 4.70, 11.49, 17.65)
    return cuerpo


def cilindro(diametro, z0, z1):
    return Manifold.cylinder(z1-z0, diametro/2, circular_segments=96).translate((0,0,z0))


def verificar(r, a):
    if (r ^ cilindro(TUBO_DIAMETRO_EXTERIOR, 3.03, 8.00)).volume() > 1e-5:
        raise ValueError('El tubo no cabe en el remate.')
    if (a ^ cilindro(TUBO_DIAMETRO_EXTERIOR, 0, 4.90)).volume() > 1e-5:
        raise ValueError('El tubo no cabe en el adaptador.')
    aro = cilindro(ARO_DIAMETRO,11.58,11.58+ARO_ALTO)
    stem = cilindro(4.90,6.68,11.58)
    malla = cilindro(MALLA_DIAMETRO,11.58+ARO_ALTO,18.20)
    if (a ^ (aro+stem+malla)).volume() > 1e-5:
        raise ValueError('El adaptador invade el volumen de la punta.')
    if (a ^ aro.translate((0,0,1.0))).volume() <= .001:
        raise ValueError('Falta retención axial en el aro.')


def exportar(solid, path):
    m = solid.to_mesh64()
    mesh = trimesh.Trimesh(vertices=m.vert_properties[:,:3],faces=m.tri_verts,process=True)
    mesh.export(path)
    check = trimesh.load_mesh(path)
    if not check.is_volume or not check.is_watertight or len(check.split()) != 1:
        raise ValueError(f'{path.name} debe ser un solo sólido cerrado.')
    print(path.name, 'mm:', check.extents.round(2).tolist(), 'caras:',len(check.faces))


if __name__=='__main__':
    r, a = remate(), adaptador()
    verificar(r,a)
    root = Path(__file__).parent
    exportar(r,root/REMATE)
    exportar(a,root/ADAPTADOR)
