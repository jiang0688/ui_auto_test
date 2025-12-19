import os,sys

current_dir = os.path.dirname(os.path.abspath(__file__))
ui_auto_test_path = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(ui_auto_test_path)

from src.core.api import download_apk

def do_download_apk(save_path):
    apk_urls = [
        "http://seafile.evkland.cn/f/d5f9d45260514affacf3/",
        "http://seafile.evkland.cn/f/667c2e88eecb45c7bdf9/",
        "http://seafile.evkland.cn/f/53029b40c7554cd599b8/",
        "http://seafile.evkland.cn/f/92cd2aecf0c646d6a308/",
        "http://seafile.evkland.cn/f/2842a2fa6d3d416b9cd1/",
        "http://seafile.evkland.cn/f/ba27e015d20e4c8ea0e5/"
    ]
    for url in apk_urls:
        download_apk(url, save_path)

if __name__ == '__main__':
    folder_name = "1.94.1"
    save_path = os.path.join(ui_auto_test_path, 'test',folder_name)
    do_download_apk(save_path)