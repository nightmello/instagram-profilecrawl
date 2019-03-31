"""
Grab the followers info by the target user

input: target user
output: followers info
"""
import sys
from time import sleep

import pandas as pd
from instapy import InstaPy
from instapy import set_workspace
from instapy import smart_run
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options

from util.account import login
from util.chromedriver import init_chromedriver
from util.datasaver import Datasaver
from util.exceptions import PageNotFound404, NoInstaProfilePageFound
from util.extractor import extract_exact_info
from util.instalogger import InstaLogger
from util.settings import Settings
from util.util import web_adress_navigator

chrome_options = Options()
chromeOptions = webdriver.ChromeOptions()
prefs = {'profile.managed_default_content_settings.images': 2,
         'disk-cache-size': 4096}
chromeOptions.add_experimental_option("prefs", prefs)
chrome_options.add_argument('--dns-prefetch-disable')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--lang=en-US')
chrome_options.add_argument('--headless')
chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'en-US'})

capabilities = DesiredCapabilities.CHROME


def get_user_info(browser, username):
    """Get the basic user info from the profile screen"""
    num_of_posts = 0
    followers = {'count': 0}
    following = {'count': 0}
    prof_img = ""
    bio = ""
    bio_url = ""
    alias = ""
    container = browser.find_element_by_class_name('v9tJq')
    isprivate = False

    try:
        if container.find_element_by_class_name('Nd_Rl'):
            isprivate = True
    except BaseException:
        isprivate = False

    try:
        alias = container.find_element_by_class_name('-vDIg').find_element_by_tag_name('h1').text
    except BaseException:
        InstaLogger.logger().info("alias is empty")

    try:
        bio = container.find_element_by_class_name(
            '-vDIg').find_element_by_tag_name('span').text
    except BaseException:
        InstaLogger.logger().info("Bio is empty")

    try:
        bio_url = container.find_element_by_class_name('yLUwa').text
    except BaseException:
        InstaLogger.logger().info("Bio Url is empty")

    try:
        img_container = browser.find_element_by_class_name('RR-M-')
        prof_img = img_container.find_element_by_tag_name(
            'img').get_attribute('src')
    except BaseException:
        InstaLogger.logger().info("image is empty")

    try:
        infos = container.find_elements_by_class_name('Y8-fY')

        try:
            num_of_posts = extract_exact_info(infos[0])
        except BaseException:
            InstaLogger.logger().error("Number of Posts empty")

        try:
            following = {'count': extract_exact_info(infos[2])}
        except BaseException:
            InstaLogger.logger().error("Following is empty")

        try:
            followers = {'count': extract_exact_info(infos[1])}
        except BaseException:
            InstaLogger.logger().error("Follower is empty")
    except BaseException:
        InstaLogger.logger().error("Infos (Following, Abo, Posts) is empty")

    information = {
        'alias': alias,
        'username': username,
        'bio': bio,
        'prof_img': prof_img,
        'num_of_posts': num_of_posts,
        'followers': followers,
        'following': following,
        'bio_url': bio_url,
        'isprivate': isprivate,
    }

    InstaLogger.logger().info("alias name: " + information['alias'])
    InstaLogger.logger().info("bio: " + information['bio'])
    InstaLogger.logger().info("url: " + information['bio_url'])
    InstaLogger.logger().info("Posts: " + str(information['num_of_posts']))
    InstaLogger.logger().info("Follower: " + str(information['followers']['count']))
    InstaLogger.logger().info("Following: " + str(information['following']['count']))
    InstaLogger.logger().info("isPrivate: " + str(information['isprivate']))

    return information


def extract_information(browser, username):
    try:
        user_link = "https://www.instagram.com/{}/".format(username)
        web_adress_navigator(browser, user_link)
    except PageNotFound404 as e:
        raise NoInstaProfilePageFound(e)

    try:
        userinfo = get_user_info(browser, username)
    except Exception as err:
        quit()

    return userinfo


# https://github.com/timgrossmann/InstaPy#grab-followers-of-a-user
def grab_followers(target_user='nightmello'):
    # set workspace folder at desired location (default is at your home folder)
    set_workspace(path=None)

    # get an InstaPy session!
    session = InstaPy(username=Settings.login_username,
                      password=Settings.login_password,
                      headless_browser=True)

    with smart_run(session):
        selected_followers = session.grab_followers(
            username=target_user,
            amount="full",
            live_match=True,
            store_locally=True)

        return selected_followers


def find_real_fans(target_user='nightmello'):
    followers_list = grab_followers(target_user)
    sleep(30)

    fan_list = {}
    try:
        browser = init_chromedriver(chrome_options, capabilities)
    except Exception as exc:
        print(exc)
        sys.exit()

    try:
        login(
            browser,
            Settings.login_username,
            Settings.login_password)

        for user in followers_list:
            print('Extracting information from ' + user)
            try:
                information = extract_information(browser, user)
                fan_list[user] = information
            except BaseException:
                print("Error with user " + user)
                sys.exit(1)

            Datasaver.save_profile_json(user, information)
        print("\nFinished.\n")

    except KeyboardInterrupt:
        print('Aborted...')

    finally:
        browser.delete_all_cookies()
        browser.close()

    df = pd.DataFrame(columns=['alias', 'private', 'num_posts', 'num_followers', 'num_following'])
    for id, element in enumerate(fan_list):
        alias = element
        is_private = fan_list[element]['isprivate']
        num_posts = fan_list[element]['num_of_posts']
        num_followers = fan_list[element]['followers']['count']
        num_following = fan_list[element]['following']['count']
        info = [alias, is_private, num_posts, num_followers, num_following]
        tmp = pd.DataFrame([info], columns=['alias', 'private', 'num_posts', 'num_followers', 'num_following'])
        df = df.append(tmp, ignore_index=True)
        print(id, info)

    df.to_csv('real_fans_of_{}.csv'.format(target_user), sep='\t', encoding='utf-8')
    return df


find_real_fans('nightmello')
