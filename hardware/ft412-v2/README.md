# FT412 V2 · Consola impresa / Printed console

**Español.** La V2 es una segunda máquina con electrónica, cámara, iPhone y movimiento dedicados. El diseño conserva libre el recorrido del carro y de los tres patines. La referencia óptica medida en V1 es **100 mm del vidrio al lente**. Con esa altura, el exterior modelado mide **196 × 302 × 231 mm**. El recorrido CAD es de 106,1 mm en X y 206,1 mm en Y. Las pruebas de montaje, cables, temperatura y carga pertenecen a la futura V2 física.

**English.** V2 is a separate machine with dedicated electronics, phone, camera and motion hardware. The console preserves clearance for the moving bridge and all three rail carriages. The V1 measurement sets the lens **100 mm above the glass**. At that height the modeled exterior is **196 × 302 × 231 mm**, with calculated travel of 106.1 mm in X and 206.1 mm in Y. Physical fit, cable routing, load and temperature still need testing on V2.

| Carpeta / Directory | Contenido / Contents |
| --- | --- |
| [Consola-tornilleria](Consola-tornilleria/) | Diseño vigente, ensamble STEP, generador paramétrico y distribución de herrajes. Current assembly, editable STEP, parametric generator and fastener layout. |
| [Fabricación · tanda 01](Fabricacion/01-Frente-y-cama-R01/) | Frente y cama con STL, STEP y dos placas PETG para boquilla de 0,4 mm. Front and phone bed with printable STL, editable STEP, and two 0.4 mm PETG plates. |
| [Consola-compacta](Consola-compacta/) · [Consola-01](Consola-01/) | Alternativas anteriores para comparar dimensiones y arquitectura. Earlier variants for comparing dimensions and architecture. |

**Para empezar a imprimir / Start printing.** [Descargar la primera tanda (ZIP) / Download print batch 01](https://livinginacat.world/downloads/ft412-v2-tanda-01.zip). Abrí el proyecto conjunto en Bambu Studio y seleccioná la placa 1 para la cama. Open the two-plate project in Bambu Studio and select plate 1 for the phone bed. [Guía ilustrada / Illustrated guide](Fabricacion/01-Frente-y-cama-R01/README.md)

La fuente externa elegida para el diseño es la MEAN WELL GST160A12-R7B (12 V, hasta 11,5 A y 138 W). La MKS recibe 12 V. El Pi 5 y el iPhone llevan convertidores dedicados. El S301T frontal conmuta corriente continua. El catálogo conserva las piezas y el presupuesto para dos máquinas independientes. [Lista V2](../../data/v2-catalog.json) · [Visor 3D](https://livinginacat.world/es/v2/#viewer)

The design uses an external MEAN WELL GST160A12-R7B (12 V, up to 11.5 A and 138 W). The MKS uses 12 V directly. Separate converters feed the Pi 5 and the iPhone. The front S301T switches DC. The catalog budgets for two independent machines. [V2 parts and estimate](https://livinginacat.world/v2/#budget)

### Regenerar / Rebuild

```sh
uv run Fabricacion/01-Frente-y-cama-R01/Fuente/generar.py
```

El generador de la tanda comprueba la huella del STEP de referencia. Para regenerar esa misma tanda directamente, usá el STEP distribuido en este repositorio. Un STEP exportado de nuevo puede llevar otra fecha en su cabecera y por tanto otra huella. The batch generator checks the reference STEP digest. Use the included STEP to reproduce that batch. Re-exporting a STEP can change its timestamp and file hash.

Para modificar y exportar la consola completa, usá `uv run Consola-tornilleria/modelo.py`. To edit and re-export the full console, run that generator separately.

Para reconstruir el proyecto de dos placas y el ZIP desde la raíz del repositorio, ejecutá el siguiente comando. To rebuild the two-plate project and download from the repository root, run the following command.

```sh
uv run --script hardware/ft412-v2/Fabricacion/01-Frente-y-cama-R01/Fuente/inicio.py --package public/downloads/ft412-v2-tanda-01.zip
```
