# save_load.py
import json

SAVE_SETTINGS_PATH = "settings.json"

def save_options(game, path=SAVE_SETTINGS_PATH):
    """메뉴 옵션만 저장 (모드/조커/인원 등)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(game.opts, f, ensure_ascii=False, indent=2)

def load_options(game, path=SAVE_SETTINGS_PATH):
    """저장된 옵션만 로드하여 game.opts에 반영. 진행 상태는 건드리지 않음."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            opts = json.load(f)
    except FileNotFoundError:
        return False
    # 존재하는 키만 덮어쓰기(안전)
    for k in game.opts.keys():
        if k in opts:
            game.opts[k] = opts[k]
    return True