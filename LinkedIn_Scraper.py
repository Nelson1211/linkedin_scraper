from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time 
import csv
import pymongo

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

def check_element(element):
    global browser
    try:
        browser.find_element_by_xpath(element)
    except NoSuchElementException:
        return False
    return True

def initialise():
    global browser, email, password, chrome_driver, link, base_link, col
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["LinkedIn_Data"]
    col = db["public_profiles"]
    '''for entry in col.find():
        print(entry)'''
    col.drop()
    col = db["public_profiles"]
    file = open('LinkedIn.txt', 'r') 
    lines = file.readlines()
    email = lines[0].split()[1].strip()
    password = lines[1].split()[1].strip()
    chrome_driver = lines[2].split()[1].strip()
    link = lines[3].split()[1].strip()
    base_link = 'https://www.linkedin.com'

    if link[0:24] != base_link:
        exit(0)

    browser = webdriver.Chrome(chrome_driver)

def fetch_site():
    global browser, email, password, link, base_link
    browser.get(base_link)

    username_field = browser.find_element_by_xpath('/html/body/nav/section[2]/form/div[1]/div[1]/input')
    time.sleep(PAUSE_TIME)

    username_field.send_keys(email)

    time.sleep(PAUSE_TIME)

    password_field = browser.find_element_by_xpath('/html/body/nav/section[2]/form/div[1]/div[2]/input')
    time.sleep(PAUSE_TIME)

    password_field.send_keys(password)
    time.sleep(PAUSE_TIME)

    sign_in_button = browser.find_element_by_xpath('/html/body/nav/section[2]/form/div[2]/button')

    sign_in_button.click()
    time.sleep(PAUSE_TIME)

    browser.get(link)
    time.sleep(PAUSE_TIME)

def get_profile(link):
    global browser, current_tab
    current_tab = browser.current_window_handle
    script = 'window.open("{}");'.format(link)
    browser.execute_script(script)
    new_tab = [tab for tab in browser.window_handles if tab != current_tab][0]
    browser.switch_to.window(new_tab)
    time.sleep(3)
    name, location = get_basic_details()
    company = get_experience()
    university = get_education()
    profile_dict = {}
    profile_dict['Name'] = name
    profile_dict['Location'] = location
    profile_dict['Profile Link'] = link
    profile_dict['Company'] = company
    profile_dict['University'] = university
    return profile_dict

def get_basic_details():
    global browser
    name = browser.find_element_by_xpath("//li[contains(@class,'inline t-24 t-black t-normal break-words')]").text
    location = browser.find_element_by_xpath("//li[contains(@class,'t-16 t-black t-normal inline-block')]").text
    return name, location

def get_experience():
    global browser
    experience_element = '//*[@id="experience-section"]/ul'
    last_height = browser.execute_script("return document.body.scrollHeight")
    flag = 0
    company = {}
    while not check_element(experience_element):
        html = browser.find_element_by_tag_name('html')
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(PAUSE_TIME)
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            flag = 1
            break
        last_height = new_height
    while check_element("//button[contains(@class,'pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle link link-without-hover-state')]"):
        time.sleep(PAUSE_TIME)
        browser.find_element_by_xpath("//button[contains(@class,'pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle link link-without-hover-state')]").click()
        html = browser.find_element_by_tag_name('html')
        html.send_keys(Keys.PAGE_DOWN)
        time.sleep(PAUSE_TIME)
    if flag == 0:
        experience_elements = browser.find_element_by_xpath(experience_element)
        experience_elements = experience_elements.find_elements_by_tag_name('li')
        experiences = []
        flag = 0
        for experience in experience_elements:
            for i in range(4):
                experience = experience.find_elements_by_xpath(".//*")[0]
                if i == 3 and experience.get_attribute('class') == 'pv-entity__company-details':
                    flag = 1
                    break
            if flag == 1:
                break
            company[experience.find_elements_by_xpath(".//*")[5].text.replace('.','')] = experience.find_elements_by_xpath(".//*")[3].text
        if flag == 1:
            while check_element("//button[contains(@class,'pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle link link-without-hover-state')]"):
                browser.find_element_by_xpath("//button[contains(@class,'pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle link link-without-hover-state')]").click()
                time.sleep(2)
            company_name = browser.find_element_by_xpath("//div[contains(@class,'pv-entity__company-summary-info')]")
            company_name = company_name.find_elements_by_xpath(".//*")[2].text.replace('.','')
            experience_elements = browser.find_element_by_xpath("//ul[contains(@class,'pv-entity__position-group mt2')]")
            experience_elements = experience_elements.find_elements_by_tag_name('li')
            for experience in experience_elements:
                experiences.append(experience.find_elements_by_xpath(".//*")[9].text)
            company[company_name] = experiences
    return company

def get_education():
    global browser
    education_element = '//*[@id="education-section"]/ul'
    university = 'N/A'
    if check_element(education_element):
        education_elements = browser.find_element_by_xpath(education_element)
        education_elements = education_elements.find_elements_by_tag_name('li')[0]
        university = education_elements.find_elements_by_xpath(".//*")[7].text
    return university

def insert_data():
    global browser, col, current_tab
    while check_element("//button[contains(@class,'button comments-comments-list__show-previous-button t-12 t-black t-normal hoverable-link-text')]"):
        comments = browser.find_elements_by_xpath("//a[contains(@class,'comments-post-meta__profile-link t-16 t-black t-bold tap-target ember-view')]")
        for comment in comments:
            link = comment.get_attribute('href')
            if not (link in link_list):
                link_list.add(link)
                x = col.insert_one(get_profile(link))
                browser.close()
                browser.switch_to_window(current_tab)

        browser.find_element_by_xpath("//button[contains(@class,'button comments-comments-list__show-previous-button t-12 t-black t-normal hoverable-link-text')]").click()
        time.sleep(2)

def fetch_information():
    print("Search by\n1. University\n2.Company")
    option = int(input())
    if option == 1:
        university_name = input("Enter the University you want profiles from: ")
        find_uni = col.find({'University': {'$eq': university_name}})
        for entries in find_uni:
            print(entries)
    elif option == 2:
        company_name = input("Enter the Company you want profiles from: ")
        find_company = col.find({'Company.{}'.format(company_name): {'$exists': True}})
        for entries in find_company:
            print(entries)
    else:
        exit(0)

def main():
    initialise()
    fetch_site()
    insert_data()
    fetch_information()

if __name__ == "__main__": 
    main()
