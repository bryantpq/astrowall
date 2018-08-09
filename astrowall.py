'''
TODO:
Add compatibility for Windows
Figure out how to show x number of reddit posts
Solve html parser compatibility for BeautifulSoup

NOTES:
- Selenium is only necessary for scraping the new reddit, since it is heavily-javascript driven,
    requests library is sufficient if scraping from the old reddit instead
- Selenium is used to scrape and BeautifulSoup used to parse
- Headless Chrome driver is used to render html from javascript without actually opening up a browser window
'''
import sys
import os
import re
import shutil
import datetime as dt
import subprocess as sp
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from requests import get
from constants import PIC_PATH, DEFAULT, TOL
from random import choice

def astrowall():
    to_scrape, folder = gen_folder()

    if to_scrape:
        print("Scraping...")
        anchors = scrapity_scroopity()
        print("Filtering anchors...")
        ancs = filter_anchors(anchors)
        print("Filtering image URLs...")
        img_urls = get_img_links(ancs)
        print("Saving images...")
        save_imgs(img_urls, folder)
    else:
        print("You already scraped today.")

    set_wall(folder)


def gen_folder():
    '''
    Returns tuple of true if the folder of the week already exists and the folder name.
    '''
    if not os.path.isdir(PIC_PATH):
        os.makedirs(PIC_PATH)

    os.chdir(PIC_PATH)
    to_scrape = False

    new_folder = dt.date.today().strftime("%d%m%Y")

    if not os.path.isdir(new_folder):
        to_scrape = True
        os.makedirs(new_folder)

    return to_scrape, new_folder


def scrapity_scroopity():
    '''
    Show me the query
    Return a list of anchor tags for each reddit post.
    '''
    chrome_options = Options()  
    chrome_options.add_argument("--headless")

    vroom = webdriver.Chrome(chrome_options=chrome_options)
    vroom.get("https://old.reddit.com/r/spaceporn/top/?sort=top&t=week")
    soup = BeautifulSoup(vroom.page_source, features="html5lib")
    res = soup.find_all('a', {'data-event-action': 'title', 'class': 'title may-blank outbound'})    

    return res


def filter_anchors(anchors):
    '''
    Parse the given list of anchor tags and return a list of anchors satisfying the aspect ratio.

    Notes:
    https://askubuntu.com/questions/584688/how-can-i-get-the-monitor-resolution-using-the-command-line
    http://rubular.com/
    '''
    anc_pass = []
    for anc in anchors:
        # check resolution
        res = re.search('\d{4}\s*[x]\s*\d{4}', str(anc))
        if res:
            # check aspect ratio of pic
            w = int(res.group()[:4])
            h = int(res.group()[-4:])
            if abs(DEFAULT - w / h) < TOL:
                anc_pass.append(anc)

    return anc_pass


def get_img_links(anchors):
    '''
    Given a list of anchors that pass the aspect ratio test, extract their image urls to be downloaded.
    Note that imgur sometimes has the image embedded within some html.

    Using requests lib just to check header content because selenium is unable to do so.
    '''
    img_pass = []
    for anc in anchors:
        response = get(anc['data-href-url'])

        if "image" in response.headers['Content-Type']: # already an image url
            img_pass.append(anc['data-href-url'])
        elif "imgur.com/" in anc['data-href-url']:      # link to imgur site
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(chrome_options = chrome_options)
            driver.get(anc['data-href-url'])

            url = driver.find_element_by_css_selector('.image.post-image').find_element_by_tag_name('img').get_attribute('src')
            img_pass.append(url)

    return img_pass


def save_imgs(urls, folder):
    for i, url in enumerate(urls, 1):
        response = get(url, stream=True)
        f_name = response.url
        if f_name[-1] == '/':
            f_name = f_name[:-1]
        print(f_name)
        f_name = folder + '/' + f_name.replace('/', '=')
        with open(f_name, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)

def set_wall(folder):
    '''
    Selects and assigns a random wallpaper from the given folder.

    Notes:
    https://askubuntu.com/questions/66914/how-to-change-desktop-background-from-command-line-in-unity
    '''
    os.chdir(folder)
    if os.listdir() == []:
        print("There are no pictures to choose from {}".format(folder))
        sys.exit(1)
    wall = choice(os.listdir())
    wall = os.path.abspath(wall)
    print('Changing wallpaper to {}.'.format(wall))
    try:
        sp.check_output(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', '\'file://{}\''.format(wall)])
    except sp.CalledProcessError as e:
        print(e)
    except FileNotFoundError as e:
        print(e)

if __name__ == "__main__":
    astrowall()
