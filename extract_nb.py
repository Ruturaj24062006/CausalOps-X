import json
import codecs

nb_path = "artifacts/model2/v9_source_recovery/model2_v9_training_source.ipynb"
out_path = "extracted_v9_source.py"

with codecs.open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

with codecs.open(out_path, 'w', encoding='utf-8') as out:
    for i, cell in enumerate(nb.get("cells", [])):
        if cell["cell_type"] == "code":
            out.write(f"# CELL {i}\n")
            source = cell.get("source", [])
            if isinstance(source, list):
                out.write("".join(source) + "\n\n")
            else:
                out.write(source + "\n\n")

print("Extraction complete.")
