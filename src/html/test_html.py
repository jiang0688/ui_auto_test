import sys
import time
import re

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
    sys.stdout.flush()


    


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("请提供版本号和链接文件路径")
        sys.exit(1)
    
    version = sys.argv[1]
    links = sys.argv[2]
    url_list = []
    urls = re.findall(r'https?://[^\s]+', links)

    for i, url in enumerate(urls, 1):
        url_list.append(url)
    

    print("下载链接列表：", url_list)
    if len(url_list) == 0:
        print("链接列表为空，请检查链接文件路径")
        sys.exit(1)

    # log("测试完成！")
    log("===TEST_COMPLETED===")