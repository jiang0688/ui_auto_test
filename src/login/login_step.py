import os
import sys
current_dir_1 = os.path.dirname(os.path.abspath(__file__))
ui_auto_test_path = os.path.dirname(os.path.dirname(current_dir_1))
sys.path.append(ui_auto_test_path)

from src.core.api import *
from tools.ocr.ocr import OCR, timeit
from functools import lru_cache

from src.core.log import log

@lru_cache(maxsize=1)
def get_ocr() -> OCR:
    return OCR()

#点击更多登录方式
def click_more():
    more_img_path_qian = os.path.join(current_dir_1,"template","login_more_qian.png")
    more_img_path_an = os.path.join(current_dir_1,"template","login_more_an.png")

    try:
        pos = wait(Template(more_img_path_qian),timeout=10)
    except:
        pos = wait(Template(more_img_path_an))
    touch(pos)
    log("点击更多登录方式按钮成功，等待5秒加载邮箱登录页...")
    sleep(5)





#点击邮箱图标
def click_email_icon():
    email_img_path = os.path.join(current_dir_1,"template","login_email_qian.png")
    pos_email = wait(Template(email_img_path))
    touch(pos_email)
    sleep(1)

    log("开始使用ocr识别邮箱输入框、密码输入框、登录按钮坐标...")
    login_img_path = os.path.join(ui_auto_test_path,"images","email_login_home.png")
    snapshot(filename=login_img_path,msg="邮箱登录页截图")
    if Path(login_img_path).exists():
        log("邮箱登录页截图成功")
    else:
        log("邮箱登录页截图失败")

    ocr = get_ocr()
    result = ocr.get_all_text_positions(login_img_path)
    eml_btm_pos = [datas for datas in result if datas["text"] == '请输入邮箱或用户名']
    pwd_btn_pos = [datas for datas in result if datas["text"] == "请输入密码"]
    login_btn_pos = [datas for datas in result if datas["text"] == "登录"]

    if eml_btm_pos:
        x, y = eml_btm_pos[0]['center']
        eml_btm_pos = (float(x), float(y))

    if pwd_btn_pos:
        x, y = pwd_btn_pos[0]['center']
        pwd_btn_pos = (float(x), float(y))

    if login_btn_pos:
        x, y = login_btn_pos[0]['center']
        login_btn_pos = (float(x), float(y))

    log(f"返回坐标：邮箱输入框:{eml_btm_pos}, 密码输入框:{pwd_btn_pos}, 登录按钮:{login_btn_pos}")
    return eml_btm_pos, pwd_btn_pos, login_btn_pos



#点击邮箱输入框
def click_email_input(pos,email):
    if not pos:
        email_input_path_qian = os.path.join(current_dir_1,"template","login_input_email_qian.png")
        email_input_path_an = os.path.join(current_dir_1,"template","login_input_email_an.png")
        try:
            pos = wait(Template(email_input_path_qian),timeout=10)
        except:
            pos = wait(Template(email_input_path_an))
    touch(pos)
    log(f"输入邮箱:{email}")
    text(email)



#点击密码输入框,并输入密码
def click_password_input(pos,password):
    
    if not pos:
        pwd_img_path = os.path.join(ui_auto_test_path,"images","pwd_input.png")
        snapshot(filename=pwd_img_path)
        ocr = get_ocr()
        result = ocr.match_text(pwd_img_path,"请输入密码")
        x, y = result[0]['center']
        pos = (float(x), float(y))

    touch(pos)
    sleep(1)
    log(f"输入密码:{password}")
    text(password)


#点击登录按钮
def click_login_btn(pos):
    if not pos:
        login_img_path = os.path.join(current_dir_1,"template","login_btn_qian.png")
        pos = wait(Template(login_img_path))

    touch(pos)
    # log("成功点击登录按钮，等待30秒，加载首页UI......")
    # sleep(30)


