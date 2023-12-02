import pathlib
import yaml
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
with open(BASE_DIR / 'config.yml') as config_file:
    config = yaml.safe_load(config_file)
