"""
input: target_user_list
output: followers of user in target_user_list
"""
import sys
from time import time, sleep

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
prefs = {'profile.managed_default_content_settings.images': 2, 'disk-cache-size': 4096}
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
    except:
        isprivate = False

    try:
        alias = container.find_element_by_class_name('-vDIg').find_element_by_tag_name('h1').text
    except:
        InstaLogger.logger().info("alias is empty")

    try:
        bio = container.find_element_by_class_name('-vDIg').find_element_by_tag_name('span').text
    except:
        InstaLogger.logger().info("Bio is empty")

    try:
        bio_url = container.find_element_by_class_name('yLUwa').text
    except:
        InstaLogger.logger().info("Bio Url is empty")

    try:
        img_container = browser.find_element_by_class_name('RR-M-')
        prof_img = img_container.find_element_by_tag_name('img').get_attribute('src')
    except:
        InstaLogger.logger().info("image is empty")

    try:
        infos = container.find_elements_by_class_name('Y8-fY')

        try:
            num_of_posts = extract_exact_info(infos[0])
        except:
            InstaLogger.logger().error("Number of Posts empty")

        try:
            following = {'count': extract_exact_info(infos[2])}
        except:
            InstaLogger.logger().error("Following is empty")

        try:
            followers = {'count': extract_exact_info(infos[1])}

            try:
                if isprivate is True:
                    InstaLogger.logger().info("Cannot get Follower List - private account")
                else:
                    followers['list'] = extract_followers(browser, username)
                    # print(followers['list'])
            except Exception as exception:
                # Output unexpected Exceptions.
                print("Unexpected error:", sys.exc_info()[0])
                print(exception)

                InstaLogger.logger().error("Cannot get Follower List")
        except:
            InstaLogger.logger().error("Follower is empty")
    except:
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

    for id, fan in enumerate(information['followers']['list']):
        print(id, fan)
    return information


def extract_followers(browser, username):
    InstaLogger.logger().info('Extracting follower from ' + username)
    try:
        user_link = "https://www.instagram.com/{}".format(username)
        web_adress_navigator(browser, user_link)
    except PageNotFound404 as e:
        raise NoInstaProfilePageFound(e)
    sleep(5)

    followers = []

    # find number of followers
    elem = browser.find_element_by_xpath(
        "//span[@id='react-root']//header[@class='vtbgv ']//ul[@class='k9GMp ']/child::li[2]/a/span")
    elem.click()
    sleep(15)

    # remove suggestion list and load 24 list elements after this
    browser.execute_script("document.getElementsByClassName('isgrP')[0].scrollTo(0,500)")
    sleep(10)

    elems = browser.find_elements_by_xpath("//body//div[@class='PZuss']//a[@class='FPmhX notranslate _0imsa ']")
    num = len(elems)
    print('debug info:', num)
    for i in range(num):
        val = elems[i].get_attribute('innerHTML')
        print('debug info -- first user:', i, val)
        followers.append(val)

    try:
        for i in range(num):
            browser.execute_script("document.getElementsByClassName('PZuss')[0].children[0].remove()")
    except:
        pass

    isDone = False
    while True:
        try:
            start = time()
            browser.execute_script(
                "document.getElementsByClassName('isgrP')[0].scrollTo(0,document.getElementsByClassName('isgrP')[0].scrollHeight)")

            while True:
                try:
                    loop = int(
                        browser.execute_script("return document.getElementsByClassName('PZuss')[0].children.length"))
                    if loop == num * 2:
                        break
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    continue
                if time() - start > 10:
                    isDone = True
                    break

            if isDone:
                break

            elems = browser.find_elements_by_xpath("//body//div[@class='PZuss']//a[@class='FPmhX notranslate _0imsa ']")
            num = len(elems)
            print('debug info:', num)
            list_segment = ""
            for i in range(12):
                val = elems[i].get_attribute('innerHTML')
                list_segment += (val + '\n')
                print('debug info -- middle user:', i, val)
                followers.append(val)

            for i in range(12):
                browser.execute_script("document.getElementsByClassName('PZuss')[0].children[0].remove()")

            print(time() - start)

        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            continue

    list_segment = ""
    elems = browser.find_elements_by_xpath("//body//div[@class='PZuss']//a[@class='FPmhX notranslate _0imsa ']")
    num = len(elems)
    print('debug info:', num)
    for i in range(len(elems)):
        val = elems[i].get_attribute('innerHTML')
        list_segment += (val + '\n')
        print('debug info -- last user:', i, val)
        followers.append(val)

    return followers


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


def run(usernames=['nightmello']):
    try:
        browser = init_chromedriver(chrome_options, capabilities)
    except Exception as exc:
        print(exc)
        sys.exit()

    try:
        for username in usernames:
            print('Extracting information from ' + username)
            try:
                login(browser, Settings.login_username, Settings.login_password)
                information = extract_information(browser, username)
            except:
                print("Error with user " + username)
                sys.exit(1)

            Datasaver.save_profile_json(username, information)
            print("\nFinished.\n")

    except KeyboardInterrupt:
        print('Aborted...')

    finally:
        browser.delete_all_cookies()
        browser.close()


run()
