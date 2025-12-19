import os
import sys
import pytest
import subprocess
from datetime import datetime


current_dir = os.path.dirname(os.path.abspath(__file__))
ui_auto_test_path = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(ui_auto_test_path)

from src.core.api import *
from src.login.login_step import *
from conftest import log


#获取版本号
version_json_path = os.path.join(ui_auto_test_path,'configs',"version.json")
with open(version_json_path, 'r', encoding='utf-8') as f:
    version = json.load(f)["version"]




def get_datas(folder_path):
    """获取测试数据"""
    target_folder = os.path.join(ui_auto_test_path,'test',folder_path)
    data_list = []
    for path in get_dir_list(target_folder):
        config_path = os.path.join(path,'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        # log(config)

        data ={
            "folder_path": path,
            "data": config
        }
        data_list.append(data)
    return data_list


#获取测试数据
DATAS = get_datas(version)

#邮箱登录测试用例
class Test_Email_Login:

    def setup_class(self):
        log("\n-----------初始化测试环境-----------")


        ST.FIND_TIMEOUT = 60  # 影响所有wait(), exists()等查找操作
        try:
            self.dev = connect_device("Android:///")
            self.dev.shell("echo ping")
            log(f"✅设备连接成功：{self.dev.uuid}")
        except Exception as e:
            log(f"❌ 设备连接失败：{e}")
            pytest.exit(str(e), returncode=1)   # 让 pytest 直接报错，不再继续执行用例


    def teardown_class(self):
        home()
        log("-----------结束测试-----------")
        self.dev.disconnect()

    @pytest.mark.parametrize('data', DATAS)
    def test_email_login(self, data,request):
        folder_path = data['folder_path']       #包体分区目录
        data = data['data']
        email = data['email']                   # 邮箱
        password = data['password']             # 密码
        package_id = data['package_id']         # 分区id
        apk_file = data['apk_file']             # apk文件路径
        package_name = data['package_name']     # 包名
        version = data['version']               # 包体版本

        log("")
        log(f"========= 开始执行分包：{package_id}  =========")
        package_list = self.dev.list_app()

        if package_name in package_list:
            log(f"存在旧版应用，卸载：{package_name}")
            self.dev.uninstall_app(package_name)
            log(f"卸载成功")

        log(f"开始安装最新版应用:{apk_file}")
        log(f"包体版本号：{version}")
        self.dev.install_app(apk_file)

        package_list = self.dev.list_app()
        if package_name in package_list:
            log(f"安装成功")

        log(f"启动应用，等待20秒进入登录页面......")
        self.dev.start_app(package_name)
        sleep(20)





        log("点击更多登录方式按钮")
        safe_step("点击更多按钮",click_more)


        log("点击邮箱图标")
        eml_btn_pos, pwd_btn_pos, login_btn_pos = safe_step("点击邮箱图标",click_email_icon)

        log(f"点击输入邮箱")
        safe_step("点击输入邮箱",lambda:click_email_input(eml_btn_pos,email))
        touch((0.1,0.1))    #用于关闭输入法

        log(f"点击输入密码")
        safe_step("点击输入密码",lambda:click_password_input(pwd_btn_pos,password))
        touch((0.1,0.1))    #用于关闭输入法

        log("点击登录按钮")
        safe_step("点击登录按钮",lambda:click_login_btn(login_btn_pos))
        log("等待30秒，加载首页UI......")
        sleep(30)


        home_img_path = os.path.join(ui_auto_test_path,"images",f"{package_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_home.png")
        log("开始截图，进行断言文本匹配......")
        log(f"截图路径:{home_img_path}")
        snapshot(filename=home_img_path)

        target_text = "装扮商城"
        ocr = get_ocr()
        result = ocr.match_text(home_img_path,target_text)
        log(f"匹配结果：{result}")

        img_ocr_result_path = os.path.join(ui_auto_test_path,"images",f"{package_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_ocr_result.png") #ocr处理结果图片路径
        ocr.save_result_image(img_ocr_result_path)

        success = bool(result)
        log(f"测试结果：{success}")
        json_path = os.path.join(folder_path,"config.json")
        log(f"将测试结果写入json文件：{json_path}")
        modify_json(json_path,success)

        request.node.add_screenshot_path(img_ocr_result_path,"断言结果")#把断言结果图片加入到测试报告中



        log(f"========= 结束执行分包：{package_id},测试结果：{success} =========")

        assert result, f"首页目标文本:{target_text}未匹配到，失败包体：{package_id}"
        log(f"登录成功，匹配结果：{result}\n")


def main(report=False):
    """
    report: 是否生成测试报告
    """
    current_script = os.path.abspath(__file__)


    if report:
        html_path = os.path.join(ui_auto_test_path,'report', f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        subprocess.run([
            sys.executable, "-m", "pytest",
            current_script,
            "-sv",
            f"--html={html_path}",
            "--self-contained-html",
            "--tb=short",           #只显示错误信息

        ]) 
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 已生成测试报告：{html_path}")
    else:
        subprocess.run([
            sys.executable, "-m", "pytest", 
            current_script,
            "-sv",
            "--tb=short",
    ]) 


if __name__ == '__main__':
    main(True)

