import PyQt5
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sqlite3
import sys
import window
import os
import re


def try_except(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            import traceback
            traceback.print_exc()
    return wrapper


class Window(QMainWindow, window.Ui_MainWindow):
    html_path = r'index.html'

    def __init__(self):
        super(Window, self).__init__()
        self.setupUi(self)
        self.init_db()
        self.init()

    def init_db(self):
        """
        初始化数据库
        """
        self.db = sqlite3.connect('data.db', check_same_thread=False)
        self.cursor = self.db.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS category(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name varchar(20) NOT NULL,
                parent_id INTEGER DEFAULT 0
            );
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS website(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name varchar(20) NOT NULL,
                url varchar(100) NOT NULL,
                real_url varchar(100) NOT NULL,
                bio varchar(100) NOT NULL,
                logo varchar(100) NOT NULL,
                category_id INTEGER NOT NULL
            );
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS TJScript(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script TEXT NOT NULL
            );
        ''')
        self.db.commit()

    def show_msg(self, msg):
        QMessageBox.information(self, '提示', msg)

    def init(self):
        # 初始化UI组件
        # ...省略具体代码

        # 连接信号和槽函数
        self.pushButtonFetch.clicked.connect(self.fetchData)
        self.pushButtonAddCategory.clicked.connect(self.addCategory)
        self.pushButtonDelCategory.clicked.connect(self.delCategory)
        self.pushButtonAddWebsite.clicked.connect(self.addWebsite)
        self.pushButtonDelWebsite.clicked.connect(self.delWebsite)
        self.pushButtonGenerateHTML.clicked.connect(self.generateHTML)
        self.pushButtonSaveToDB.clicked.connect(self.saveToDB)
        self.fetchData(False)

    def fetchData(self, show_msg=True):
        """
        获取数据
        """
        self.cur_parent_category = self.comboBoxParentCategory.currentText()
        self.cur_category2 = self.comboBoxCategory2.currentText()
        categories = ['']
        # 获取分类数据
        self.cursor.execute("select * from category")
        result = self.cursor.fetchall()

        # 设置表格行数
        self.tableWidgetCategory.setRowCount(len(result))
        # 设置表格内容
        for i in range(len(result)):
            parent_id = result[i][2]
            if parent_id == -1:
                parent_name = ''
            else:
                self.cursor.execute(
                    "select * from category where id=?", (parent_id,))
                parent_name = self.cursor.fetchone()
                parent_name = parent_name[1] if parent_name else ''
            self.tableWidgetCategory.setItem(
                i, 0, QTableWidgetItem(result[i][1]))
            self.tableWidgetCategory.setItem(
                i, 1, QTableWidgetItem(parent_name))
            categories.append(result[i][1])

        self.comboBoxParentCategory.clear()
        self.comboBoxParentCategory.addItems(categories)
        self.comboBoxCategory2.clear()
        self.comboBoxCategory2.addItems(categories)
        self.comboBoxParentCategory.setCurrentText(self.cur_parent_category)
        self.comboBoxCategory2.setCurrentText(self.cur_category2)

        # 获取网站数据
        self.cursor.execute("select * from website")
        result = self.cursor.fetchall()
        # 设置表格行数
        self.tableWidgetWebsite.setRowCount(len(result))
        # 设置表格内容
        for i in range(len(result)):
            category_id = result[i][6]
            self.cursor.execute(
                "select * from category where id=?", (category_id,))
            category_name = self.cursor.fetchone()[1]
            # 分类、网站名称、网站简介、真实跳转、网址、logo
            self.tableWidgetWebsite.setItem(
                i, 0, QTableWidgetItem(category_name))
            self.tableWidgetWebsite.setItem(
                i, 1, QTableWidgetItem(result[i][1]))
            self.tableWidgetWebsite.setItem(
                i, 2, QTableWidgetItem(result[i][4]))
            self.tableWidgetWebsite.setItem(
                i, 3, QTableWidgetItem(result[i][3]))
            self.tableWidgetWebsite.setItem(
                i, 4, QTableWidgetItem(result[i][2]))
            self.tableWidgetWebsite.setItem(
                i, 5, QTableWidgetItem(result[i][5]))
        # 获取统计代码
        self.cursor.execute("select * from TJScript")
        result = self.cursor.fetchone()
        if result:
            self.plainTextEditTJScript.setPlainText(result[1])
        if show_msg:
            self.show_msg('获取数据成功')

    def saveToDB(self):
        """
        保存表格里面的数据到数据库
        """
        # 保存分类
        # 获取表格行数
        rowCount = self.tableWidgetCategory.rowCount()
        for i in range(rowCount):
            # 获取表格内容
            categoryName = self.tableWidgetCategory.item(i, 0).text()
            parentCategoryName = self.tableWidgetCategory.item(
                i, 1).text()
            parentCategory_id = -1
            if parentCategoryName != "":
                # 判断父级分类是否存在
                self.cursor.execute(
                    "select * from category where name=?", (parentCategoryName,))
                result = self.cursor.fetchone()
                if result:
                    parentCategory_id = result[0]
                else:
                    self.show_msg('父级分类不存在')
                    return
            # 判断是否已经存在该分类
            self.cursor.execute(
                "select * from category where name=?", (categoryName,))
            result = self.cursor.fetchone()
            if result:
                self.cursor.execute(
                    "update category set parent_id=? where name=?", (parentCategory_id, categoryName))
            else:
                self.cursor.execute(
                    "insert into category(name,parent_id) values(?,(select id from category where name=?))", (categoryName, parentCategory_id))
        # 保存网站
        # 获取表格行数
        rowCount = self.tableWidgetWebsite.rowCount()
        for i in range(rowCount):
            # 获取表格内容
            categoryName = self.tableWidgetWebsite.item(i, 0).text()
            websiteName = self.tableWidgetWebsite.item(i, 1).text()
            websiteBio = self.tableWidgetWebsite.item(i, 2).text()
            websiteRealUrl = self.tableWidgetWebsite.item(i, 3).text()
            websiteUrl = self.tableWidgetWebsite.item(i, 4).text()
            websiteLogo = self.tableWidgetWebsite.item(i, 5).text()
            # 判断是否已经存在该网站
            self.cursor.execute(
                "select * from website where name=?", (websiteName,))
            result = self.cursor.fetchone()
            if result:
                self.cursor.execute(
                    "update website set url=?,real_url=?,bio=?,logo=?,category_id=(select id from category where name=?) where name=?", (websiteUrl, websiteRealUrl, websiteBio, websiteLogo, categoryName, websiteName))
            else:
                self.cursor.execute(
                    "insert into website(name,url,real_url,bio,logo,category_id) values(?,?,?,?,?,(select id from category where name=?))", (websiteName, websiteUrl, websiteRealUrl, websiteBio, websiteLogo, categoryName))
        # 保存统计代码
        TJScript = self.plainTextEditTJScript.toPlainText()
        self.cursor.execute("select * from TJScript")
        result = self.cursor.fetchone()
        if result:
            self.cursor.execute(
                "update TJScript set script=?", (TJScript,))
        else:
            self.cursor.execute(
                "insert into TJScript(script) values(?)", (TJScript,))
        self.db.commit()
        self.show_msg('保存数据成功')

    def addCategory(self):
        # 增加分类
        lineEditNewCategory = self.lineEditNewCategory.text()
        comboBoxParentCategory = self.comboBoxParentCategory.currentText()
        if lineEditNewCategory == "":
            self.show_msg('分类名称不能为空')
            return
        # 判断是否已经存在该分类
        self.cursor.execute(
            "select * from category where name=?", (lineEditNewCategory,))
        result = self.cursor.fetchone()
        if result:
            self.show_msg('该分类已经存在')
            return
        # 判断是否有父级分类
        if comboBoxParentCategory == "":
            parent_id = -1
        else:
            self.cursor.execute(
                "select * from category where name=?", (comboBoxParentCategory,))
            result = self.cursor.fetchone()
            if result:
                parent_id = result[0]
            else:
                self.show_msg('父级分类不存在')
                return
        # 插入数据
        self.cursor.execute(
            "insert into category(name,parent_id) values(?,?)", (lineEditNewCategory, parent_id))
        self.db.commit()
        self.lineEditNewCategory.setText("")
        self.fetchData(False)
        self.show_msg('添加分类成功')

    def delCategory(self):
        # 删除分类
        # 当前行 tableWidgetCategory
        currentRow = self.tableWidgetCategory.currentRow()
        if currentRow == -1:
            self.show_msg('请选择要删除的分类')
            return
        # 获取当前行的分类名称
        categoryName = self.tableWidgetCategory.item(currentRow, 0).text()
        parentCategoryName = self.tableWidgetCategory.item(
            currentRow, 1).text()
        # 判断是否有子分类
        self.cursor.execute(
            "select * from category where parent_id=(select id from category where name=?)", (categoryName,))
        result = self.cursor.fetchone()
        if result:
            self.show_msg('该分类下有子分类，不能删除')
            return
        # 判断是否有网站
        self.cursor.execute(
            "select * from website where category_id=(select id from category where name=?)", (categoryName,))
        result = self.cursor.fetchone()
        if result:
            self.show_msg('该分类下有网站，不能删除')
            return
        # 删除数据
        self.cursor.execute(
            "delete from category where name=?", (categoryName,))
        self.db.commit()
        self.fetchData(False)
        self.show_msg('删除分类成功')

    def addWebsite(self):
        # 增加网站
        comboBoxCategory2 = self.comboBoxCategory2.currentText()
        lineEditNewName = self.lineEditNewName.text()
        lineEditNewBio = self.lineEditNewBio.text()
        lineEditNewUrl = self.lineEditNewUrl.text()
        lineEditNewRealUrl = self.lineEditNewRealUrl.text()
        lineEditNewLogo = self.lineEditNewLogo.text()

        # 判断是否已经存在该网站
        self.cursor.execute(
            "select * from website where name=?", (lineEditNewName,))
        result = self.cursor.fetchone()
        if result:
            self.show_msg('该网站已经存在')
            return
        # 判断是否有分类
        if comboBoxCategory2 == "":
            self.show_msg('请选择分类')
            return
        else:
            self.cursor.execute(
                "select * from category where name=?", (comboBoxCategory2,))
            result = self.cursor.fetchone()
            if result:
                category_id = result[0]
            else:
                self.show_msg('分类不存在')
                return
        # 插入数据
        self.cursor.execute(
            "insert into website(name,url,real_url,bio,logo,category_id) values(?,?,?,?,?,?)", (lineEditNewName, lineEditNewUrl, lineEditNewRealUrl, lineEditNewBio, lineEditNewLogo, category_id))
        self.db.commit()
        self.fetchData(False)
        self.show_msg('添加网站成功')

    def delWebsite(self):
        # 删除网站
        # 当前行 tableWidgetWebsite
        currentRow = self.tableWidgetWebsite.currentRow()
        if currentRow == -1:
            self.show_msg('请选择要删除的网站')
            return
        # 获取当前行的网站名称
        websiteName = self.tableWidgetWebsite.item(currentRow, 1).text()
        # 删除数据
        self.cursor.execute(
            "delete from website where name=?", (websiteName,))
        self.db.commit()
        self.fetchData(False)
        self.show_msg('删除网站成功')

    def generateHTML(self):
        # 生成HTML
        # 获取分类数据
        self.cursor.execute("select * from category")
        all_categories = self.cursor.fetchall()
        all_categories_dict = {}
        for category in all_categories:
            all_categories_dict[category[1]] = category[0]
        # 获取一级分类
        self.cursor.execute("select * from category where parent_id=-1")
        categories1 = self.cursor.fetchall()
        # 获取二级分类
        categories = {}
        for category1 in categories1:
            self.cursor.execute(
                "select * from category where parent_id=?", (category1[0],))
            categories[category1[1]] = self.cursor.fetchall()
        #
        tempcateid = {}
        for c in categories:
            tempcateid[all_categories_dict[c]] = c
            if categories[c]:
                for c2 in categories[c]:
                    tempcateid[all_categories_dict[c2[1]]] = c2[1]
        # 获取网站数据
        self.cursor.execute("select * from website")
        all_websites = self.cursor.fetchall()
        cate_websites = {}
        for category in tempcateid:
            cate_websites[tempcateid[category]] = []

        # for website in all_websites:
        #     if tempcateid.get(website[6], None) == None:
        #         cateid = website[6]
        #         self.cursor.execute(
        #             "select * from category where id=?", (cateid,))
        #         tempcateid[cateid] = self.cursor.fetchone()[1]
        #         catename = tempcateid[cateid]
        #     else:
        #         catename = tempcateid[website[6]]
        #     cate_websites[catename].append(website)
        for c in tempcateid:
            for website in all_websites:
                if website[6] == c:
                    cate_websites[tempcateid[c]].append(website)

        # 统计代码
        self.cursor.execute("select * from TJScript")
        TJScript = self.cursor.fetchone()
        TJScript = TJScript[1] if TJScript else None
        if not TJScript:
            TJScript = self.plainTextEditTJScript.toPlainText()
            if TJScript:
                self.cursor.execute(
                    "insert into TJScript(script) values(?)", (TJScript,))
                self.db.commit()
        # 生成HTML
        # 分类
        cate_html = ''
        for cate in categories:
            if len(categories[cate]) == 0:
                cate_html += f'''
                <li>
                    <a href="#{cate}" class="smooth">
                        <i class="linecons-star"></i>
                        <span class="title">{cate}</span>
                    </a>
                </li>
                '''
            else:
                cate_html += f'''
                <li>
                    <a>
                        <i class="linecons-lightbulb"></i>
                        <span class="title">{cate}</span>
                    </a>
                    <ul>
                '''
                for cate2 in categories[cate]:
                    cate_html += f'''
                        <li>
                            <a href="#{cate2[1]}" class="smooth">
                                <span class="title">{cate2[1]}</span>
                            </a>
                        </li>
                    '''
                cate_html += '''
                    </ul>
                </li>
                '''
        # 网站
        ###
        website_html = ''
        for c_w in cate_websites:
            if not cate_websites[c_w]:
                continue
            temp_html = f'''<!-- {c_w} -->
            <h4 class="text-gray"><i class="linecons-tag" style="margin-right: 7px;" id="{c_w}"></i>{c_w}</h4>
            '''
            # 每4个网站一个  <div class="row">
            idx = 0
            for website in cate_websites[c_w]:
                if idx == 0:
                    temp_html += '<div class="row">'
                idx += 1
                temp_html += f'''<div class="col-sm-3">
                <div class="xe-widget xe-conversations box2 label-info"
                    onclick="window.open('{website[3]}', '_blank')" data-toggle="tooltip"
                    data-placement="bottom" title="" data-original-title="{website[2]}">
                <div class="xe-comment-entry">
                        <a class="xe-user-img">
                            <img data-src="{website[5]}" class="lozad img-circle"
                                width="40">
                        </a>
                        <div class="xe-comment">
                            <a href="#" class="xe-user-name overflowClip_1">
                                <strong>{website[1]}</strong>
                            </a>
                            <p class="overflowClip_2">{website[4]}</p>
                        </div>
                    </div>
                </div>
            </div>
            '''
                if idx == 4:
                    temp_html += '</div><br />'
                    idx = 0
            if idx != 0:
                temp_html += '</div><br />'
            website_html += temp_html
        # 生成HTML
        with open('./temp_html.html', 'r', encoding='utf-8') as f:
            html = f.read()
        html = html.replace('{{menu_list}}', cate_html)
        html = html.replace('{{website_content}}', website_html)
        html = html.replace('{{tj_script}}', TJScript)
        with open(self.html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        ##
        # 推送github
        os.system('git add .')
        os.system('git commit -m "update"')
        os.system('git push origin main')

        self.show_msg('生成HTML成功')
        ###


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
