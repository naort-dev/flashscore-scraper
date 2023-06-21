import scrapy
import json
from datetime import datetime
import time
import psutil
from ..items import StandingItem, FixtureItem, LeagueItem
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from pyvirtualdisplay import Display
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# from flashscore.items import TickerItem
# from flashscore.utils import cleanTickers

def kill_children(proc):
    for sub_proc in proc.children(True):
        sub_proc.kill()
    proc.kill()

def kill_idle_process():
    # names = ['Xvfb', 'chromedriver', 'chromedriver.ex']
    names = ['Xvfb']

    for proc in psutil.process_iter():
        """ current time in seconds """
        current_time = time.time()

        try:
            pinfo = proc.as_dict(attrs=['pid', 'ppid', 'name', 'create_time', 'username', 'cwd'])
            print(pinfo['name'])
            """ if orphan process """
            # if pinfo['username'] == 'www-data' and pinfo['name'] in names:
            if pinfo['name'] in names:
                kill_children(proc)

        except psutil.NoSuchProcess:
            pass

class FlashScoreSpider(scrapy.Spider):
    crawlera_enabled = False

    name = "flashscore"
    sports = [
        'football', 
        'hockey', 
        'handball'
    ]

    base_url = 'https://www.flashscore.com'
    driver = ''

    def __init__(self, *args, **kwargs):

        super(FlashScoreSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        # https://www.flashscore.com/football/england/premier-league/standings/
        # yield scrapy.Request(
        #     url='https://www.flashscore.com/hockey/czech-republic/extraliga/',
        #     callback=self.parse_league,
        #     method="GET",
        #     meta={
        #         'url': 'https://www.flashscore.com/hockey/czech-republic/extraliga/',
        #         'sport': 'hockey',
        #         'country': 'Czech Republic',
        #         'league': 'extraliga'
        #     }
        # )
        # self.driver = self.getDriver()
        kill_idle_process()
        for sport in self.sports:
            yield scrapy.Request(
                url=self.base_url + '/' + sport,        
                callback=self.parse_sport,
                method="GET",
                meta={
                    'url': self.base_url + '/' + sport,
                    'sport': sport
                }
            )
            # break

    def parse_sport(self, response):
        try:
            driver = self.getDriver()
            driver.get(response.meta['url'])
            soup = BeautifulSoup(driver.page_source, features="html.parser")
            kill_idle_process()
            driver.quit()
            # time.sleep(2)
            print('======================================================')
            for menu in soup.findAll('ul', class_='tournament-menu'):
                for item in menu.findAll('li'):
                    link = item.find('a')
                    if link:
                        if len(link.attrs['href'].split('/')) == 4:
                            print(link.text.strip(), link.attrs['href'])
                            yield scrapy.Request(
                                url=self.base_url + link.attrs['href'],
                                callback=self.parse_country,
                                method="GET",
                                meta={
                                    'url': self.base_url + link.attrs['href'],
                                    'sport': response.meta['sport'],
                                    'country': link.text.strip()
                                }
                            )
            print('======================================================')
            
            # print(len(soup.find('ul', class_='country-list').findAll('li')))
        except Exception as e:
            print(response.meta['url'], e)
            if driver:
                kill_idle_process()
                driver.quit()

    def parse_country(self, response):
        try:
            driver = self.getDriver()
            driver.get(response.meta['url'])
            soup = BeautifulSoup(driver.page_source, features="html.parser")
            kill_idle_process()
            driver.quit()
            print('======================================================')
            # time.sleep(2)
            for item in soup.find('ul', class_='selected-country-list').findAll('li'):
                link = item.find('a')
                if link and 'More (' not in link.text.strip():
                    print(link.text.strip(), link.attrs['href'])
                    item = LeagueItem(
                        sport = response.meta['sport'].strip(),
                        country = response.meta['country'].strip(),
                        league = link.text.strip(),
                        driver = self.driver,
                    )
                    yield item
                    yield scrapy.Request(
                        url=self.base_url + link.attrs['href'],
                        callback=self.parse_league,
                        method="GET",
                        meta={
                            'url': self.base_url + link.attrs['href'],
                            'sport': response.meta['sport'],
                            'country': response.meta['country'],
                            'league': link.text.strip()
                        }
                    )
            
            print('======================================================')
        except Exception as e:
            print(response.meta['url'], e)
            if driver:
                kill_idle_process()
                driver.quit()

        # print('++++++++++++++++++++++++++++++++++++++++', response.meta['url'] + 'standings/')
        # self.parse_fixture(response.meta['url'] + 'fixtures/', response.meta)
        # return

    def getDriver(self):
        options = webdriver.ChromeOptions()
        options.headless = True
        display = Display(visible=0, size=(800, 600))
        display.start()
        driver = webdriver.Chrome('./chromedriver.exe', options=options)
        return driver

    def get_standing_info(self, soup):
        info = {}
        for team in soup.findAll('div', class_='row___1rtP1QI'):
            team_name = team.find(
                'a', class_='rowCellParticipantName___38vskiN').text
            cells = []
            for cell in team.findAll('span', class_='rowCell____vgDgoa'):
                cells.append(cell.text)
            cells.append(
                team.find('div', class_='rowCell____vgDgoa').text.replace('.', '').strip())
            info[team_name] = cells
        return info

    def parse_league(self, response):
        print('-----------------------------------')
        print(response.meta['url'], 'starts running...')
        now = datetime.now()
        response.meta['scraped_date'] = now.strftime("%Y-%m-%d %H:%M:%S")
        try:
            driver = self.getDriver()

            # Parse Standings Table
            standing_url = response.meta['url'] + 'standings/'
            driver.get(standing_url)
            
            for element in driver.find_elements_by_css_selector('.tabs__tab'):
                print(element.get_attribute("href"))
                if element.get_attribute("href") == 'https://www.flashscore.com/table':
                    element.click()
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, features="html.parser")
            season = soup.find('div', class_='teamHeader__text').text.strip()
            all_info = self.get_standing_info(soup)
            print(all_info)
            for element in driver.find_elements_by_css_selector('.subTabs__tab'):
                if element.get_attribute("href") == 'https://www.flashscore.com/table/home':
                    element.click()
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, features="html.parser")
            home_info = self.get_standing_info(soup)

            for element in driver.find_elements_by_css_selector('.subTabs__tab'):
                # print(element.get_attribute("href"))
                if element.get_attribute("href") == 'https://www.flashscore.com/table/away':
                    element.click()
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, features="html.parser")
            kill_idle_process()
            driver.quit()
            away_info = self.get_standing_info(soup)
            # print('======================')
            # print(away_info)
            # print('======================')
            for team in home_info.keys():
                print(all_info[team])
                if len(all_info[team]) > 7:
                    item = StandingItem(
                        sport=response.meta['sport'],
                        country=response.meta['country'],
                        league=response.meta['league'],
                        team=team,
                        overall_rank=all_info[team][7],
                        home_rank=home_info[team][7],
                        away_rank=away_info[team][7],
                        home_mp=home_info[team][0],
                        home_w=home_info[team][1],
                        home_wo=home_info[team][2],
                        home_lo=home_info[team][3],
                        home_l=home_info[team][4],
                        home_gf=home_info[team][5].split(':')[0],
                        home_ga=home_info[team][5].split(':')[1],
                        home_pts=home_info[team][6],
                        away_mp=away_info[team][0],
                        away_w=away_info[team][1],
                        away_d=away_info[team][2],
                        away_l=away_info[team][3],
                        away_gf=away_info[team][5].split(':')[0],
                        away_ga=away_info[team][5].split(':')[1],
                        away_pts=away_info[team][6],
                        away_wo=away_info[team][3],
                        away_lo=away_info[team][4],
                        scraped_date=response.meta['scraped_date'],
                        season=season,
                    )
                else:
                    item = StandingItem(
                        sport=response.meta['sport'],
                        country=response.meta['country'],
                        league=response.meta['league'],
                        team=team,
                        overall_rank=all_info[team][6],
                        home_rank=home_info[team][6],
                        away_rank=away_info[team][6],
                        home_mp=home_info[team][0],
                        home_w=home_info[team][1],
                        home_d=home_info[team][2],
                        home_l=home_info[team][3],
                        home_gf=home_info[team][4].split(':')[0],
                        home_ga=home_info[team][4].split(':')[1],
                        home_pts=home_info[team][5],
                        home_wo=None,
                        home_lo=None,
                        away_mp=away_info[team][0],
                        away_w=away_info[team][1],
                        away_d=away_info[team][2],
                        away_l=away_info[team][3],
                        away_gf=away_info[team][4].split(':')[0],
                        away_ga=away_info[team][4].split(':')[1],
                        away_pts=away_info[team][5],
                        away_wo=None,
                        away_lo=None,
                        season=season,
                        scraped_date=response.meta['scraped_date']
                    )
                print('=============================================')
                yield item
                print('=============================================')

            # Parse Fixtures Table
            driver = self.getDriver()
            fixture_url = response.meta['url'] + 'fixtures/'
            driver.get(fixture_url)
            soup = BeautifulSoup(driver.page_source, features="html.parser")
            kill_idle_process()
            driver.quit()
            season = soup.find('div', class_='teamHeader__text').text.strip()
            for match in soup.findAll('div', class_='event__match'):
                match_time = match.find(
                    'div', class_='event__time').text.strip()
                home_team = match.find(
                    'div', class_='event__participant--home').text.strip()
                away_team = match.find(
                    'div', class_='event__participant--away').text.strip()
                item = FixtureItem(
                    sport=response.meta['sport'],
                    country=response.meta['country'],
                    league=response.meta['league'],
                    match_time=match_time,
                    home_team=home_team,
                    away_team=away_team,
                    season=season,
                    scraped_date=response.meta['scraped_date']
                )
                yield item
        except Exception as e:
            print(standing_url, e)
            if driver:
                kill_idle_process()
                driver.quit()

    