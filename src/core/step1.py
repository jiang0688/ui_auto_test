import os
import re
import sys
import shutil


curr_path = os.path.dirname(os.path.abspath(__file__))
ui_auto_test_path = os.path.dirname(os.path.dirname(curr_path)) #上两级目录

sys.path.append(ui_auto_test_path)
from src.core.log import log

test_path = os.path.join(ui_auto_test_path, 'test')



def list_apk_files(folder_path):
    """
    1.列出文件夹下所有 .apk 文件
    :param folder_path: 目标文件夹路径
    :return: .apk 文件路径列表
    """
    apk_files = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".apk"):
            apk_files.append(os.path.join(folder_path, filename))
    return apk_files

def extract_package_id(filename):
    """
    2.根据 apk 文件名提取分包id
    :param filename: apk 文件名
    """
    # 匹配1个大写字母+4位数字
    match = re.search(r'([A-Z][0-9]{4})', filename)
    if match:
        return match.group(1)
    return None


def create_package_dict(parent,subfolder_name):
    """
    3.根据分包id名创建文件夹
    """
    try:
        sub_path = os.path.join(parent, subfolder_name)
        os.makedirs(sub_path, exist_ok=True)
        return os.path.abspath(sub_path)
    except Exception as e:
        print(f"创建文件夹失败: {str(e)}", file=sys.stderr)
        return None

def move_apk_file(apk_file, package_id_path):
    """
    4.移动 apk 文件到分包文件夹
    """
    try:
        new_path = shutil.move(apk_file, package_id_path)
        return new_path
    except Exception as e:
        print(f"移动 apk 文件失败: {str(e)}", file=sys.stderr)
        return None


def main(folder_name):
    """
    在ui_auto_test/test/{folder_name} 目录下，
    1.提取 apk 文件，
    2.根据 apk 文件名创建分包文件夹
    3.移动 apk 文件到分包文件夹
    file_name: 文件名；如：ui_auto_test/test/1.93,则文件名输入1.93
    """
    file_apks_path = os.path.join(test_path, folder_name)

    log("开始提取APK文件")
    apk_files_list = list_apk_files(file_apks_path)
    if not apk_files_list:
        log(f"未找到APK文件")
        return
    log(f"一共{len(apk_files_list)}个APK文件")

    log("开始提取APK文件名")
    apk_files_dict = {}
    for apk_file in apk_files_list:
        package_id = extract_package_id(os.path.basename(apk_file))
        if package_id:
            apk_files_dict[package_id] = apk_file
        else:
            log(f"未找到 apk 文件名: {os.path.basename(apk_file)}", file=sys.stderr)

    log("开始创建分包文件夹")
    package_id_list = []
    for package_id, apk_file in apk_files_dict.items():
        package_id_list.append(package_id)
        package_id_path = create_package_dict(file_apks_path, package_id)
        if package_id_path:
            # log(f"创建分包文件夹: {package_id_path}")
            pass
        else:
            log(f"创建分包文件夹失败: {package_id}", file=sys.stderr)
            continue

        # log(f"开始移动 apk 文件: {os.path.basename(apk_file)}")
        new_path = move_apk_file(apk_file, package_id_path)
        if new_path:
            # log(f"移动 apk 文件成功: {new_path}")
            pass
        else:
            log(f"移动 apk 文件失败: {os.path.basename(apk_file)}", file=sys.stderr)
    log(f"分包：[{package_id_list}]")
    log("根据分包名创建目录、移动APK到分包目录成功")



if __name__ == '__main__':
    folder_name = '1.93'
    # main(folder_name)
    log("Hello, world!")