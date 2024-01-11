from twitter import TwitterBot
from datetime import datetime


if __name__ == "__main__":
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"CURRENT TIME {current_datetime}")

    TwitterBot(dry_run=False, vm=True).post_tweet()
