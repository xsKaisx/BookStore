import pathlib
import yaml
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
def read_yaml(filepath: str) -> dict:
    with open(BASE_DIR / filepath, 'r') as f:
        res = yaml.safe_load(f)
    return res