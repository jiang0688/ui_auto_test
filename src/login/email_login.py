from airtest.core.api import *
import logging
from airtest.core.android.adb import ADB

import os,sys
current_dir = os.path.dirname(os.path.abspath(__file__))
ui_auto_test_path = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(ui_auto_test_path)

from src.core.log import log
from tools.ocr.ocr import OCR, timeit



logging.basicConfig(level=logging.WARNING)  # 设置全局日志级别
logging.getLogger("airtest").setLevel(logging.WARNING)

# 设置全局默认超时时间为60秒
ST.FIND_TIMEOUT = 60  # 影响所有wait(), exists()等查找操作

# dev = connect_device("Android:///?cap_method=MINICAP&touch_method=MINITOUCH")

dev = connect_device("Android:///")
width, height = dev.display_info['width'], dev.display_info['height']
ocr = OCR()

@timeit
def emain_login(email, password,package_name,apk_path):
    package_list = dev.list_app()

    if package_name in package_list:
        log(f"存在旧版应用，卸载：{package_name}")
        dev.uninstall_app(package_name)
        log(f"卸载成功")

    log(f"开始安装最新版应用:{package_name}")
    dev.install_app(apk_path)

    package_list = dev.list_app()
    if package_name in package_list:
        log(f"安装成功")

    log(f"启动应用")
    dev.start_app(package_name)
    sleep(15)

    log("点击更多")
    more_img_path_qian = os.path.join(current_dir,"template","login_more_qian.png")
    more_img_path_an = os.path.join(current_dir,"template","login_more_an.png")
    try:
        pos = wait(Template(more_img_path_qian),timeout=10)
    except:
        pos = wait(Template(more_img_path_an))
    touch(pos)



    log("点击邮箱图标")
    email_img_path = os.path.join(current_dir,"template","login_email_qian.png")
    pos_email = wait(Template(email_img_path))
    touch(pos_email)

    log(f"点击输入邮箱")
    email_input_path_qian = os.path.join(current_dir,"template","login_input_email_qian.png")
    email_input_path_an = os.path.join(current_dir,"template","login_input_email_an.png")
    try:
        pos = wait(Template(email_input_path_qian),timeout=10)
    except:
        pos = wait(Template(email_input_path_an))
    touch(pos)
    log(f"输入邮箱:{email}")
    text(email)
    touch((0.1,0.1))


    log(f"点击输入密码")
    pwd_img_path_qian = os.path.join(current_dir,"template","login_input_email_pwd_qian.png")
    pwd_img_path_an = os.path.join(current_dir,"template","login_input_email_pwd_an.png")
    try:
        pos = wait(Template(pwd_img_path_qian),timeout=10)
    except:
        pos = wait(Template(pwd_img_path_an))
    touch(pos)
    sleep(1)
    log(f"输入密码:{password}")
    text(password)

    log("点击其他地方尝试关闭输入法弹窗")
    touch((0.1,0.1))

    log("点击登录按钮")
    login_img_path = os.path.join(current_dir,"template","login_btn_qian.png")
    pos_login_btn = wait(Template(login_img_path))
    touch(pos_login_btn)

    sleep(30)

    log("断言装扮商城入口是否存在")
    home_img_path = os.path.join(current_dir,"template","home_qian.png")
    snapshot(filename=home_img_path)
    target_text = "装扮商城"
    result = ocr.match_text(home_img_path,target_text)
    log(f"装扮商城入口是否存在：{result}")


    if not result:
        log(f"未找到 {target_text}")
        return False
    else:

        log("登录成功")
        return True




if __name__ == '__main__':
    email = "a222@end.tw"
    password = "12345678"
    package_name = "com.newlang.weelife"
    apk_path = r"D:\Download\982-meta-android-global-v1.94.0.0.982_290-STABLE-release_v1.94.0-release_1.94_Android-Debug-20250818114015.apk"

    # emain_login(email, password, package_name, apk_path)



    pwd_img_path_qian = os.path.join(current_dir,"template","login_input_email_pwd_qian.png")
    pwd_img_path_an = os.path.join(current_dir,"template","login_input_email_pwd_an.png")
    # try:
    #     pos = wait(Template(pwd_img_path_qian),timeout=10)
    #     log("浅色")
    # except:
    #     pos = wait(Template(pwd_img_path_an))
    #     log("深色")
    # log(pos)
    # touch(pos)
    # sleep(1)
    # log(f"输入密码:{password}")
    ppp = r"E:\A1myProject\python\UiAuto\ui_auto_test\images\home.png"
    result = ocr.get_all_text_positions(ppp)
    print(result)

    data = [datas for datas in result if datas["text"] == "登录"]
    data1 = [datas for datas in result if datas["text"] == "请输入邮箱或用户名"]
    data2 = [datas for datas in result if datas["text"] == "请输入密码"]

    log(data)
    log(data1)
    log(data2)





