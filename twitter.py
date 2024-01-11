import tweepy
import config
from nba_models import Model
import sqlite3
from datetime import date
import os


class TwitterBot:
    def __init__(self, dry_run=False, vm=False) ->  None:
        self.dry_run = dry_run
        self.vm = vm

        # v1 client
        auth = tweepy.OAuth1UserHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
        auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_TOKEN_SECRET)
        self.api = tweepy.API(auth)


        # # v2 client
        self.client = tweepy.Client(
                consumer_key=config.CONSUMER_KEY,
                consumer_secret=config.CONSUMER_SECRET,
                access_token=config.ACCESS_TOKEN,
                access_token_secret=config.ACCESS_TOKEN_SECRET,
            )
        

    def fetch_nfl_image(self):
        pass

    def fetch_picks(self, db):
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        today = date.today()
        query = f"SELECT * FROM bets WHERE date = '{today}'"
        data = cur.execute(query).fetchall()

        cur.close()
        conn.close()

        return data



    def run_model(self):

        ### CHANGE THIS ARGUMENT FOR DRY RUN
        if self.dry_run:
            if self.vm:
                m = Model(dry_run=True, vm=True)
            else:
                m = Model(dry_run=True)
        else:
            if self.vm:
                m = Model(vm=True)
            else:
                m = Model()

        all_games_results = m.check_picks(recent_games=False)
        recent_games_results = m.check_picks(recent_games=True)

        m.make_picks(recent_games=False)
        m.make_picks(recent_games=True)

        
        ## FETCH PICKS FROM DATABASE
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        all_games_picks = self.fetch_picks(f"{cur_dir}/nba_models/nba_pick_data_2023.db")
        recent_games_picks = self.fetch_picks(f"{cur_dir}/nba_models/nba_pick_recent_data_2023.db")


        tweet_text = f"""Season-long trends:
Yesterday: {all_games_results["yesterdays"]}
Overall: {all_games_results["overall"]}\n"""

        if not all_games_picks:
            tweet_text += "No picks for today\n"
        else:
            for m in all_games_picks:
                tweet_text += f"{m[-3]}\n"

        tweet_text +=  f"""\nLast 7 games trends:
Yesterday: {recent_games_results["yesterdays"]}
Overall: {recent_games_results["overall"]}\n"""

        if not recent_games_picks:
            tweet_text += "No picks for today\n"
        else:
            for m in recent_games_picks:
                tweet_text += f"{m[-3]}\n"

        print(len(tweet_text))
        print(tweet_text)

        return tweet_text

    
    def post_tweet(self):
        text = self.run_model()
        
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        media = self.api.simple_upload(f"{cur_dir}/mcnulty wife.webp")
        self.client.create_tweet(text=text, media_ids=[media.media_id])
