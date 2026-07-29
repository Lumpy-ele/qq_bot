"""pytest 公共 fixtures。"""
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，便于 `import app...` / `import config...`
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
