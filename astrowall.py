'''
TODO:
Add compatibility for Windows
Figure out how to show x number of reddit posts

NOTES:
- Selenium is only necessary for scraping the new reddit, since it is heavily-javascript driven,
    requests library is sufficient if scraping from the old reddit instead
- Selenium is used to scrape and BeautifulSoup used to parse
- Headless Chrome driver is used to render html from javascript without actually opening up a browser window
'''

def astrowall():
    import os
    status, folder = gen_folder()

    print("Scraping..." if status else "You already scraped today.")

    if status:
        anchors  = scrapity_scroopity()
        os.exit(0)
        print(anchors)
        img_urls = filter_anchors(anchors)
        save_imgs(img_urls)

    print("Changing wallpaper...")
    set_wall(folder)


def gen_folder():
    '''
    Returns tuple of true if the folder of the week already exists and the folder name.
    '''
    import datetime as dt
    import os
    from constants import PIC_PATH

    if not os.path.isdir(PIC_PATH):
        os.makedirs(PIC_PATH)

    os.chdir(PIC_PATH)
    status = True

    if not os.path.isdir(dt.date.today().strftime("%d%m%Y")):
        status = False
    os.makedirs(new_folder)

    return status, new_folder


def scrapity_scroopity():
    '''
    Show me the query
    Return a list of anchor tags for each reddit post.

    Notes:
    https://www.analyticsvidhya.com/blog/2015/10/beginner-guide-web-scraping-beautiful-soup-python/
    '''
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from bs4 import BeautifulSoup

    chrome_options = Options()  
    chrome_options.add_argument("--headless")

    vroom = webdriver.Chrome(chrome_options=chrome_options)
    vroom.get("https://old.reddit.com/r/spaceporn/top/?sort=top&t=week")
    soup = BeautifulSoup(d.page_source)

    return soup.find_all('a', {'data-event-action': 'title', 'class': 'title may-blank outbound'})    


def filter_anchors(anchors):
    '''
    Parse the given list of anchor tags and return a list of anchors satisfying the aspect ratio.

    Example accepted format for urls:
    <a 
    class="title may-blank outbound"
    data-event-action="title"
    data-href-url="https://cdn.eso.org/images/large/eso0905a.jpg"
    data-outbound-expiration="1533102938000"
    data-outbound-url="https://out.reddit.com/t3_9275r8?url=https%3A%2F%2Fcdn.eso.org%2Fimages%2Flarge%2Feso0905a.jpg&amp;token=AQAAWkthW-Ra4RKuGOx6IaqdaZiZUMjz6Kn_8Urgsdp-m5Sfo6cF&amp;app_name=reddit.com" 
    href="https://cdn.eso.org/images/large/eso0905a.jpg" 
    rel="" tabindex="1">The Carina Nebula [8408 x 8337]
    </a>

    Notes:
    https://askubuntu.com/questions/584688/how-can-i-get-the-monitor-resolution-using-the-command-line
    http://rubular.com/
    '''
    import re
    from constants import DEFAULT, TOL

    anc_pass = []
    for anc in anchors:
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
    from requests import get
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from bs4 import BeautifulSoup

    img_pass = []
    for anc in anchors:
        response = get(anc['data-href-url'])
    if "image" in response.headers['Content-Type']:
        img_pass.append(response.headers['Content-Type'])
    elif "imgur.com/" in anc['data-href-url']: # make a better check than this
        # support more image hosting sites?                
        # use selenium here
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(chrome_options = chrome_options)
        driver.get(anc['data-href-url'])

        url = driver.find_element_by_css_selector('.image.post-image').find_element_by_tag_name('img').get_attribute('src')
        img_pass.append(url)

    return img_pass


def save_imgs(urls):
    import shutil
    import requests

    for i, url in enumerate(urls, 1):
        response = requests.get(url, stream=True)
    with open('img{}.png'.format(i), 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)


def set_wall(folder):
    '''
    Selects and assigns a random wallpaper from the given folder.

    Notes:
    https://askubuntu.com/questions/66914/how-to-change-desktop-background-from-command-line-in-unity
    '''
    import os
    import subprocess as sp
    from random import choice

    os.chdir(folder)
    wall = choice(os.listdir())
    try:
        sp.check_output(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', 'file://{}'.format(wall)])
    except sp.CalledProcessError as e:
        print("An error occured while trying to change your wallpaper.\n"
                "Please ensure you have 'gsettings' installed.")


if __name__ == "__main__":
    astrowall()
