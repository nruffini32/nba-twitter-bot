# NBA Picks Twitter Bot

## Overview

This repository contains the code for a Twitter bot that is tweeting daily NBA picks against the spread.

Twitter account <a href="https://twitter.com/ShitterNBAPicks">here</a>

###### Disclaimer: This was made for educational purposes only and should not be considered financial or betting advice.

## High Level Overview
Every day the script is doing the following:
1. Checking yesterday's picks and storing results in database
2. Making picks for tonight's games and storing in database
3. Tweeting out picks, yesterday's record, and total record

### Pick Algorithm
I did not spend a lot of time developing an algorithm as the purpose of this project was to mess around with deploying a twitter bot.

For each matchup the script is doing the following
1. Group the two teams into one of the following categories: home dog / home favorite / away dog / away favorite
2. Check the percentage of times each team has covered in their given category on that night
3. If a team have covered more than 75% of the time or did not cover less than 25% of the time, the algorithm with tail or fade that team, respectively
4. If the two teams have contradicting decisions (We want to tail both teams / fade both teams) then no pick will be given for that matchup

## Technologies
- Data is being stored in a sqlite database in the VM
- Script is being scheduled with a cronjob on a Google Cloud VM
- Log files are stored in the filesystem of the VM
- Data is being scraper from <a href="https://www.basketball-reference.com/">www.basketball-reference.com</a>

## Modules
There are two main modules that are being utilized

[nba_models.nba_scraper.scraper.NBAScraper](nba_models/nba_scraper/scraper.py) - This is an interface that is being used to scrape data from basketball-reference.com

[nba_models.vegas.vegas.Vegas](nba_models/vegas/vegas.py) - Interface used to check picks.

[nba_models.get_picks.Model](nba_models/get_picks.py.) - Model class that contains logic to make the picks.

## Acknowledgements

Special thanks to basketball-reference.com for designing a scrape friendly site

Also to [Tweepy](https://github.com/tweepy/tweepy) - For Twitter API integration.
