"""Render generated oriented STL files for geometric visual review."""
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

root = Path(__file__).resolve().parents[1] / "hardware/ft412"
data = json.loads((root / "qa/print-manifest.json").read_text())
fig = plt.figure(figsize=(16, 19), facecolor="#f7f9fc")
for i, record in enumerate(data["parts"]):
    mesh = trimesh.load_mesh(root / record["stl"])
    ax = fig.add_subplot(4, 4, i + 1, projection="3d", facecolor="#f7f9fc")
    collection = Poly3DCollection(
        mesh.triangles, facecolors="#4b91be", edgecolors="#4b91be", linewidths=0, shade=True,
        lightsource=matplotlib.colors.LightSource(azdeg=315, altdeg=45))
    ax.add_collection3d(collection)
    center = mesh.bounds.mean(axis=0)
    radius = mesh.extents.max() / 2 * 1.1
    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(0, 2 * radius)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=28, azim=-60)
    ax.set_axis_off()
    dims = " × ".join(f"{v:.1f}" for v in record["print_bbox_mm"])
    ax.set_title(record["part"].replace("_x1", "").replace("_x2", "").replace("_x4", "").replace("_", " ") +
                 f'   ×{record["quantity"]}\n' + dims + " mm",
                 fontsize=9, pad=0, color="#14243a")
fig.suptitle("DIY robot — FramingTech 355/250 + Adafruit 412\n"
             "CAD exports reviewed · no physical testing",
             fontsize=19, y=.98, color="#14243a")
fig.subplots_adjust(top=.94, bottom=.02, wspace=.02, hspace=.08)
fig.savefig(root / "qa/parts-preview.png", dpi=150, facecolor=fig.get_facecolor())
volume = sum(r["volume_mm3"] * r["quantity"] for r in data["parts"])
print(f"Total solid volume: {volume/1000:.2f} cm3")
print(f"Solid PETG estimate at1.27g/cm3: {volume/1000*1.27:.1f}g; excludes supports/coupons")

import shutil
shutil.copyfile(root / "qa/parts-preview.png", root.parents[1] / "public/assets/printed-parts.png")
