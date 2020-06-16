from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time 
import csv
import os

browser = None
email = None
password = None
chrome_driver = None
link = None
base_link = None
col = None
current_tab = None
PAUSE_TIME = 0.5
link_list = set()
profile_dict = {}

def check_element(element):
    global browser
    try:
        browser.find_element_by_xpath(element)
    except NoSuchElementException:
        return False
    return True

def check_element_by_class(element):
    global browser
    try:
        browser.find_element_by_class_name(element)
    except NoSuchElementException:
        return False
    return True

def initialise(post_link):
    global browser, email, password, chrome_driver, link, base_link, col
    file = open('flasksite/LinkedIn.txt', 'r') 
    lines = file.readlines()
    email = lines[0].split()[1].strip()
    password = lines[1].split()[1].strip()
    chrome_driver = r"P:\CMU\Nelson_Project\chromedriver.exe"  
    link = post_link
    base_link = 'https://www.linkedin.com'  
    browser = webdriver.Chrome(chrome_driver)

def fetch_site():
    global browser, email, password, link, base_link
    browser.get(base_link)

    browser.find_element_by_xpath('/html/body/nav/a[3]').click()

    WebDriverWait(browser, 100).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="username"]')))
    username_field = browser.find_element_by_xpath('//*[@id="username"]')
    time.sleep(PAUSE_TIME)
    username_field.send_keys(email)

    WebDriverWait(browser, 100).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="password"]')))
    password_field = browser.find_element_by_xpath('//*[@id="password"]')
    password_field.send_keys(password)

    sign_in_button = browser.find_element_by_xpath("//button[contains(@aria-label,'Sign in')]")
    sign_in_button.click()
    
    browser.get(link)

def get_profile(link):
    global browser, current_tab
    current_tab = browser.current_window_handle
    script = 'window.open("{}");'.format(link)
    browser.execute_script(script)
    new_tab = [tab for tab in browser.window_handles if tab != current_tab][0]
    browser.switch_to.window(new_tab)
    time.sleep(3)
    name, location, headline = get_basic_details()
    company, role, year = get_experience()
    university, course, year = get_education()
    title, subtitle_and_year, description = get_publications()

    profile_data = [headline, location, company, role, link, university, course, year, title, subtitle_and_year, description]
    return name, profile_data

def get_basic_details():
    global browser
    name = browser.find_element_by_xpath("//li[contains(@class,'inline t-24 t-black t-normal break-words')]").text
    location = browser.find_element_by_xpath("//li[contains(@class,'t-16 t-black t-normal inline-block')]").text
    headline = browser.find_element_by_xpath("//h2[contains(@class, 'mt1 t-18 t-black t-normal break-words')]").text
    return name, location, headline

def get_experience():
    global browser
    company, role, year = [], [], []
    experience_element = '//*[@id="experience-section"]/ul'
    last_height = browser.execute_script("return document.body.scrollHeight")

    while not check_element(experience_element):
        html = browser.find_element_by_tag_name('html')
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(PAUSE_TIME)
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            flag = 1
            break
        last_height = new_height

    if check_element(experience_element):
        experience_elements = browser.find_element_by_xpath(experience_element)
        experience_elements = experience_elements.find_elements_by_tag_name('li')
        for element in experience_elements:
            role.append(element.find_element_by_tag_name('h3').text)
            try:
                company_name_init = element.find_element_by_xpath(".//p[contains(@class,'pv-entity__secondary-title t-14 t-black t-normal')]")
                try:
                    type_of_job = company_name_init.find_element_by_xpath(".//*").text
                except NoSuchElementException:
                    type_of_job = ''
                company_name = company_name_init.text.replace(type_of_job, '')
                company.append(company_name)

            except NoSuchElementException:
                pass

    return company, role, year


def get_education():
    global browser
    university, course, year = [], [], []
    last_height = browser.execute_script("return document.body.scrollHeight")
    education_element = '//*[@id="education-section"]/ul'

    while not check_element(education_element):
        html = browser.find_element_by_tag_name('html')
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(PAUSE_TIME)
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            flag = 1
            break
        last_height = new_height

    if check_element(education_element):
        education_elements = browser.find_element_by_xpath(education_element)
        education_elements = education_elements.find_elements_by_tag_name('li')
        for element in education_elements:
            university.append(element.find_element_by_tag_name('h3').text)

            course_name = "N/A"
            try:
                course_name = element.find_element_by_xpath(".//p[contains(@class,'pv-entity__secondary-title pv-entity__degree-name t-14 t-black t-normal')]").text.split('\n')[1]
            except NoSuchElementException:
                pass
            try:
               course_name = element.find_element_by_xpath(".//p[contains(@class,'pv-entity__secondary-title pv-entity__fos t-14 t-black t-normal')]").text.split('\n')[1]
            except NoSuchElementException:
                pass
            course.append(course_name)

            year_name = "N/A"
            try:
               year_name = (element.find_element_by_xpath(".//p[contains(@class,'pv-entity__dates t-14 t-black--light t-normal')]").text.split('\n')[1])
            except NoSuchElementException:
                pass
            year.append(year_name)

    return university, course, year

def get_publications():
    global browser
    title, subtitle_and_year, description = [], [], []
    publication_element = 'publications__list'
    last_height = browser.execute_script("return document.body.scrollHeight")

    while not check_element_by_class(publication_element):
        html = browser.find_element_by_tag_name('html')
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(PAUSE_TIME)
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            flag = 1
            break
        last_height = new_height

    if check_element_by_class(publication_element):
        publication_elements = browser.find_element_by_class_name(publication_element)
        publication_elements = publication_elements.find_elements_by_tag_name('li')
        for element in publication_elements:
            try:
                title.append(element.find_element_by_tag_name('h3').text)
            except NoSuchElementException:
                pass
            try:
                subtitle_and_year.append(element.find_element_by_tag_name('h4').text)
            except NoSuchElementException:
                pass
            try:    
                description.append(element.find_element_by_tag_name('div').text)
            except NoSuchElementException:
                pass
    
    return title, subtitle_and_year, description

    
def insert_data():
    global browser, col, current_tab
    profile_dict = {}
    while check_element("//button[contains(@data-control-name,'more_comments')]"):
        if check_element("//button[contains(@data-control-name,'more_comments')]"):
            browser.find_element_by_xpath("//button[contains(@data-control-name,'more_comments')]").click()
            time.sleep(2)
    comments = browser.find_elements_by_xpath("//a[contains(@class,'comments-post-meta__profile-link t-16 t-black t-bold tap-target ember-view')]")
    for comment in comments:
        link = comment.get_attribute('href')
        if not (link in link_list):
            link_list.add(link)
            name, profile_data = get_profile(link)
            profile_dict[name] = profile_data
            browser.close()
            browser.switch_to_window(current_tab)

    browser.close()
    return profile_dict
