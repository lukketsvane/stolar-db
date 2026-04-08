import os
import re
from pathlib import Path

viz_dir = Path('analysis/scripts_viz')
# The font folder is at analysis/scripts_viz/fonts
# So os.path.dirname(__file__) will be analysis/scripts_viz
# Thus os.path.join(os.path.dirname(__file__), 'fonts') is correct.

for pyfile in viz_dir.glob('*.py'):
    with open(pyfile, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update font_dir definition to be robust
    # We search for font_dir = something and replace it
    content = re.sub(r'font_dir = .*?$', "font_dir = os.path.join(os.path.dirname(__file__), 'fonts')", content, flags=re.MULTILINE)
    
    with open(pyfile, 'w', encoding='utf-8') as f:
        f.write(content)

print("Standardized all viz script font paths.")
