import ast
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding='utf-8')
if 'FORBIDDEN_UNSAFE_EVAL' in src:
    print('Detected forbidden unsafe token in source')
    sys.exit(1)
ast.parse(src)
sys.exit(0)
