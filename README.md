# ui_auto_test
    基于cv2和ocr的ui自动化脚本  
##  安装依赖,也可以安装最新版本  
    `pip install -r requirements.txt`
##  目录结构
- config:配置目录，读取run_fenbao_test.py的version参数并保存，用于创建测试目录
- images:临时存放截图
- report:测试报告
- src:具体实现代码
- test:存放各版本分包目录，需要把分包apk存放到分包目录下，才可以执行分包回归
- tools:工具目录，存放一些辅助脚工具,cv2、ocr、aapt
- run_fenbao_test.py:用pytest框架执行分包测试
- run_fenbao_test1.py：用web模式，在web页面输入分包版本和全部分包连接，一键执行


##  运行示例
###  1.在test目录以版本号命名创建文件夹，也可以在run_fenbao_test.py中输入版本文件夹名称会自动创建  
###  2.将分包apk都在下载到刚刚创建的文件夹内  
###  3.然后执行run_fenbao_test.py
    ![运行示例](https://github.com/user-attachments/assets/c78c4663-d40c-4a62-a232-c546a4f892bd)    
