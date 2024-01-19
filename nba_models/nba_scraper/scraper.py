from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date
from datetime import datetime
from selenium.webdriver.chrome.service import Service


class Soup:
    def __init__(self, dynamic=False, element="", vm=False) -> None:
        self.dynamic = dynamic
        self.element = element

        if self.dynamic:
            options = webdriver.ChromeOptions()
            options.page_load_strategy = "none"
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument("--disable-images")
            options.add_argument("--no-sandbox")

            if vm:
                # FOR VM
                s = Service('/usr/local/bin/chromedriver')
                self.driver = webdriver.Chrome(service=s, options=options)
            else:
                # FOR MY MACHINE
                self.driver = webdriver.Chrome(options=options)

            

    def get_soup(self, url):
        if self.dynamic:
            self.driver.get(url)
            if self.element != "":
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, self.element))
                )
            else:
                time.sleep(1)
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "lxml")
        else:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'lxml')

        return soup
    
    
    def __del__(self):
        if self.dynamic:
            self.driver.quit()

class NBAScraper:
    def __init__(self, vm=False) -> None:
        self._base_url = "https://www.basketball-reference.com"
        self.vm=vm

        self._links = {
            'Hawks': '/teams/ATL/',
            'Celtics': '/teams/BOS/', 
            'Nets': '/teams/BRK/', 
            'Hornets': '/teams/CHO/', 
            'Bulls': '/teams/CHI/', 
            'Cavaliers': '/teams/CLE/', 
            'Mavericks': '/teams/DAL/', 
            'Nuggets': '/teams/DEN/', 
            'Pistons': '/teams/DET/', 
            'Warriors': '/teams/GSW/', 
            'Rockets': '/teams/HOU/', 
            'Pacers': '/teams/IND/', 
            'Clippers': '/teams/LAC/', 
            'Lakers': '/teams/LAL/', 
            'Grizzlies': '/teams/MEM/', 
            'Heat': '/teams/MIA/', 
            'Bucks': '/teams/MIL/', 
            'Timberwolves': '/teams/MIN/', 
            'Pelicans': '/teams/NOP/', 
            'Knicks': '/teams/NYK/', 
            'Thunder': '/teams/OKC/', 
            'Magic': '/teams/ORL/', 
            '76ers': '/teams/PHI/', 
            'Suns': '/teams/PHO/', 
            'Trail Blazers': '/teams/POR/', 
            'Kings': '/teams/SAC/', 
            'Spurs': '/teams/SAS/', 
            'Raptors': '/teams/TOR/', 
            'Jazz': '/teams/UTA/', 
            'Wizards': '/teams/WAS/'
            }

        self._season_desc = {}
        self._game_desc = {}

    #####################
    # PRIVATE FUNCTIONS #
    #####################

    # Scrape teams and links from site and return as dictionary
    def _get_links(self):
        soup = Soup(vm=self.vm).get_soup(self._base_url + "/teams/")

        # Create dictionary with team: link
        rows = soup.find(id="teams_active").find_all(class_="full_table")
        dic = {}
        for row in rows:
            tag = row.find("a")
            team = "Trail Blazers" if tag.text.split()[-1] == "Blazers" else tag.text.split()[-1]

            dic[team] = tag.get("href")

        return dic
    
    # Split dictionary in half so you don't get timed out
    def _split_dict(self, d):
        keys = list(d.keys())
        mid = len(keys) // 2
        
        dict1 = {key: d[key] for key in keys[:mid]}
        dict2 = {key: d[key] for key in keys[mid:]}
        
        return dict1, dict2
    
    def _create_season_desc_dic(self):
        full_url = "https://www.basketball-reference.com/teams/NOP/2024.html"

        soup = Soup(dynamic=True, element='team_and_opponent', vm=self.vm).get_soup(full_url)

        # Getting english descriptions
        header = soup.find("table", id="team_and_opponent").find("thead").find_all("th")
        for tag in header[1:]:
            self._season_desc[tag["data-stat"]] = tag["aria-label"]

    def _create_game_desc_dic(self):
        full_url = "https://www.basketball-reference.com/teams/NOP/2024/gamelog/"

        soup = Soup(vm=self.vm).get_soup(full_url)
        table = soup.find("table", id="tgl_basic")

        # Getting english descriptions
        header = table.find("thead").find_all("tr")[1].find_all("th")
        for tag in header:
            stat = tag["data-stat"]
            if stat == "x":
                continue

            if stat == "game_location":
                self._game_desc[stat] = "Game Location"
            else:
                self._game_desc[stat] = tag["aria-label"]


    
    ####################
    # PUBLIC FUNCTIONS #
    ####################


    def get_single_team_season_stats(self, team: str):
        print(f"Fetching season data for {team}..")

        full_url = self._base_url + self._links[team] + "2024.html"

        # Getting english descriptions if not already created
        if not self._season_desc:
            self._create_season_desc_dic()
            self.s = Soup(dynamic=True, element='team_and_opponent')

        soup = self.s.get_soup(full_url)

        # Getting team statistics
        rows = soup.find("table", id="team_and_opponent").find("tbody").find_all("tr")
        stats_dic = {}

        # Record
        misc_table = soup.find("table", id="team_misc").find("tr", {"data-row": 0})
        wins = misc_table.find("td", {"data-stat": "wins"}).text
        losses = misc_table.find("td", {"data-stat": "losses"}).text

        games_played = rows[0].find("td", {"data-stat":"g"}).text
        stats_dic["Team"] = team
        stats_dic["Games"] = games_played
        stats_dic["Record"] = f"{wins}-{losses}"
        for tag in rows[1].find_all("td")[1:]:
            lookup = tag["data-stat"].replace("_per_g", "")
            stats_dic[self._season_desc[lookup] + " Per Game"] = tag.text

        return stats_dic

    def get_all_team_season_stats(self):
        print("Fetching data for all teams..")
        self._create_season_desc_dic()
        team_data = {}

        self.s = Soup(dynamic=True, element='team_and_opponent', vm=self.vm)

        # Getting english descriptions if not already created
        self._create_season_desc_dic()

        links1, links2 = self._split_dict(self._links)
        for team in links1:
            dic = self.get_single_team_season_stats(team)
            team_data[team] = dic
        
        print("Sleeping for a min bc www.basketball-reference.com is stupid!")
        time.sleep(61)

        for team in links2:
            dic = self.get_single_team_season_stats(team)
            team_data[team] = dic
        
        print("Done fetching all data\n")
        return team_data
    
    def get_single_team_game_stats(self, team: str, last_n_games: int = 100):
        print(f"Fetching game stats for {team}..")
        full_url = self._base_url + self._links[team] + "2024/gamelog/"

        soup = Soup(vm=self.vm).get_soup(full_url)
        table = soup.find("table", id="tgl_basic")

        if not self._game_desc:
            self._create_game_desc_dic()
        
        # Getting statistics
        games = table.find("tbody").find_all("tr")
        lst = []
        for game in games[-last_n_games:]:
            dic = {}
            cols = game.find_all("td")
            for col in cols:
                if col["data-stat"] == "x":
                    continue

                key = self._game_desc[col["data-stat"]]
                if key == "Game Location":
                    val = "Away" if col.text == "@" else "Home"
                    dic[key] = val
                elif key == "W/L":
                    key = "Win/Loss"
                    dic[key] = col.text
                else:
                    dic[key] = col.text

            lst.append(dic)
        
        return lst
    
    # Gets matchups for nba games and betting lines
    def get_matchups(self):
        today = date.today()
        print(f"Fetching matchups for {today}..")

        soup = Soup(vm=self.vm).get_soup("https://www.vegasinsider.com/nba/matchups/")

        header_rows = soup.find("tbody", id="trends-table-bets--0").find_all("tr", class_="header")
        dic = {}
        for header_row in header_rows:
            # Create a new table starting from the header row
            current_table = str(header_row)

            # Find the following siblings (sibling rows) until the next header row
            next_row = header_row.find_next_sibling()
            while next_row and 'header' not in next_row.get('class', []):
                current_table += str(next_row)
                next_row = next_row.find_next_sibling()

            # table for each matchup
            table = BeautifulSoup(current_table, 'html.parser')

            # Getting matchup and saving as tup
            teams_soup = table.find_all("a", class_="team-name")
            teams = [tag.find("span").text.strip() for tag in teams_soup]
            home_team = teams[-1]
            temp = (teams[0], teams[1])
            tup = tuple(sorted(temp))
            # dic["matchup"] = tup

            # Getting abbreviations
            tags = {tag.get("data-abbr"):  tag.find("span").text.strip() for tag in teams_soup}

            # Getting lines
            lines_dic = {}
            lines_soup = table.find("tr", class_="game-odds current")
            spread = lines_soup.find('td', {'data-filter': 'spread'}).text.strip()
            total = lines_soup.find('td', {'data-filter': 'total'}).text.strip()[1:]
            temp = spread.split()[0]

            ## Handling if N/A appears for line at vegas site (no line for game)
            try:
                lines_dic["spread"] = spread.replace(temp, tags[temp])
            except Exception as e:
                print(f"ERROR - NO SPREAD FOR {tup}")
                print(e)
                continue

            lines_dic["total"] = total
            lines_dic["home_team"] = home_team
            # dic["lines"] = lines_dic


            dic[tup] = lines_dic

        print("Done fetching matchups!\n")

        return dic
    
    def get_yesterday_scores(self):
    
        soup = Soup(vm=self.vm).get_soup(self._base_url)

        tables = soup.find("div", class_="game_summaries").find_all("div", class_="game_summary expanded nohover")
        dic = {}
        for table in tables:
            winner_tag = table.find("tr", class_="winner")
            win_team = winner_tag.find("a").text
            win_score = float(winner_tag.find("td", class_="right").text)

            loser_tag = table.find("tr", class_="loser")
            lose_team = loser_tag.find("a").text
            lose_score = float(loser_tag.find("td", class_="right").text)

            for team in self._links:
                if team in win_team:
                    win_team = team
                if team in lose_team:
                    lose_team = team

            temp = (win_team, lose_team)
            tup = tuple(sorted(temp))



            dic[tup] = {win_team: win_score, lose_team: lose_score}

        return dic
    
    def get_single_team_prev_lines(self, team, last_n_games=100):
        team = team.lower().replace(" ", "-")
        url = "https://www.vegasinsider.com/nba/teams/" + team
        soup = Soup(vm=self.vm).get_soup(url)

        dic = {}

        try:
            rows = soup.find("table", class_="schedule-table").find("tbody", class_="alternating").find_all("tr")
        except:
            print(f"{url} BROKEN")
            return dic

        games = []
        for row in rows:
            info = row.find_all("td")

            # Game hasnt happened yet
            temp = info[3].text.rstrip()
            if temp == "":
                break

            games.append(row)

        for row in games[-last_n_games:]:
            info = row.find_all("td")

            date = info[0].text
            date = datetime.strptime(date, "%b %d, %Y").strftime("%Y-%m-%d")

            temp = info[1].find("a").text
            location = "away" if "@" in temp else "home"
            opp = temp.replace("@", "")

            temp = info[2].text.split("/")
            line = float(temp[0].strip())
            ou = float(temp[1].strip())

            temp = info[4].text.split("/")
            line_result = temp[0].strip().lower()
            ou_result = temp[1].strip().lower()

            temp_dic = {
                "home/away": location,
                "opp": opp,
                "spread": line,
                "ou": ou,
                "ats_result": line_result,
                "ou_result": ou_result
            }
            dic[date] = temp_dic

        return dic
    
