import requests
from PIL import Image
from bs4 import BeautifulSoup
import copy
import time
import re


class Spider:
    class Lesson:

        def __init__(self, name, code, teacher_name, Time, number):
            self.name = name
            self.code = code
            self.teacher_name = teacher_name
            self.time = Time
            self.number = number

        def show(self):
            print('  name:' + self.name + '  code:' + self.code + '  teacher_name:' + self.teacher_name + '  time:' + self.time)

    def __init__(self, url):
        self.__uid = ''
        self.__real_base_url = ''
        self.__base_url = url
        self.__name = ''
        self.__base_data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '',
            'ddl_kcxz': '',
            'ddl_ywyl': '',
            'ddl_kcgs': '',
            'ddl_xqbs': '',
            'ddl_sksj': '',
            'TextBox1': '',
            'dpkcmcGrid:txtChoosePage': '1',
            'dpkcmcGrid:txtPageSize': '200',
        }
        self.__headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36',
        }

    def __set_real_url(self):
        request = requests.get(self.__base_url, headers=self.__headers)
        real_url = request.url
        self.__real_base_url = real_url[:len(real_url) - len('default2.aspx')]
        return request

    def __get_code(self):
        request = requests.get(self.__real_base_url + 'CheckCode.aspx', headers=self.__headers)
        with open('code.jpg', 'wb')as f:
            f.write(request.content)
        im = Image.open('code.jpg')
        im.show()
        print('Please input the code:')
        code = input()
        return code

    def __get_login_data(self, uid, password):
        self.__uid = uid
        request = self.__set_real_url()
        soup = BeautifulSoup(request.text, 'lxml')
        form_tag = soup.find('input')
        __VIEWSTATE = form_tag['value']
        code = self.__get_code()
        data = {
            '__VIEWSTATE': __VIEWSTATE,
            'txtUserName': self.__uid,
            'TextBox2': password,
            'txtSecretCode': code,
            'RadioButtonList1': '学生'.encode('gb2312'),
            'Button1': '',
            'lbLanguage': '',
            'hidPdrs': '',
            'hidsc': '',
        }
        return data

    def login(self, uid, password):
        while True:
            data = self.__get_login_data(uid, password)
            request = requests.post(self.__real_base_url + 'default2.aspx', headers=self.__headers, data=data)
            soup = BeautifulSoup(request.text, 'lxml')
            if request.status_code != requests.codes.ok:
                print('4XX or 5XX Error,try to login again')
                time.sleep(0.5)
                continue
            if request.text.find('验证码不正确') > -1:
                print('Code error,please input again')
                continue
            if request.text.find('密码错误') > -1:
                print('Password may be error')
                return False
            if request.text.find('用户名不存在') > -1:
                print('Uid may be error')
                return False
            try:
                name_tag = soup.find(id='xhxm')
                self.__name = name_tag.string[:len(name_tag.string) - 2]
                print('欢迎' + self.__name)
                self.__enter_lessons_first()
            except:
                print('Unknown Error,try to login again.')
                time.sleep(0.5)
                continue
            finally:
                return True

    def __enter_lessons_first(self):
        data = {
            'xh': self.__uid,
            'xm': self.__name.encode('gb2312'),
            'gnmkdm': 'N121103',
        }
        self.__headers['Referer'] = self.__real_base_url + 'xs_main.aspx?xh=' + self.__uid
        request = requests.get(self.__real_base_url + 'xf_xsqxxxk.aspx', params=data, headers=self.__headers)
        self.__headers['Referer'] = request.url
        soup = BeautifulSoup(request.text, 'lxml')
        self.__set__VIEWSTATE(soup)
        try:
            xq_tag = soup.find('select', id='ddl_xqbs')
            self.__base_data['ddl_xqbs'] = xq_tag.find('option')['value']
        except:
            pass

    def __set__VIEWSTATE(self, soup):
        __VIEWSTATE_tag = soup.find('input', attrs={'name': '__VIEWSTATE'})
        self.__base_data['__VIEWSTATE'] = __VIEWSTATE_tag['value']

    def __get_lessons(self, soup):
        lesson_list = []
        lessons_tag = soup.find('table', id='kcmcGrid')
        lesson_tag_list = lessons_tag.find_all('tr')[1:]
        for lesson_tag in lesson_tag_list:
            td_list = lesson_tag.find_all('td')
            code = td_list[0].input['name']
            name = td_list[1].string
            teacher_name = td_list[3].string
            Time = td_list[4]['title']
            number = td_list[10].string
            lesson = self.Lesson(name, code, teacher_name, Time, number)
            lesson_list.append(lesson)
        return lesson_list

    def __search_lessons(self, lesson_name=''):
        self.__base_data['TextBox1'] = lesson_name.encode('gb2312')
        request = requests.post(self.__headers['Referer'], data=self.__base_data, headers=self.__headers)
        soup = BeautifulSoup(request.text, 'lxml')
        self.__set__VIEWSTATE(soup)
        return self.__get_lessons(soup)

    def __select_lesson(self, lesson_list):
        data = copy.deepcopy(self.__base_data)
        data['Button1'] = '  提交  '.encode('gb2312')
        for lesson in lesson_list:
            code = lesson.code
            data[code] = 'on'
        request = requests.post(self.__headers['Referer'], data=data, headers=self.__headers)
        soup = BeautifulSoup(request.text, 'lxml')
        self.__set__VIEWSTATE(soup)
        error_tag = soup.html.head.script
        if not error_tag is None:
            error_tag_text = error_tag.string
            r = "alert\('(.+?)'\);"
            for s in re.findall(r, error_tag_text):
                print(s)
        print('已选课程:')
        selected_lessons_pre_tag = soup.find('legend', text='已选课程')
        selected_lessons_tag = selected_lessons_pre_tag.next_sibling
        tr_list = selected_lessons_tag.find_all('tr')[1:]
        for tr in tr_list:
            td = tr.find('td')
            print(td.string)

    def run(self):
        print('请输入搜索课程名字')
        lesson_name = input()
        lesson_list = self.__search_lessons(lesson_name)
        print('请输入想选的课的id，id为每门课程开头的数字')
        for i in range(len(lesson_list)):
            print(i, end='')
            lesson_list[i].show()
        select_id = int(input())
        lesson_list = lesson_list[select_id:select_id + 1]
        self.__select_lesson(lesson_list)


if __name__ == '__main__':
    url = 'http://' #在这里输入你学校教务系统的IP地址
    print('请输入你们学校教务系统的IP地址，不用加上前面的http://')
    spider = Spider(url)
    print('请输入学号')
    uid = input()  #学号
    print('请输入密码')
    password = input() #密码
    if (spider.login(uid, password)):
        spider.run()
