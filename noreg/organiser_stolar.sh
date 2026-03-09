#!/bin/bash
# Organiserer noreg/: for kvar GLB-fil, flytt GLB + matchande JPG inn i undermappe.
# Bilete utan GLB vert liggjande (stolar utan 3D-modell enno).
cd "$(dirname "$0")"
echo ""
echo "  ======================================"
echo "  Organiserer stolar med 3D-modellar"
echo "  ======================================"
echo ""

moved=0
shopt -s nullglob

for glb in *.glb; do
    obj_id="${glb%%_*}"
    mkdir -p "$obj_id"
    echo "  + $obj_id/$glb"
    mv "$glb" "$obj_id/"
    ((moved++))
    for jpg in "${obj_id}"_*.jpg; do
        echo "    $(basename "$jpg")"
        mv "$jpg" "$obj_id/"
        ((moved++))
    done
done

shopt -u nullglob

folders=$(find . -mindepth 1 -maxdepth 1 -type d | wc -l)
remaining=$(ls *.jpg 2>/dev/null | wc -l)

echo ""
echo "  ======================================"
echo "  $folders mapper med GLB + bilete"
echo "  $remaining bilete ventar på 3D-modell"
echo "  ======================================"
echo ""
