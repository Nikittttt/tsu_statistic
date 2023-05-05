import contextlib
from time import sleep, time
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType


from login_param import user_name, password
from param_to_parse import courses_name, semesters

implicitly_wait = 10


@contextlib.contextmanager
def init_browser():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    browser = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(),
                               chrome_options=chrome_options)
    browser.implicitly_wait(implicitly_wait)
    browser.get("http://edu.tltsu.ru/")
    yield browser
    browser.quit()


def login(browser):
    login_button = browser.find_element_by_xpath('//a[@href="javascript: face.lookBtnClick()"]')
    login_button.click()

    input_login = browser.find_element_by_xpath('//input[@name="core_log"]')
    input_login.send_keys(user_name)

    input_password = browser.find_element_by_xpath('//input[@name="core_pas"]')
    input_password.send_keys(password)

    log_in = browser.find_element_by_xpath('//input[@value="Войти"]')
    log_in.click()


def main():
    with init_browser() as browser:
        login(browser)
        WebDriverWait(browser, implicitly_wait).until((
            EC.presence_of_element_located((By.XPATH, '//td[@class="status_box" and text() != "Гость"]')))
        )
        list_score = []
        browser.get(f"http://edu.tltsu.ru/edu/assignments.php")
        for semester in semesters:
            body = browser.find_element_by_xpath('//tbody')
            semester_choice = Select(body.find_element_by_xpath('.//select[@name="semestr"]'))
            semester_choice.select_by_visible_text(semester)
            course_error = 0
            course_ind = 0
            while True:
                course_name = courses_name[course_ind]
                try:
                    print(f"<{semester}> <{course_name}>")

                    WebDriverWait(browser, implicitly_wait).until((
                        EC.presence_of_element_located((By.XPATH, '//img[@alt="Выбор курса"]')))
                    )
                    find = browser.find_element_by_xpath('//img[@alt="Выбор курса"]')
                    find.click()

                    WebDriverWait(browser, implicitly_wait).until((
                        EC.presence_of_element_located((By.XPATH, '//input[@id="course_sel_1"]')))
                    )
                    sleep(1)
                    input_name_course = browser.find_element_by_xpath('//input[@id="course_sel_1"]')
                    input_name_course.clear()
                    input_name_course.send_keys(course_name)

                    find = browser.find_element_by_xpath('//input[@type="submit"]')
                    find.click()
                    sleep(2)  # на странице ничего значимого не меняется и у меня нет особо идей как это сделать нормально
                    try:
                        go_to_course = browser.find_element_by_xpath('//input[@type="checkbox"]')
                        go_to_course.click()
                    except NoSuchElementException:
                        go_back = browser.find_elements_by_xpath('//img[@src="/core/images/img_popup/close.png"]')[-1]
                        go_back.click()
                        raise
                    body = browser.find_element_by_xpath('//tbody')

                    list_score.append({'semester': semester, 'course_name': course_name, 'groups': []})

                    WebDriverWait(browser, implicitly_wait).until((
                        EC.presence_of_element_located((By.XPATH, '//span[@class="T_icoClosePunktImg"]')))
                    )

                    list_to_open = body.find_elements_by_xpath('.//span[@class="T_icoClosePunktImg"]')
                    for i in list_to_open[::-1]:
                        i.click()

                    WebDriverWait(browser, implicitly_wait).until((
                        EC.invisibility_of_element((By.XPATH, '//span[@class="T_icoClosePunktImg"]')))
                    )

                    table = body.find_element_by_xpath('.//div[@id="div_results"]').find_element_by_xpath('.//tbody')
                    rows = table.find_elements_by_xpath('.//tr[@id]')
                    for row in rows:
                        if row.get_attribute("id")[0] == 'G':
                            name_group = row.find_elements_by_xpath('.//td')[1].text
                            print(f"\t\t<{name_group}>")
                            list_score[-1]['groups'].append({'name': name_group, 'final': [], 'score': []})
                        else:
                            scores = row.find_elements_by_xpath('.//td[@id]')
                            try:
                                final = row.find_elements_by_xpath('.//td[@class=" core_table_22"]')[0].text
                            except IndexError:
                                final = row.find_elements_by_xpath('.//td[@class=" core_table_22 core_table_2bottom"]')[0].text
                            list_score[-1]['groups'][-1]['final'].append(final)
                            score_l = []
                            for score in scores:
                                score_to_add = score.text
                                if score_to_add in ['?', '']:
                                    score_to_add = None
                                score_l.append(score_to_add)
                            list_score[-1]['groups'][-1]['score'].append(score_l)
                except Exception as e:
                    course_error += 1
                    if course_error == 3:
                        course_error = 0
                        course_ind += 1
                else:
                    course_error = 0
                    course_ind += 1
                if course_ind == len(courses_name):
                    break
    name_file = f"./result/{int(time())}.json"
    with open(name_file, 'w', encoding='utf-8') as outfile:
        json.dump(list_score, outfile, ensure_ascii=False, indent=4)


main()
