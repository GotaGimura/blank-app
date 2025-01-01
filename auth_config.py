import yaml
from yaml.loader import SafeLoader

def load_auth_config(file_path='config.yaml'):
    """
    認証設定をYAMLファイルから読み込む関数
    Args:
        file_path (str): YAMLファイルのパス（デフォルトはconfig.yaml）
    Returns:
        dict: 読み込んだ設定内容を含む辞書
    """
    with open(file_path, 'r') as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config
