from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import time 
import csv
import pymongo

def check_more_comments():
    try:
        browser.find_element_by_xpath("//button[contains(@class,'button comments-comments-list__show-previous-button t-12 t-black t-normal hoverable-link-text')]")
    except NoSuchElementException:
        return False
    return True

def check_element(element):
    try:
        browser.find_element_by_xpath(element)
    except NoSuchElementException:
        return False
    return True

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["LinkedIn_Data"]
col = db["public_profiles"]
col.drop()
col = db["public_profiles"]

email = ''
password = ''
chrome_driver = ''
link = ''
file = open('LinkedIn.txt', 'r') 
lines = file.readlines()
email = lines[0].split()[1].strip()
password = lines[1].split()[1].strip()
chrome_driver = lines[2].split()[1].strip()
link = lines[3].split()[1].strip()

browser = webdriver.Chrome(chrome_driver)

browser.get('https://www.linkedin.com')

username_field = browser.find_element_by_xpath('/html/body/nav/section[2]/form/div[1]/div[1]/input')
time.sleep(1)

username_field.send_keys(email)

time.sleep(1)

password_field = browser.find_element_by_xpath('/html/body/nav/section[2]/form/div[1]/div[2]/input')
time.sleep(1)

password_field.send_keys(password)
time.sleep(1)

# locate submit button by_xpath
sign_in_button = browser.find_element_by_xpath('/html/body/nav/section[2]/form/div[2]/button')

# .click() to mimic button click
sign_in_button.click()
time.sleep(1)

browser.get(link)
time.sleep(1)

link_list = set()

while check_more_comments():
    comments = browser.find_elements_by_xpath("//a[contains(@class,'comments-post-meta__profile-link t-16 t-black t-bold tap-target ember-view')]")
    for comment in comments:
        link = comment.get_attribute('href')
        if not (link in link_list):
            link_list.add(link)
            current_tab = browser.current_window_handle
            script = 'window.open("{}");'.format(link)
            browser.execute_script(script)
            new_tab = [tab for tab in browser.window_handles if tab != current_tab][0]
            browser.switch_to.window(new_tab)
            time.sleep(3)
            name = browser.find_element_by_xpath("//li[contains(@class,'inline t-24 t-black t-normal break-words')]").text
            location = browser.find_element_by_xpath("//li[contains(@class,'t-16 t-black t-normal inline-block')]").text
            experience = browser.find_elements_by_xpath("//span[contains(@class,'text-align-left ml2 t-14 t-black t-bold full-width lt-line-clamp lt-line-clamp--multi-line ember-view')]")
            if len(experience) == 1:
                if(experience[0].text.find('University') >= 0 or experience[0].text.find('Institute') >= 0):
                    university = experience[0].text
                    company = 'N/A'
                else:
                    university = 'N/A'
                    company = experience[0].text
            else:
                company = experience[0].text
                university = experience[1].text
            if company == university:
                company = 'N/A'
            experience_element = '//*[@id="experience-section"]/ul'
            SCROLL_PAUSE_TIME = 0.5
            last_height = browser.execute_script("return document.body.scrollHeight")
            flag = 0
            while not check_element(experience_element):
                html = browser.find_element_by_tag_name('html')
                html.send_keys(Keys.PAGE_DOWN)
                time.sleep(SCROLL_PAUSE_TIME)
                new_height = browser.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    flag = 1
                    break
                last_height = new_height
            if flag == 0:
                experience_elements = browser.find_element_by_xpath('//*[@id="experience-section"]/ul')
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
                    experience = experience.find_elements_by_xpath(".//*")[3]
                    experiences.append(experience.text)
                if flag == 1:
                    experience_elements = browser.find_element_by_xpath("//ul[contains(@class,'pv-entity__position-group mt2')]")
                    experience_elements = experience_elements.find_elements_by_tag_name('li')
                    for experience in experience_elements:
                        experiences.append(experience.find_elements_by_xpath(".//*")[9].text)
                profile_dict = {}
                profile_dict['Name'] = name
                profile_dict['Location'] = location
                profile_dict['Profile Link'] = link
                profile_dict['Company'] = company
                profile_dict['University'] = university
                profile_dict['Experiences'] = experiences
                x = col.insert_one(profile_dict)
            browser.close()
            browser.switch_to_window(current_tab)

    browser.find_element_by_xpath("//button[contains(@class,'button comments-comments-list__show-previous-button t-12 t-black t-normal hoverable-link-text')]").click()
    time.sleep(2)