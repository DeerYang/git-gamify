import sys
from pathlib import Path
from rich.console import Console

# 全局 Rich Console 实例
console = Console()

# 定义项目中的关键路径
# 这是确保打包后也能找到资源文件的关键
# 我们现在从 __file__ (当前文件位置) 来相对地寻找
CODE_DIR = Path(__file__).parent
DEFINITIONS_DIR = CODE_DIR / "definitions"
LOCALES_DIR = CODE_DIR / "locales"

# 用户数据目录保持不变
DATA_DIR = Path.home() / ".git-gamify"
DATA_FILE = DATA_DIR / "data.json"

# 创建数据目录（如果不存在）
DATA_DIR.mkdir(exist_ok=True)