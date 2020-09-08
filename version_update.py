import psutil
from bs4 import BeautifulSoup
import sys
from PyQt5.QtWidgets import QDialog, QApplication
import os
import requests
from update import Ui_dialog
from PyQt5.QtCore import QThread, pyqtSignal
import shutil
from subprocess import Popen
server_location = sys.argv[1]
runable_programm = sys.argv[2]
download_url = server_location
download_flag = False
update_content = None
with open('version.txt', 'r', encoding ='utf-8') as fo_:
    my_version = fo_.read()
with open('version.txt', 'wb') as fileobj:
    # 请求更新文件包
    f = requests.get(download_url, stream=True)
    soup = BeautifulSoup(f.text, 'lxml')
    text = soup.find_all('a')
    version_list = [str(x) for x in text if 'update' in str(x) and '.zip' in str(x)]
    if version_list: ##找到最近的更新
        last_version = version_list[-1]
        server_version = last_version[last_version.find('>')+1:last_version.find('</')]
        if server_version != my_version: #如果最近的更新和现在的版本不同
            fileobj.write(bytes(server_version, encoding='utf-8'))
            download_flag = True
            print("write done! new")
            version_document = server_version.replace('.zip', '.txt')
            vd = requests.get(server_location+version_document, stream=True) ##读取更新的版本内容
            with open('version_document.txt', 'wb') as fd:
                for chunk in vd.iter_content(chunk_size=1660376):
                    fd.write(chunk)
            update_content = open('version_document.txt', encoding= 'utf-8').read()
        else: ##如果相同的话，结束更新程序
            fileobj.write(bytes(my_version, encoding='utf-8'))
            print("write done! old")

class Download(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_dialog()
        self.ui.setupUi(self)
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setVisible(False)
        self.ui.pushButton_ok.clicked.connect(self.download)
        self.ui.pushButton_cancel.clicked.connect(self.cancel)
        self.ui.textBrowser.setText(update_content)
        self.ui.label.setText('程序有新的版本，是否进行更新？')
        self.complete = False
    def UpProgress(self, value):
        self.ui.progressBar.setVisible(True)
        if value == 0:
            self.ui.label.setText('正在向服务器请求数据...')
            self.ui.progressBar.setMaximum(0)
            self.ui.progressBar.setMinimum(0)

        if value == 1:
            self.ui.label.setText('正在下载数据...')

        if value == 99:
            self.ui.label.setText('正在解压缩文件...')

        if value == 100:
            self.complete = True
            self.ui.label.setText("程序已成功更新！")
            self.ui.progressBar.close()
            self.ui.pushButton_cancel.setText('确认')

    def download(self):
        self.ui.pushButton_ok.setVisible(False)
        self.proc = Thread_progress()
        self.proc.trigger.connect(self.UpProgress)
        self.proc.start()
        self.ui.label.setText('正在向服务器请求数据...')

    def cancel(self):
        if self.complete:
            Popen(runable_programm)
        super().close()

class Thread_progress(QThread):
    trigger = pyqtSignal(int)

    def __init__(self):
        super(Thread_progress, self).__init__()
    def run(self):
        download_update_url = os.path.join(download_url, server_version)
        with open(server_version, 'wb') as fileobj__:
            # 请求更新文件包
            self.trigger.emit(0)
            f = requests.get(download_update_url, stream=True)
            offset = 0
            print('------------------')
            self.trigger.emit(1)
            for chunk in f.iter_content(chunk_size=1660376):
                if not chunk:
                    break
                fileobj__.seek(offset)
                fileobj__.write(chunk)
                offset = offset + len(chunk)
        ##如果程序在运行则结束当前的进程
        for proc in psutil.process_iter():
            if proc.name() == runable_programm:
                proc.kill()
        self.trigger.emit(99)
        ##将更新包解压到当前的文件夹
        shutil.unpack_archive(
            filename=server_version,
            extract_dir=os.path.abspath(os.path.dirname('__file__'))
        )
        ##删除下载的更新包
        os.remove(server_version)
        self.trigger.emit(100)

if __name__ == "__main__":
    if download_flag:
        app = QApplication(sys.argv)
        form = Download()
        form.show()
        sys.exit(app.exec_())
