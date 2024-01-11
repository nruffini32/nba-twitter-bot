import numpy as np
from .nba_scraper import NBAScraper
from datetime import date
import sqlite3
from .vegas import Vegas
import os

class Model:
    def __init__(self, dry_run=False, vm=False) -> None:
        if dry_run:
            print("DRY RUN")

        if vm:
            print("ON VM")

        self.nba = NBAScraper(vm=vm)
        self.cur_dir = os.path.dirname(os.path.realpath(__file__))
        self.dry_run = dry_run
        self.matchups = self.nba.get_matchups()
        

    # Creatiing percentage dictionary
    def get_cover_percentages(self, todays_teams, recent_games=False):
        # Getting game history
        dic = {}
        for team in todays_teams:
            if recent_games:
                dic[team] = self.nba.get_single_team_prev_lines(team, 7)
            else:
                dic[team] = self.nba.get_single_team_prev_lines(team)
        
        trends = {}
        for team in dic:
            full_info = dic[team]
            
            home_dog_tot = 0
            home_dog_win = 0
            home_fav_tot = 0
            home_fav_win = 0
            away_dog_tot = 0
            away_dog_win = 0
            away_fav_tot = 0
            away_fav_win = 0
            
            # Going through each game
            for game in full_info:
                game_dic = full_info[game]
                    
                # home dog
                if game_dic["home/away"] == "home" and game_dic["spread"] > 0:
                    home_dog_tot += 1
                    if game_dic["ats_result"] == "won": 
                        home_dog_win += 1
                # home favorite
                elif game_dic["home/away"] == "home" and game_dic["spread"] < 0:
                    home_fav_tot += 1
                    if game_dic["ats_result"] == "won": 
                        home_fav_win += 1
                # away dog
                elif game_dic["home/away"] == "away" and game_dic["spread"] > 0:
                    away_dog_tot += 1
                    if game_dic["ats_result"] == "won": 
                        away_dog_win += 1
                # away favorite
                elif game_dic["home/away"] == "away" and game_dic["spread"] < 0:
                    away_fav_tot += 1
                    if game_dic["ats_result"] == "won": 
                        away_fav_win += 1
                # pick em
                else:
                    print("pick em")
                    
                    
            team_dic = {
                "away_cover_percent": (away_dog_win+away_fav_win)/(away_dog_tot+away_fav_tot) if (away_dog_tot+away_fav_tot) != 0 else np.nan,
                "away_tot": away_dog_tot+away_fav_tot,

                "away_dog_cover_percent": away_dog_win/away_dog_tot if away_dog_tot != 0 else np.nan,
                "away_dog_tot": away_dog_tot,

                "away_fav_cover_percent": away_fav_win/away_fav_tot if away_fav_tot != 0 else np.nan,
                "away_fav_tot": away_fav_tot,
        
                "home_cover_percent": (home_dog_win+home_fav_win)/(home_dog_tot+home_fav_tot) if (home_dog_tot+home_fav_tot) != 0 else np.nan,
                "home_tot": home_dog_tot+home_fav_tot,

                "home_dog_cover_percent": home_dog_win/home_dog_tot if home_dog_tot != 0 else np.nan,
                "home_dog_tot": home_dog_tot,

                "home_fav_cover_percent": home_fav_win/home_fav_tot if home_fav_tot != 0 else np.nan,
                "home_fav_tot": home_fav_tot
            }
            trends[team] = team_dic

        return trends
    
    def make_picks(self, recent_games=False):

        todays_teams = [team for game in self.matchups.keys() for team in game]

        if recent_games:
            print("Fetching trends for recent games...")
            trends = self.get_cover_percentages(todays_teams, recent_games=True)
            db = f'{self.cur_dir}/nba_pick_recent_data_2023.db'
        else:
            print("Fetching trends for all games...")
            trends = self.get_cover_percentages(todays_teams)
            db = f'{self.cur_dir}/nba_pick_data_2023.db'
        print()

        # Connect to SQLite database (create a new file if it doesn't exist)
        conn = sqlite3.connect(db)
        cur = conn.cursor()

        picks = ""

        ## Recent pick logic
        if recent_games:
            print("---- PICKS FOR LAST 7 GAMES ----")
 
            # cur.execute("drop table if exists bets")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS bets (
                    id INTEGER PRIMARY KEY,
                    date DATE,
                    matchup_team1 TEXT,
                    matchup_team2 TEXT,
                    spread TEXT,
                    home_team TEXT,
                    home_cover_percent REAL,
                    away_cover_percent REAL,
                    pick TEXT,
                    threshold REAL,
                    win_loss TEXT
                )
            ''')
            conn.commit()

            for matchup, info in self.matchups.items():
                # Getting cover percentages
                team1, team2 = matchup
                spread_info = info['spread'].rsplit(" ", 1)
                dog_team = team1 if spread_info[0] == team2 else team2

                home_team = info['home_team']
                away_team = team1 if team2 == home_team else team2

                home_cover_percent = trends[home_team]['home_cover_percent']
                home_games = trends[home_team]['home_tot']
                away_cover_percent = trends[away_team]['away_cover_percent']
                away_games = trends[away_team]['away_tot']

                # Logic for picks
                threshold = 0.3
                high_limit = 1 - threshold
                low_limit = threshold

                if home_cover_percent >= high_limit and away_cover_percent >= high_limit:
                    pick = None
                elif home_cover_percent <= low_limit and away_cover_percent <=low_limit:
                    pick = None
                elif (home_cover_percent >= high_limit and home_games >1 ) or (away_cover_percent <= low_limit and away_games > 1):
                    # We want the home team
                    if home_team == spread_info[0]:
                        pick = info['spread']
                    else:
                        pick = f"{dog_team} +{spread_info[-1][1:]}"

                elif (home_cover_percent <= low_limit and home_games >1) or (away_cover_percent >= high_limit and away_games > 1):
                    # We want the away team
                    if away_team == spread_info[0]:
                        pick = info["spread"]
                    else:
                        pick = f"{dog_team} +{spread_info[-1][1:]}"
                else:
                    pick = None
                    
                # Inserting data into database
                today = date.today()
                win_loss = None

                if pick == None:
                    print(f"NO PICK FOR {matchup}")
                else:
                    print("Matchup:", matchup, info)
                    print(f"{home_team} percent:", home_cover_percent, "GP:", home_games)
                    print(f"{away_team} percent:", away_cover_percent, "GP:", away_games)
                    print("Pick:", pick)

                    if not self.dry_run:
                        cur.execute('''
                            INSERT INTO bets (date, matchup_team1, matchup_team2, spread, home_team, home_cover_percent, away_cover_percent, pick, threshold,  win_loss)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (today, matchup[0], matchup[1], info['spread'], info['home_team'], home_cover_percent, away_cover_percent, pick, threshold, win_loss))
                        conn.commit()

                print()

        else:
            print("---- PICKS FOR ALL GAMES ----")
            
            # cur.execute("drop table if exists bets")
            cur.execute('''
                CREATE TABLE IF NOT EXISTS bets (
                    id INTEGER PRIMARY KEY,
                    date DATE,
                    matchup_team1 TEXT,
                    matchup_team2 TEXT,
                    spread TEXT,
                    total TEXT,
                    home_team TEXT,
                    fav_cover_percent REAL,
                    dog_cover_percent REAL,
                    pick TEXT,
                    threshold REAL,
                    win_loss TEXT
                )
            ''')
            conn.commit()

            for matchup, info in self.matchups.items():

                # Getting cover percentages
                team1, team2 = matchup
                spread_info = info['spread'].rsplit(" ", 1)
                home_team = info['home_team']

                if home_team == spread_info[0]:
                    fav_team, dog_team = home_team, team1 if home_team == team2 else team2
                else:
                    fav_team, dog_team = spread_info[0], team1 if spread_info[0] == team2 else team2

                fav_cover_percent = trends[fav_team]['home_fav_cover_percent'] if home_team == fav_team else trends[fav_team]['away_fav_cover_percent']
                dog_cover_percent = trends[dog_team]['home_dog_cover_percent'] if home_team == dog_team else trends[dog_team]['away_dog_cover_percent']

                # Logic for picks
                threshold = 0.3
                high_limit = 1 - threshold
                low_limit = threshold

                if fav_cover_percent >= high_limit and dog_cover_percent >= high_limit:
                    pick = None
                elif fav_cover_percent <= low_limit and dog_cover_percent <=low_limit:
                    pick = None
                elif fav_cover_percent >= high_limit or dog_cover_percent <= low_limit:
                    pick = info['spread']
                elif fav_cover_percent <= low_limit or dog_cover_percent >= high_limit:
                    pick = f"{dog_team} +{spread_info[-1][1:]}"
                else:
                    pick = None
                    
                # Inserting data into database
                today = date.today()
                win_loss = None

                if pick == None:
                    print(f"NO PICK FOR {matchup}")
                else:
                    print("Matchup:", matchup, info)
                    print(f"{fav_team} percent:", fav_cover_percent)
                    print(f"{dog_team} percent:", dog_cover_percent)
                    print("Pick:", pick)

                    if not self.dry_run:
                        cur.execute('''
                            INSERT INTO bets (date, matchup_team1, matchup_team2, spread, total, home_team, fav_cover_percent, dog_cover_percent, pick, threshold,  win_loss)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (today, matchup[0], matchup[1], info['spread'], info['total'], info['home_team'], fav_cover_percent, dog_cover_percent, pick, threshold, win_loss))
                        conn.commit()

                print()

        # Close the connection
        cur.close()
        cur.close()


    def check_picks(self, recent_games=False):
        # Checking yesterdays picks
        scores = self.nba.get_yesterday_scores()
        v = Vegas()

        if recent_games:
            db = f'{self.cur_dir}/nba_pick_recent_data_2023.db'
        else:
            db = f'{self.cur_dir}/nba_pick_data_2023.db'
        
        yesterdays_record = "DRY RUN"
        if not self.dry_run:
            yesterdays_record = v.check_picks(scores, db)
            print("Yesterday's record:", yesterdays_record)

        # Getting overall record
        conn = sqlite3.connect(db)
        cur = conn.cursor()

        tot_win = cur.execute("select sum(win) from results").fetchone()[0]
        tot_lose = cur.execute("select sum(loss) from results").fetchone()[0]
        tot_push = cur.execute("select sum(push) from results").fetchone()[0]

        overall_record = f"{tot_win}-{tot_lose}-{tot_push}"

        cur.close()
        conn.close()

        return {"yesterdays": yesterdays_record, "overall": overall_record}

