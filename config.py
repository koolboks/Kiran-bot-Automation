#### This section contain the setting section you are only allownto edit here ########
from manage_json import load_json

TELEGRAM_TOKEN='6827265715:AAEXwgOGDTCZPgSEU0V3otX_wj09w6PpFAU'
MANUAL = "no" # Yes or No
DATA_PATH = "data.csv"
ALWAYS_SHOW_PREVIEW = "yes" # yes or no this will always show pdf preview pf each page if no only wait for the last page









### DO NOT EDIT ###########

data = load_json(filename="settings.json")




if data.get("MANUAL",False):

    bot_manual_setting = True
else:
    bot_manual_setting = False




if data.get("ALWAYS_SHOW_PREVIEW", False):
    preview = True
else:
    preview = False

