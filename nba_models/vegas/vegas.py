import os
import pandas as pd
from datetime import date, timedelta
import sqlite3

class Vegas:
    def __init__(self, dry_run=False) -> None:
        self.dry_run=dry_run
        

    def check_picks(self, scores, db):
        print(f"Checking picks from yesterday for {db}..")

        # Connect to SQLite database
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        yesterday = date.today() - timedelta(days=1)
        query = f"SELECT * FROM bets WHERE date = '{yesterday}'"
        df = pd.read_sql_query(query, conn)
        
        if len(df) == 0:
            print(f"No picks for {yesterday}")
            return "No picks"
        
        win_cnt = 0
        lose_cnt = 0
        push_cnt = 0
        for index, row in df.iterrows():
            team1 = row["matchup_team1"]
            team2 = row["matchup_team2"]
            key = (team1, team2)

            # Get the actual scores from the 'scores' dictionary

            # try and except for is if game got cancelled/didn't happen for some reason
            try:
                game_result = scores[key]
            except:
                print(f"{row['pick']} - GAME DIDN'T HAPPEN")
                query = f"""
                    UPDATE bets
                    SET win_loss = ?
                    WHERE date = ? AND matchup_team1 = ? AND matchup_team2 = ?
                """
                cur.execute(query, ("N/A", yesterday, team1, team2))
                conn.commit()
                push_cnt += 1
                continue


            actual_score1 = game_result[team1]
            actual_score2 = game_result[team2]

            # Before doing stuff with pick, check if we didn't have a pick
            pick = row['pick']

            # Extract team and spread from pick column
            picked_team = pick.rsplit(' ', 1)[0]
            other_team = team2 if team1 == picked_team else team1
            spread = float(pick.rsplit(' ', 1)[-1])

            game_result[picked_team] += spread

            # pick logic
            if game_result[picked_team] > game_result[other_team]:
                result = "W"
                win_cnt += 1
            elif game_result[picked_team] < game_result[other_team]:
                result = "L"
                lose_cnt += 1
            else:
                result = "Push"
                push_cnt += 1

            print(f"{pick} - {result}")

            query = f"""
                UPDATE bets
                SET win_loss = ?
                WHERE date = ? AND matchup_team1 = ? AND matchup_team2 = ?
            """
            cur.execute(query, (result, yesterday, team1, team2))
            conn.commit()


        # Updating record
        # Create a new table called 'results'
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS results (
            date DATE,
            win INTEGER,
            loss INTEGER,
            push INTEGER
        );
        '''
        cur.execute(create_table_query)
        conn.commit()

        # Insert data using variables into the 'results' table
        if not self.dry_run:

            cur.execute("select max(date) from results")
            max_date = cur.fetchone()[0]

            # Only inserting if results doesn't exists in table
            if str(yesterday) != str(max_date):
                insert_data_query = '''
                INSERT INTO results (date, win, loss, push)
                VALUES (?, ?, ?, ?);
                '''
                cur.execute(insert_data_query, (yesterday, win_cnt, lose_cnt, push_cnt))
                conn.commit()

        cur.close()
        conn.close()

        return f"{win_cnt}-{lose_cnt}-{push_cnt}"

