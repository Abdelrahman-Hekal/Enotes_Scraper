from selenium import webdriver
import undetected_chromedriver.v2 as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from pathlib import Path
import time
import os
import random
import shutil
import time
import unidecode
import sys
from copy import deepcopy
import numpy as np

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options  = webdriver.ChromeOptions()
    # suppressing output messages from the driver
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    # adding user agents
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # running the driver with no browser window
    chrome_options.add_argument('--headless')
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    # configuring the driver
    driver = webdriver.Chrome(driver_path, options=chrome_options)
    driver.set_page_load_timeout(60)
    driver.maximize_window()

    return driver

def scrape_enotes(path):

    start = time.time()
    print('-'*75)
    print('Scraping enotes.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()
    name = path.split('\\')[-1][:-4]
    try:
        df = pd.read_csv(name + '_output.csv')
    except:
        # read the urls csv input file
        df = pd.read_csv(path)
    cols = df.columns

    if 'Author' not in cols:
        df['Author'] = ''
    if 'Author Link' not in cols:
        df['Author Link'] = ''
    if 'Citation' not in cols:
        df['Citation'] = ''
    if 'Sections' not in cols:
        df['Sections'] = ''
    inds = df.index
    n = df.shape[0]
    for i, ind in enumerate(inds):
        try:
            # conditions for skipping scraped data
            if isinstance(df.loc[ind, 'Author Link'], str) and df.loc[ind, 'Author Link']!= '': continue            
            elif isinstance(df.loc[ind, 'Citation'], str) and df.loc[ind, 'Citation']!= '': continue            
            elif isinstance(df.loc[ind, 'Sections'], str) and df.loc[ind, 'Sections']!= '': continue
            
            # saving data to csv file each 100 links
            if np.mod(i+1, 100) == 0:
                print('Outputting scraped data to csv file ...')
                df.to_csv(name + '_output.csv', encoding='UTF-8', index=False)

            print(f'Scraping the info for book {i+1}\{n}')
            driver.get(df.loc[ind, 'URL'])
            # for debugging
            #driver.get("https://www.enotes.com/topics/william-saroyan#")
            time.sleep(2)

            # author and author link
            author, author_link = '', ''
            try:
                a = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.author-link")))
                author = a.get_attribute("textContent")
                author = unidecode.unidecode(author)
                author_link = a.get_attribute("href")
            except:
                pass    
                
            df.loc[ind, 'Author'] = author
            df.loc[ind, 'Author Link'] = author_link

            # getting the cite information
            cite = ''
            try:
                button = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Page Citation']")))
                driver.execute_script("arguments[0].click();", button)
                time.sleep(1)
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.u-flex.u-align-items--center.u-justify-content--space-between.u-padding--triple")))
                cite = wait(div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "p")))[0].get_attribute("textContent")
               
                button = wait(div, 2).until(EC.presence_of_element_located((By.XPATH, "//button[@aria-label='Close modal popup']")))
                driver.execute_script("arguments[0].click();", button)
                time.sleep(1)   
            except:
                pass
            df.loc[ind, 'Citation'] = cite.strip()

            #other info
            try:
                ul = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.c-secondary-nav__list.o-scroll-nav__links.l-container--lg")))
                lis = wait(ul, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
                nlis = len(lis)
                sections = {}
                title, prev_title = '', ''
                for j in range(nlis):
                    ul = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.c-secondary-nav__list.o-scroll-nav__links.l-container--lg")))
                    li = wait(ul, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))[j]
                    a = wait(li, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                    cat = a.get_attribute("textContent").replace('\n', '').replace('–', '-').strip()
                    driver.execute_script("arguments[0].click();", a)
                    time.sleep(1)

                # getting the details of each tab
                    count = ''
                    try:
                        text = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.u-color--gray--darker.u-no-spacing"))).get_attribute("textContent")
                        if 'Word Count:' in text:
                            count = text.split(' ')[-1]
                    except:
                        pass

                    try:
                        prev_title = title
                        title = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.c-article-header__title"))).get_attribute("textContent")
                        if title != prev_title:
                            sections[cat] = count
                        elif cat not in sections.keys():
                            sections[cat] = ""
                    except:
                        if cat not in sections.keys():
                            sections[cat] = ""

                df.loc[ind, 'Sections'] =  [deepcopy(sections)]
                    
            except Exception as err:
                df.loc[ind, 'Sections'] =  [deepcopy(sections)]   

        except Exception as err:
            print('The following rror occurred during the scraping from Enotes.com, retrying ..')
            print('-'*50)
            print(err)
            print('-'*50)
            driver.quit()
            time.sleep(5)
            driver = initialize_bot()

    # optional output to csv
    df.to_csv(name + '_output.csv', encoding='UTF-8', index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'enotes.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return df

if __name__ == "__main__":

    path = sys.argv[1]
    data = scrape_enotes(path)

