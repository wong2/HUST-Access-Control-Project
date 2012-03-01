#-*-coding:utf-8-*-

import sys, hashlib, os
import sqlite3 as sqlite
from datetime import datetime
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import qrc_resources
import AccessControl

__version__ = "1.0.0"

class MainWindow(QMainWindow):

    def __init__(self, id, is_admin, parent=None):
        super(MainWindow, self).__init__(parent)
        self.uid = id
        self.is_admin = is_admin
        self.id_name_buffer = {}
        self.file_info_buffer = {}
        self.aac = AccessControl.AutoAccessControl()

        self.setFixedSize(690, 400)
        self.setWindowTitle(u"自主访问控制实验系统")

        self.cwidget = QWidget()

        self.file_list = QTableWidget(0, 4)
        self.file_list.setHorizontalHeaderLabels(QStringList([u"名称", u"创建者", u"大小"]))
        self.file_list.hideColumn(3)
        self.file_list.setColumnWidth(0, 230)
        self.file_list.setColumnWidth(1, 150)
        self.file_list.setColumnWidth(2,128)
        self.file_list.setShowGrid(False)
        self.file_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        h_header = self.file_list.horizontalHeader()
        h_header.setHighlightSections(False)
        h_header.setDefaultAlignment(Qt.AlignLeft)
        self.file_list.verticalHeader().hide()
        self.connect(self.file_list, SIGNAL("itemSelectionChanged()"), self.fileSelected)

        self.con = sqlite.connect("db.db")
        self.con.text_factory = lambda x: unicode(x, "utf-8", "ignore")
        c = self.con.cursor()
        c.execute("select name, owner, size, id from object order by name")
        for row in c:
            self.showFile(row[0], self.getUserNameById(row[1]), row[2], row[3])

        self.file_info = QTextBrowser()
        self.file_info.setFixedHeight(110)

        left_widgets = QWidget()
        left_vbox = QVBoxLayout()
        left_vbox.addWidget(self.file_list)
        left_vbox.addWidget(self.file_info)
        left_widgets.setLayout(left_vbox)

        button_group = QGroupBox(u"操作")
        self.read_button = QPushButton(u"读文件")
        self.write_button = QPushButton(u"写文件")
        self.delete_button = QPushButton(u"删文件")
        self.execute_button = QPushButton(u"执行文件")
        right_vbox = QVBoxLayout()
        right_vbox.setContentsMargins(20, 20, 20, 0)
        right_vbox.setSpacing(15)
        right_vbox.setAlignment(Qt.AlignTop)
        right_vbox.addWidget(self.read_button)
        right_vbox.addWidget(self.write_button)
        right_vbox.addWidget(self.delete_button)
        right_vbox.addWidget(self.execute_button)
        button_group.setLayout(right_vbox)
        self.buttons = [self.read_button, self.write_button, self.delete_button,
            self.execute_button]
        for button in self.buttons:
            button.setEnabled(False)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(0,5,20,0)
        hbox.addWidget(left_widgets)
        hbox.addWidget(button_group)
        self.cwidget.setLayout(hbox)
        self.setCentralWidget(self.cwidget)

        subjectNewAction = self.createAction(u"新建主体...", self.subjectNew,
            "Ctrl+N", None, u"创建新的主体")
        subjectManageAction = self.createAction(u"管理主体...", self.subjectManage,
            "Ctrl+M", None, u"管理主体")
        subjectChangePwdAction = self.createAction(u"修改密码...", self.subjectChangePwd,
            None, None, u"修改我的密码")

        subjectMenu = self.menuBar().addMenu(u"主体(&S)")
        self.addActions(subjectMenu, (subjectNewAction,subjectManageAction,subjectChangePwdAction))
        
        if not self.is_admin:
            subjectNewAction.setEnabled(False)
            subjectManageAction.setEnabled(False)

        objectNewAction = self.createAction(u"新建客体...", self.objectNew,
            None, None, u"创建新的客体")
        objectImportAction = self.createAction(u"导入客体...", self.objectImport,
            None, None, u"从文件系统导入客体")

        objectMenu = self.menuBar().addMenu(u"客体(&O)")
        self.addActions(objectMenu, (objectNewAction,objectImportAction))
        
        permNewAction = self.createAction(u"新的授权...", self.permNew, 
            None, None, u"创建一个新的自主授权")
        permManageAction = self.createAction(u"管理授限...", self.permManage,
            None, None, u"管理自主授权")

        permMenu = self.menuBar().addMenu(u"权限(&P)")
        self.addActions(permMenu, (permNewAction, permManageAction))

        aboutAction = self.createAction(u"关于",
            lambda: QMessageBox.about(self, u"关于", u"作者：wong2.cn"), None, None, "About")
        aboutQtAction = self.createAction(u"关于Qt",
            lambda: QMessageBox.aboutQt(self, u"关于Qt"), None, None, "About Qt")
        helpMenu = self.menuBar().addMenu(u"帮助(&H)")
        self.addActions(helpMenu, (aboutQtAction, aboutAction))

        '''
        fileToolbar = self.addToolBar("File")
        fileToolbar.setObjectName("FileToolBar")
        self.addActions(fileToolbar, (fileNewAction, ))
        '''

        status = self.statusBar()
        status.showMessage("Ready", 5000)

        self.connect(self.read_button, SIGNAL("clicked()"), self.showReadFileDlg)
        self.connect(self.write_button, SIGNAL("clicked()"), self.showWriteFileDlg)
        self.connect(self.delete_button, SIGNAL("clicked()"), self.showDeleteFileDlg)
        self.connect(self.execute_button, SIGNAL("clicked()"), lambda:QMessageBox.information(self,"No",u"浮云"))

    def showFile(self, name, owner, size, id):
        row = self.file_list.rowCount()
        self.file_list.insertRow(row)
        self.file_list.setItem(row, 0, QTableWidgetItem(QString(name)))
        self.file_list.setItem(row, 1, QTableWidgetItem(QString(owner)))
        self.file_list.setItem(row, 2, QTableWidgetItem(QString(str(size)+"B")))
        self.file_list.setItem(row, 3, QTableWidgetItem(QString(str(id))))

    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def fileSelected(self):
        row = self.file_list.currentRow()
        f_id = int(self.file_list.item(row, 3).text())
        file_info = self.getFileInfoById(f_id)
        self.updateFileInfo(file_info)
        for i in range(4):
            if self.is_admin:
                self.buttons[i].setEnabled(True)
            else:
                self.buttons[i].setEnabled(self.aac.determine(self.uid, f_id, i))
    def updateFileInfo(self, file_info):
        self.file_info.setHtml(u'''
            <b>文件名:</b> %s<br>
            <b>字节数:</b> %s字节<br>
            <b>创建者:</b> %s<br>
            <b>创建于:</b> %s<br>
            <b>修改于:</b> %s<br>'''
            % (file_info['name'], file_info['size'], file_info['owner'],
               file_info['ctime'], file_info['atime']))

    def getUserNameById(self, id):
        if id in self.id_name_buffer:
            return self.id_name_buffer[id]
        res = self.con.execute("select * from subject where id=?", (id,)).fetchone()
        name = res[1]
        self.id_name_buffer[id] = name
        return name

    def getFileInfoById(self, f_id):
        if f_id in self.file_info_buffer:
            return self.file_info_buffer[f_id]
        fields = []
        res = self.con.execute('select name,size,owner,a_time,c_time\
            from object where id=?', (f_id,)).fetchone()
        file_info = dict(zip(['name','size','owner','atime','ctime'], res))
        file_info['owner'] = self.getUserNameById(file_info['owner'])
        file_info['atime'] = file_info['atime'].split('.')[0]
        file_info['ctime'] = file_info['ctime'].split('.')[0]
        self.file_info_buffer[f_id] = file_info
        return file_info

    def showReadFileDlg(self):
        row = self.file_list.currentRow()
        f_id = int(self.file_list.item(row, 3).text())
        res = self.con.execute("select name,content from object where id=?", (f_id,)).fetchone()
        title = u"查看 %s" % res[0]
        content = res[1]
        read_only_dlg = ReadOnlyDialog(title, content, self)
        read_only_dlg.exec_()

    def showWriteFileDlg(self):
        row = self.file_list.currentRow()
        f_id = int(self.file_list.item(row, 3).text())
        res = self.con.execute("select name,content from object where id=?", (f_id,)).fetchone()
        title = u"编辑 %s" % res[0]
        content = res[1]
        write_dlg = WriteDialog(title, content, f_id, row, self)
        write_dlg.exec_()

    def showDeleteFileDlg(self):
        msgBox = QMessageBox()
        msgBox.setWindowTitle(u"确认删除？")
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText(u"你确认要删除该文件吗？");
        msgBox.setInformativeText(u"木有回收站");
        msgBox.addButton(u"别拦我", QMessageBox.YesRole)
        msgBox.addButton(u"那算了吧", QMessageBox.RejectRole)
        ret = msgBox.exec_();
        if ret == QMessageBox.AcceptRole:
            row = self.file_list.currentRow()
            f_id = int(self.file_list.item(row, 3).text())
            self.con.execute("delete from object where id=?", (f_id,))
            self.con.execute("delete from authorize where object=?", (f_id,))
            self.con.commit()
            self.file_list.removeRow(row)

    def subjectNew(self):
        new_subject_dlg = NewSubjectDialog(self)
        new_subject_dlg.exec_()

    def subjectManage(self):
        new_manage_subject_dlg = ManageSubjectDialog(self)
        new_manage_subject_dlg.exec_()

    def subjectChangePwd(self):
        change_pwd_dlg = ChangePwdDialog(self)
        change_pwd_dlg.exec_()

    def objectNew(self):
        new_object_dlg = NewObjectDialog(self)
        new_object_dlg.exec_()

    def objectImport(self):
        fname = unicode(QFileDialog.getOpenFileName(self, u"选择要导入的文本文件...",
            "", "Text files (*.txt)"))
        if not fname:
            return
        
        with open(fname) as fp:
            raw_content = fp.read()
            try:
                content = raw_content.decode("gb2312").encode("utf-8")
            except:
                content = raw_content
        title = os.path.basename(fname)
        
        if self.con.execute("select id from object where name=?", (title,)).fetchone():
            QMessageBox.critical(self, u"错误", u"文件名%s已存在" % title)
        elif len(content) > 2047:
            QMessageBox.critical(self, u"错误", u"文件内容太长，请勿超过2048字节")
        else:
            self.con.execute("insert into object values(?,?,?,?,?,?,?)",
                (None, title, content, len(content), self.uid, 
                 datetime.now(), datetime.now()))
            o_id = self.con.execute("select id from object where name=?",
                (title,)).fetchone()[0]
            for access in range(6):
                self.con.execute("insert into authorize values(?,?,?,?,?)",
                    (None, self.uid, access, o_id, 0))
            self.con.commit()
            QMessageBox.information(self, u"成功", u"客体%s导入成功！" % title)
            self.showFile(title, self.getUserNameById(self.uid), 
                len(content), o_id)
            
    def permNew(self):
        new_perm_dlg = NewPermDialog(self)
        new_perm_dlg.exec_()
    
    def permManage(self):
        manage_perm_dlg = ManagePermDialog(self)
        manage_perm_dlg.exec_()
        
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)

        self.setWindowTitle(u"自主访问控制实验")
        self.setFixedSize(270, 220)

        label_intro = QLabel(u"<h2>登录到系统</h2>")
        label_intro.setContentsMargins(0, 0, 0, 20)
        label_name = QLabel(u"用户名：")
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText(u"在此输入用户名")
        label_pwd = QLabel(u"密码：")
        self.input_pwd = QLineEdit()
        self.input_pwd.setPlaceholderText(u"在此输入密码")
        self.input_pwd.setEchoMode(QLineEdit.Password)
        self.input_pwd.setContentsMargins(0, 0, 0, 30)
        button_ok = QPushButton(u"登录")
        button_ok.setFixedHeight(30)
        self.connect(button_ok, SIGNAL("clicked()"), self.doLogin)

        vbox = QVBoxLayout()
        vbox.addWidget(label_intro)
        vbox.addWidget(label_name)
        vbox.addWidget(self.input_name)
        vbox.addWidget(label_pwd)
        vbox.addWidget(self.input_pwd)
        vbox.addWidget(button_ok)
        self.setLayout(vbox)

    def doLogin(self):
        name = self.input_name.text()
        pwd = self.input_pwd.text()
        id, is_admin = AccessControl.isValidUser(str(name), str(pwd))
        if id:
            self.done(id*10+is_admin)
        else:
            QMessageBox.critical(self, u"登录错误", u"用户名或密码错误,请重新输入！")
            
            self.input_name.selectAll()
            self.input_name.setFocus()
            
class ReadOnlyDialog(QDialog):

    def __init__(self, title, text, parent=None):
        super(ReadOnlyDialog, self).__init__(parent)

        self.setWindowTitle(unicode(title))

        self.text_browser = QTextBrowser()
        self.text_browser.setPlainText(text)
        self.button = QPushButton(u"确认")

        vbox = QVBoxLayout()
        vbox.addWidget(self.text_browser)
        vbox.addWidget(self.button)
        self.setLayout(vbox)

        self.connect(self.button, SIGNAL("clicked()"), self.accept)

class WriteDialog(QDialog):

    def __init__(self, title, text, id, row, parent=None):
        super(WriteDialog, self).__init__(parent)

        self.changed = False
        self.id = id
        self.row = row
        self.setWindowTitle(unicode(title))
        self.parent = parent

        self.text_editor = QTextEdit()
        self.text_editor.setPlainText(text)

        self.ok_button = QPushButton(u"保存")
        self.cancel_button = QPushButton(u"取消")
        hbox = QHBoxLayout()
        hbox.addWidget(self.ok_button)
        hbox.addWidget(self.cancel_button)
        h_widget = QWidget()
        h_widget.setLayout(hbox)

        vbox = QVBoxLayout()
        vbox.addWidget(self.text_editor)
        vbox.addWidget(h_widget)
        self.setLayout(vbox)

        self.connect(self.text_editor, SIGNAL("textChanged()"), self.setChanged)
        self.connect(self.ok_button, SIGNAL("clicked()"), self.saveFile)
        self.connect(self.cancel_button, SIGNAL("clicked()"), self.reject)

    def setChanged(self):
        self.changed = True

    def saveFile(self):
        if self.changed:
            new_content = unicode(self.text_editor.toPlainText())
            self.parent.con.execute("update object set content=?,size=?,a_time=? where id=?",
                (new_content, len(new_content), datetime.now(), self.id))
            self.parent.con.commit()
            self.parent.file_list.setItem(self.row, 2,
                QTableWidgetItem(unicode(len(new_content))+"B"))
            self.parent.file_info_buffer[self.id]['size'] = len(new_content)
            self.parent.file_info_buffer[self.id]['atime'] = str(datetime.now()).split(".")[0]
            self.parent.updateFileInfo(self.parent.file_info_buffer[self.id])
        self.accept()

class NewSubjectDialog(QDialog):
    def __init__(self, parent=None):
        super(NewSubjectDialog, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle(u"创建新主体")
        
        label_name = QLabel(u"用户名:")
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText(u"在此输入用户名")
        label_pwd = QLabel(u"密码:")
        self.input_pwd = QLineEdit()
        self.input_pwd.setPlaceholderText(u"在此输入密码")
        self.input_pwd.setEchoMode(QLineEdit.Password)
        label_pwd2 = QLabel(u"密码(第二遍):")
        self.input_pwd2 = QLineEdit()
        self.input_pwd2.setPlaceholderText(u"再输一遍密码")
        self.input_pwd2.setEchoMode(QLineEdit.Password)
        
        button_ok = QPushButton(u"确认")
        button_cancel = QPushButton(u"取消")
        
        grid = QGridLayout()
        grid.addWidget(label_name, 0, 0)
        grid.addWidget(self.input_name, 0, 1)
        grid.addWidget(label_pwd, 1, 0)
        grid.addWidget(self.input_pwd, 1, 1)
        grid.addWidget(label_pwd2, 2, 0)
        grid.addWidget(self.input_pwd2, 2, 1)
        grid.addWidget(button_ok, 3, 0)
        grid.addWidget(button_cancel, 3, 1)
        self.setLayout(grid)
        
        self.connect(button_ok, SIGNAL("clicked()"), self.addSubject)
        self.connect(button_cancel, SIGNAL("clicked()"), self.reject)
    
    def addSubject(self):
        name = unicode(self.input_name.text())
        pwd = unicode(self.input_pwd.text())
        pwd2 = unicode(self.input_pwd2.text())
        
        if not name.strip():
            QMessageBox.critical(self, u"错误", u"用户名不能为空")
        elif self.parent.con.execute("select id from subject where name=?", 
            (name,)).fetchone():
            QMessageBox.critical(self, u"错误", u"用户名 %s 已被占用" % name)
            self.input_name.selectAll()
            self.input_name.setFocus()
        elif pwd != pwd2:
            QMessageBox.critical(self, u"错误", u"两次输入的密码不同" % name)
            self.input_pwd.selectAll()
            self.input_pwd.setFocus()
        elif not pwd.strip():
            QMessageBox.critical(self, u"错误", u"密码不能为空")
        else:
            self.parent.con.execute("insert into subject values(?,?,?,?)",
                (None, name, hashlib.md5(pwd).hexdigest(), False))
            self.parent.con.commit()
            self.accept()
            QMessageBox.information(self, u"成功", u"新主体 %s 创建成功！" % name)
            
class ChangePwdDialog(QDialog):
    def __init__(self, parent=None):
        super(ChangePwdDialog, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle(u"修改密码")
        
        label_old = QLabel(u"旧密码:")
        self.input_old = QLineEdit()
        self.input_old.setPlaceholderText(u"在此输入旧密码")
        label_pwd = QLabel(u"新密码:")
        self.input_pwd = QLineEdit()
        self.input_pwd.setPlaceholderText(u"在此输入新密码")
        self.input_pwd.setEchoMode(QLineEdit.Password)
        label_pwd2 = QLabel(u"新密码(第二遍):")
        self.input_pwd2 = QLineEdit()
        self.input_pwd2.setPlaceholderText(u"再输一遍新密码")
        self.input_pwd2.setEchoMode(QLineEdit.Password)
        
        button_ok = QPushButton(u"确认")
        button_cancel = QPushButton(u"取消")
        
        grid = QGridLayout()
        grid.addWidget(label_old, 0, 0)
        grid.addWidget(self.input_old, 0, 1)
        grid.addWidget(label_pwd, 1, 0)
        grid.addWidget(self.input_pwd, 1, 1)
        grid.addWidget(label_pwd2, 2, 0)
        grid.addWidget(self.input_pwd2, 2, 1)
        grid.addWidget(button_ok, 3, 0)
        grid.addWidget(button_cancel, 3, 1)
        self.setLayout(grid)
        
        self.connect(button_ok, SIGNAL("clicked()"), self.changePwd)
        self.connect(button_cancel, SIGNAL("clicked()"), self.reject)
    
    def changePwd(self):
        old = str(self.input_old.text())
        pwd = str(self.input_pwd.text())
        pwd2 = str(self.input_pwd2.text())
        
        res = self.parent.con.execute("select pwd from subject where id=?", 
            (self.parent.uid,)).fetchone()
        if res[0] != hashlib.md5(old).hexdigest():
            QMessageBox.critical(self, u"错误", u"你输入的旧密码不正确！")
            self.input_old.selectAll()
            self.input_old.setFocus()
        elif pwd != pwd2:
            QMessageBox.critical(self, u"错误", u"两次输入的新密码不同")
            self.input_pwd.selectAll()
            self.input_pwd.setFocus()
        else:
            self.parent.con.execute("update subject set pwd=? where id=?",
                (hashlib.md5(pwd).hexdigest(), self.parent.uid))
            self.parent.con.commit()
            self.accept()
            QMessageBox.information(self, u"成功", u"密码修改成功！")

class NewObjectDialog(QDialog):

    def __init__(self, parent=None):
        super(NewObjectDialog, self).__init__(parent)

        self.setWindowTitle(u"编辑新客体")
        self.setFixedSize(400, 300)
        self.parent = parent

        label_title = QLabel(u"文件名:")
        self.input_title = QLineEdit()
        
        label_content = QLabel(u"内容:")
        self.text_editor = QTextEdit()
        
        self.ok_button = QPushButton(u"保存")
        self.cancel_button = QPushButton(u"取消")
        hbox = QHBoxLayout()
        hbox.addWidget(self.ok_button)
        hbox.addWidget(self.cancel_button)
        h_widget = QWidget()
        h_widget.setLayout(hbox)

        vbox = QVBoxLayout()
        vbox.addWidget(label_title)
        vbox.addWidget(self.input_title)
        vbox.addWidget(label_content)
        vbox.addWidget(self.text_editor)
        vbox.addWidget(h_widget)
        self.setLayout(vbox)

        self.connect(self.ok_button, SIGNAL("clicked()"), self.saveFile)
        self.connect(self.cancel_button, SIGNAL("clicked()"), self.reject)

    def saveFile(self):
        title = unicode(self.input_title.text()).strip()
        content = unicode(self.text_editor.toPlainText()).strip()
        if not title:
            QMessageBox.critical(self, u"错误", u"文件名不能为空")
        elif not self.parent.con.execute("select id from object where name=?", (title,)):
            QMessageBox.critical(self, u"错误", u"文件名%s已存在" % title)
        elif len(content) > 2048:
            QMessageBox.critical(self, u"错误", u"文件内容太长，请勿超过2048字节")
        else:
            self.parent.con.execute("insert into object values(?,?,?,?,?,?,?)",
                (None, title, content, len(content), self.parent.uid, 
                 datetime.now(), datetime.now()))
            o_id = self.parent.con.execute("select id from object where name=?",
                (title,)).fetchone()[0]
            for access in range(6):
                self.parent.con.execute("insert into authorize values(?,?,?,?,?)",
                    (None, self.parent.uid, access, o_id, 0))
            self.parent.con.commit()
            self.accept()
            QMessageBox.information(self, u"成功", u"客体%s创建成功！" % title)
            self.parent.showFile(title, self.parent.getUserNameById(self.parent.uid), 
                len(content), o_id)
            
class NewPermDialog(QDialog):
    
    def __init__(self, parent=None):
        super(NewPermDialog, self).__init__(parent)
        
        self.setWindowTitle(u"创建新的自主授权")
        self.setFixedSize(350, 240)
        self.parent = parent
        
        label_s = QLabel(u"选择主体：")
        self.combo_s = QComboBox()
        result = self.parent.con.execute("select id,name from subject where \
        not id=? and is_admin != 'Y'",
            (self.parent.uid,)).fetchall()
        [[1, 'wong2'], [2, 'zhang3'], [5, 'zhu4']]
        self.s_id_list = [subject[0] for subject in result]
        
        self.combo_s.addItems([subject[1] for subject in result])
        
        hbox1 = QHBoxLayout()
        hbox1.addWidget(label_s)
        hbox1.addWidget(self.combo_s)
        hbox1_widget = QWidget()
        hbox1_widget.setLayout(hbox1)
        
        label_o = QLabel(u"选择客体：")
        self.combo_o = QComboBox()
        can_controls = self.parent.con.execute(
            "select object from authorize where subject=? and access=?",
            (self.parent.uid, 5)
        ).fetchall()
        result2 = []
        for tmpl in can_controls:
            id = tmpl[0]
            result2.append(self.parent.con.execute(
                "select id,name from object where id=?",
                (id,)
            ).fetchone())
        self.o_id_list = [object[0] for object in result2]
        
        self.combo_o.addItems([object[1] for object in result2])
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(label_o)
        hbox2.addWidget(self.combo_o)
        hbox2_widget = QWidget()
        hbox2_widget.setLayout(hbox2)
        
        label_a = QLabel(u"选择权限：")
        self.combo_a = QComboBox()
        self.combo_a.addItems([u"读", u"写", u"执行"])
        self.a_id_list = [0, 1, 3]
        
        hbox3 = QHBoxLayout()
        hbox3.addWidget(label_a)
        hbox3.addWidget(self.combo_a)
        hbox3_widget = QWidget()
        hbox3_widget.setLayout(hbox3)
        
        ok_button = QPushButton(u"确定")
        cancel_button = QPushButton(u"取消")
        if self.combo_o.count()==0 or self.combo_s.count()==0:
            ok_button.setDisabled(True)
        hbox4 = QHBoxLayout()
        hbox4.addWidget(ok_button)
        hbox4.addWidget(cancel_button)
        hbox4_widget = QWidget()
        hbox4_widget.setLayout(hbox4)
        
        vbox = QVBoxLayout()
        vbox.addWidget(hbox1_widget)
        vbox.addWidget(hbox2_widget)
        vbox.addWidget(hbox3_widget)
        vbox.addWidget(hbox4_widget)
        
        self.setLayout(vbox)
        
        self.connect(ok_button, SIGNAL("clicked()"), self.createNewPerm)
        self.connect(cancel_button, SIGNAL("clicked()"), self.reject)
    
    def createNewPerm(self):
        s_id = self.s_id_list[self.combo_s.currentIndex()]
        o_id = self.o_id_list[self.combo_o.currentIndex()]
        a_id = self.a_id_list[self.combo_a.currentIndex()]
        
        res = self.parent.con.execute(
            "select id from authorize where 'from'=? and subject=? and object=? \
             and access=?",
            (self.parent.uid, s_id, o_id, a_id)
        ).fetchone()
        if res == None:
            self.parent.con.execute(
                "insert into authorize values(?,?,?,?,?)",
                (None, s_id, a_id, o_id, self.parent.uid)
            )
            self.parent.con.commit()
        self.accept()
        QMessageBox.information(self, u"成功", u"授权成功！")
        
 
class ManagePermDialog(QDialog):
        
    def __init__(self, parent=None):
        super(ManagePermDialog, self).__init__(parent)
        
        self.setWindowTitle(u"管理自主授权")
        self.setFixedSize(440, 300)
        self.parent = parent
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            QStringList([u"客体", u"权限", u"接收者"])
        )
        self.table.hideColumn(3)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2,100)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        h_header = self.table.horizontalHeader()
        h_header.setHighlightSections(False)
        h_header.setDefaultAlignment(Qt.AlignLeft)
        self.table.verticalHeader().hide()
        
        results = self.parent.con.execute(
            "select id,subject,access,object from authorize where `from`=?",
            (self.parent.uid,)
        ).fetchall()
                
        for result in results:
            print result
            self.showItem(result[0], self.parent.getUserNameById(result[1]), 
                result[2], self.parent.con.execute(
                    "select name from object where id=?", (result[3],)).fetchone()[0]
            )
        
        button_retri = QPushButton(u"回收")
        button_close = QPushButton(u"关闭")
        hbox = QHBoxLayout()
        hbox.addWidget(button_retri)
        hbox.addWidget(button_close)
        hbox_widget = QWidget()
        hbox_widget.setLayout(hbox)        
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.table)
        vbox.addWidget(hbox_widget)
        
        self.setLayout(vbox)
        
        self.connect(button_retri, SIGNAL("clicked()"), self.retrieve)
        self.connect(button_close, SIGNAL("clicked()"), self.reject)
        
    def showItem(self, id, subject, access, object):
        row = self.table.rowCount()
        self.table.insertRow(row)
        access = [u"读", u"写", u"删除", u"执行"][access]
        self.table.setItem(row, 0, QTableWidgetItem(QString(object)))
        self.table.setItem(row, 1, QTableWidgetItem(QString(access)))
        self.table.setItem(row, 2, QTableWidgetItem(QString(subject)))
        self.table.setItem(row, 3, QTableWidgetItem(QString(str(id))))
        print str(id)
        
    def retrieve(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, u"失败", u"请选中一行")
            return
        msgBox = QMessageBox()
        msgBox.setWindowTitle(u"确认回收？")
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText(u"你确认要回收该授权吗？");
        msgBox.addButton(u"确定", QMessageBox.YesRole)
        msgBox.addButton(u"取消", QMessageBox.RejectRole)
        ret = msgBox.exec_();
        if ret != QMessageBox.AcceptRole:
            return
        
        au_id = int(self.table.item(row, 3).text())
        print self.table.item(row, 3)
        try:
            self.parent.con.execute(
                "delete from authorize where id=?",
                (au_id,)
            )
            self.parent.con.commit()
            self.table.removeRow(row)
        except:
            QMessageBox.information(self, u"失败", u"回收失败，数据库原因")
        else:
            QMessageBox.information(self, u"成功", u"回收成功！")
            
class ManageSubjectDialog(QDialog):
        
    def __init__(self, parent=None):
        super(ManageSubjectDialog, self).__init__(parent)
        
        self.setWindowTitle(u"管理主体")
        self.setFixedSize(440, 300)
        self.parent = parent
        
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(
            QStringList([u"id", u"名字"])
        )
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        h_header = self.table.horizontalHeader()
        h_header.setHighlightSections(False)
        h_header.setDefaultAlignment(Qt.AlignLeft)
        self.table.verticalHeader().hide()
        
        results = self.parent.con.execute(
            "select id,name from subject where not is_admin=='Y'"
        ).fetchall()
                
        for result in results:
            self.showItem(result[0], result[1])
        
        button_retri = QPushButton(u"删除")
        button_close = QPushButton(u"取消")
        hbox = QHBoxLayout()
        hbox.addWidget(button_retri)
        hbox.addWidget(button_close)
        hbox_widget = QWidget()
        hbox_widget.setLayout(hbox)        
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.table)
        vbox.addWidget(hbox_widget)
        
        self.setLayout(vbox)
        
        self.connect(button_retri, SIGNAL("clicked()"), self.delete)
        self.connect(button_close, SIGNAL("clicked()"), self.reject)
        
    def showItem(self, id, name):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(QString(str(id))))
        self.table.setItem(row, 1, QTableWidgetItem(QString(name)))
        
    def delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, u"失败", u"请选中一行")
            return
        msgBox = QMessageBox()
        msgBox.setWindowTitle(u"确认删除？")
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText(u"你确认要删除这个主体吗？");
        msgBox.addButton(u"确定", QMessageBox.YesRole)
        msgBox.addButton(u"取消", QMessageBox.RejectRole)
        ret = msgBox.exec_();
        if ret != QMessageBox.AcceptRole:
            return
        
        s_id = int(self.table.item(row, 0).text())
        try:
            self.parent.con.execute(
                "delete from subject where id=?",
                (s_id,)
            )
            self.parent.con.commit()
            self.table.removeRow(row)
        except:
            QMessageBox.information(self, u"失败", u"删除失败，数据库原因")
        else:
            QMessageBox.information(self, u"成功", u"删除成功！")
        
def main():
    app = QApplication(sys.argv)
    login_dlg = LoginDialog()
    id_admin = login_dlg.exec_()
    id = id_admin // 10
    is_admin = id_admin % 10
    #id = 2
    #is_admin = 0
    if id:
        win = MainWindow(id, is_admin)
        win.show()
    else:
        QTimer.singleShot(0, app.quit)
    app.exec_()

if __name__ == '__main__':
    main()