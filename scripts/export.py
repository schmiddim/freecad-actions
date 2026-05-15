import FreeCAD, Mesh, Part
import os, glob

os.makedirs("exports", exist_ok=True)

for fcstd in glob.glob("**/*.FCStd", recursive=True):
    doc = FreeCAD.openDocument(fcstd)
    name = os.path.splitext(os.path.basename(fcstd))[0]
    
    for obj in doc.Objects:
        if obj.isDerivedFrom("Part::Feature") and not obj.Shape.isNull():
            Mesh.export([obj], f"exports/{name}.stl")
            Part.export([obj], f"exports/{name}.step")
            break  # erstes valides Objekt
    
    FreeCAD.closeDocument(doc.Name)
