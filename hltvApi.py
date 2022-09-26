from abc import abstractmethod
from scraper import scraper
from collections import deque
from typing import Union

import requests
import pandas as pd
import time
import pickle


class HltvApi(scraper.Scraper):
    """
    Main interface to request HLTV data for many matches. Individual statistics can be obtained through the Scraper
    subclass. Most work is delegated to the subclass while looping, data transformation and  loading to other sources
    will be done in this class
    """

    def __init__(self):
        super().__init__()
        self.counter = 0

        # Normalized fact tables column names
        self.match_cols = ["matchid", "bestof", "instance", "eventid", "lan", "date", "team1id", "team2id", "winnerid"]
        self.map_cols = ["mapid", "matchid", "teamid", "map", "score", "enemy_score", "ct_result", "t_result",
                         "overtime", "won", "pick"],
        self.player_cols = ["mapId", "teamid", "matchId", "playerid", "map", "ct_kills", "ct_deaths", "ct_adr",
                            "t_kills", "t_deaths", "t_adr"]

        # Denormalized DataFrame column names
        self.df_match_cols = ["match_id", "date", "t1_id", "t1_name", "t2_id", "t2_name", "t1_score", "t2_score",
                              "winner", "event_id", "event_name", "instance", "best_of", "lan"]
        self.df_map_cols = ["mapId", "matchId", "t1_id", "t1_name", "t2_id", "t2_name", "map", "t1_result", "t2_result",
                            "t1_ct_score", "t1_t_score", "t2_ct_score", "t2_t_score", "winner", "overtime", "picked_by"]

    def match_dataframe(self, mdict: Union[dict, list[dict]]) -> pd.DataFrame:
        """
        Receives a dict or a list of dictionaries obtained with extract_match_info method and extracts all relevant
        match data into a single denormalized DataFrame. Differs from process_match because this method includes
        redundant information in the DataFrame for readability.
        :param mdict: match dictionaries returned by request_match_info method
        :type mdict: dict, list[dict]
        :return: DataFrame with self.match_df columns
        :rtype: pd.DataFrame
        """
        container = []

        def process_dict(mdict: dict) -> list:
            """
            This nested function contains the code used to process match information for each dictionary
            """
            l = []
            match = mdict["match_info"]
            l.append(match["match_id"])
            l.append(match["date"])
            l.append(mdict["team1"]["id"])
            l.append(mdict["team1"]["name"])
            l.append(mdict["team2"]["id"])
            l.append(mdict["team2"]["name"])
            l.append(mdict["team1"]["result"])
            l.append(mdict["team2"]["result"])
            l.append(mdict["team1"]["name"] if mdict["team1"]["won"] is True else mdict["team2"]["name"])
            l.append(match["event_id"])
            l.append(mdict["event"]["name"])
            l.append(match["instance"])
            l.append(match["bestof"])
            l.append(1 if match["lan"] is True else 0)

            return l

        if isinstance(mdict, list):
            for m in mdict:
                container.append(process_dict(m))

        elif isinstance(mdict, dict):
            container.append(process_dict(mdict))

        return pd.DataFrame(container, columns=self.df_match_cols)

    def maps_dataframe(self, mdict: Union[dict, list[dict]]) -> pd.DataFrame:
        """
        Receives a dict or a list of dictionaries obtained with extract_match_info method and extracts all relevant
        mp results data into a single denormalized DataFrame. Differs from process_results because this method includes
        redundant information in the DataFrame for readability.
        :param mdict: match dictionaries returned by request_match_info method
        :type mdict: dict, list[dict]
        :return: DataFrame with self.match_df columns
        :rtype: pd.DataFrame
        """
        container = []

        def process_dict(mdict: dict, cont: list) -> None:
            """
            This nested function contains the code used to process map information for each dictionary
            """
            for key, dct in mdict["map_results"].items():
                # If a map wasn't played because a team won before, there is a null dictionary
                if dct is None or key == "Default":
                    continue

                else:
                    cont.append([
                        dct["mapID"],
                        mdict["match_info"]["match_id"],
                        mdict["team1"]["id"],
                        mdict["team1"]["name"],
                        mdict["team2"]["id"],
                        mdict["team2"]["name"],
                        key,
                        dct["first_team"]["score"],
                        dct["second_team"]["score"],
                        dct["first_team"]["round_results"][0][1],
                        dct["first_team"]["round_results"][1][1],
                        dct["second_team"]["round_results"][0][1],
                        dct["second_team"]["round_results"][1][1],
                        mdict["team1"]["name"] if dct["first_team"]["won"] is True else mdict["team2"]["name"],
                        dct["overtime"],
                        1 if dct["first_team"]["pick"] is True else 2
                    ])

        if isinstance(mdict, list):
            for m in mdict:
                process_dict(m, container)

        elif isinstance(mdict, dict):
            process_dict(mdict, container)
            print(container)

        return pd.DataFrame(container, columns=self.df_map_cols)

    def players_dataframe(self, mdict: Union[dict, list[dict]]) -> pd.DataFrame:
        """
        Receives a dict or a list of dictionaries obtained with extract_match_info method and extracts all relevant
        player score statistics data into a single denormalized DataFrame. Differs from process_results because this
        method includes redundant information in the DataFrame for readability.
        :param mdict: match dictionaries returned by request_match_info method
        :type mdict: dict, list[dict]
        :return: DataFrame with self.match_df columns
        :rtype: pd.DataFrame
        """
        # Implementation pending
        ...

    @abstractmethod
    def process_match(self, mdict: dict) -> list:
        """
        Takes a dictionary with match information and parses it to normalize data for a match Fact Table row
        :param mdict: match dictionary returned by request_match_info method
        :type mdict: dict
        :return: list with data extracted from the dictionary
        :rtype: list
        """
        container = []
        match = mdict["match_info"]
        container.append(match["match_id"])
        container.append(match["bestof"])
        container.append(match["instance"])
        container.append(match["event_id"])
        container.append((1 if match["lan"] is True else 0))
        container.append(pd.to_datetime(match["date"]))
        container.append(mdict["team1"]["id"])
        container.append(mdict["team2"]["id"]),
        container.append((mdict["team1"]["id"] if mdict["team1"]["won"] is True else mdict["team2"]["id"]))

        return container

    @abstractmethod
    def process_results(self, mdict: dict) -> list:
        """
        Takes a dictionary with match information and parses it to normalize data for a map table row
        :param mdict: match dictionary returned by request_match_info method
        :type mdict: dict
        :return: list with data extracted from the dictionary
        :rtype: list
        """
        container = []

        for key, dct in mdict["map_results"].items():
            # If a map wasn't played because a team won before, there is a null dictionary
            if dct is None or key == "Default":
                continue

            else:
                # Make map entry for team 1
                container.append(
                    [
                        dct["mapID"],
                        mdict["match_info"]["match_id"],
                        mdict["team1"]["id"],
                        key,
                        dct["first_team"]["score"],
                        dct["second_team"]["score"],
                        dct["first_team"]["round_results"][0][1],  # ct round score
                        dct["first_team"]["round_results"][1][1],  # t round score
                        dct["overtime"],
                        dct["first_team"]["won"],
                        dct["first_team"]["pick"]
                    ]
                )
                # Make map entry for team 2
                container.append(
                    [
                        dct["mapID"],
                        mdict["match_info"]["match_id"],
                        mdict["team2"]["id"],
                        key,
                        dct["second_team"]["score"],
                        dct["first_team"]["score"],
                        dct["second_team"]["round_results"][0][1],
                        dct["second_team"]["round_results"][1][1],
                        dct["overtime"],
                        dct["second_team"]["won"],
                        dct["second_team"]["pick"],

                    ]
                )

            return container

    @abstractmethod
    def process_players(self, mdict: dict, player_container: dict = None) -> list:
        """
        Takes a dictionary with match information and parses it to normalize data for a player stats table row
        :param mdict: match dictionary returned by request_match_info method
        :type mdict: dict
        :param player_container: container for all player dim information 
        :type player_container: dict
        :return: list with data extracted from the dictionary
        :rtype: list
        """
        # Player stats can be null if match was forfeit and no map was played
        if mdict["player_stats"] is not None:
            container = []
            # Extract and prepare player stats info
            for key, dct in mdict["player_stats"].items():
                # Global stats contain player dimension table data (id, nick, name, nationality)
                if key == "global_stats" and isinstance(player_container, dict):
                    for team in mdict["player_stats"]["global_stats"].values():
                        for player in team.keys():
                            # Verify player is not stored in player dimension already
                            if team[player]["playerID"] not in player_container:
                                # Add player row to player dimension
                                player_container[team[player]["playerID"]] = [
                                    team[player]["playerName"],
                                    player,
                                    team[player]["nationality"]
                                ]
                # The rest contain player game statistics (kills, deaths, damage)
                elif key != "global_stats":
                    for player, stats in dct["first_team"].items():
                        container.append(
                            [mdict["map_results"][key]["mapID"],
                             mdict["team1"]["id"],
                             mdict["match_info"]["match_id"],
                             stats["playerID"],
                             key,
                             int(stats["ct"]["kd"].split("-")[0]),
                             int(stats["ct"]["kd"].split("-")[1]),
                             stats["ct"]["adr"],
                             int(stats["t"]["kd"].split("-")[0]),
                             int(stats["t"]["kd"].split("-")[1]),
                             stats["t"]["adr"],
                             ]
                        )
                    for player, stats in dct["second_team"].items():
                        container.append(
                            [mdict["map_results"][key]["mapID"],
                             mdict["team2"]["id"],
                             mdict["match_info"]["match_id"],
                             stats["playerID"],
                             key,
                             int(stats["ct"]["kd"].split("-")[0]),
                             int(stats["ct"]["kd"].split("-")[1]),
                             stats["ct"]["adr"],
                             int(stats["t"]["kd"].split("-")[0]),
                             int(stats["t"]["kd"].split("-")[1]),
                             stats["t"]["adr"],
                             ]
                        )
            return container
        else:
            pass

    def start_matches_queue(self, matches: Union[list[tuple], deque]) -> list[pd.DataFrame]:
        """
        This method starts a deque object with a list or receives one that contains tuples (matchid, matchlink) and
        iterates over them to return matches, maps, players, teams and events information in a list of normalized
        dataframes ready for insertion into the Data Warehouse.
        :param matches: matches container with tuples in format (teamid, matchlink)
        :type matches: list, deque
        :return: list of DataFrames with match, map, player, team and event information
        :rtype: list of DataFrames
        """
        # Create matches container
        if isinstance(matches, list):
            match_container = deque(matches)
        elif isinstance(matches, deque):
            match_container = matches
        else:
            raise TypeError("Please provide a valid match list to iterate over")

        # Start containers for data, dicts for players, team and event data to eval if an element is in the dict faster
        failed_extractions = deque()
        player_dim_rows = {}
        team_rows = {}
        event_rows = {}
        match_rows = []
        map_rows = []
        player_rows = []

        # Counter to prevent too many api requests and aggregate time taken
        sleeping_time = 1
        agg = 0

        # Create requests session
        session = requests.Session()

        # Loop over matches
        while len(match_container) > 0:
            # Limit to 15 requests and 15 seconds sleep
            if (sleeping_time % 15) == 0:
                time.sleep(15)

            # Mechanism to interrupt the loop
            if self.counter >= 500:
                with open("pending_matches", "wb") as file:
                    pickle.dump(match_container, file)
                with open("failed_matches", "wb") as file:
                    pickle.dump(failed_extractions, file)

                break

            # Extract and request match data while measuring time taken
            current = match_container.pop()
            print("PROCESSING MAP: ", current)
            start = time.time()

            try:
                match = self.request_match_info(current, session)

                # Process team data into container
                if match["team1"]["id"] not in team_rows:
                    team_rows[match["team1"]["id"]] = match["team1"]["name"]
                if match["team2"]["id"] not in team_rows:
                    team_rows[match["team2"]["id"]] = match["team2"]["name"]

                # Process event data into container
                if match["event"]["id"] not in event_rows:
                    event_rows[match["event"]["id"]] = match["event"]["name"]

                # Append match, map and player stats rows to containers
                match_rows.append(self.process_match(match))

                # Map results can be null if match was forfeit and no map was played
                map_results = self.process_results(match)
                if map_results:
                    for x in map_results:
                        map_rows.append(x)

                # Player stats can also be null if match was forfeit and no map was played
                player_results = self.process_players(match, player_dim_rows)
                if player_results:
                    for x in player_results:
                        player_rows.append(x)

                # Once finished processing match info, continue looping
                sleeping_time += 1
                finish = time.time() - start
                agg += finish
                self.counter += 1
                print("PROCCESING TIME: ", finish)
                print("---" * 10)

            except Exception as e:
                # If an exception was raised, add match to failed extractions
                failed_extractions.append(current)
                print("*" * 10)
                print("An exception was raised on: ", current)
                print(e)
                print("*" * 10)

                continue

        # Return data
        playerstats_df = pd.DataFrame(player_rows, columns=self.player_cols)
        maps_df = pd.DataFrame(map_rows, columns=self.map_cols)
        match_df = pd.DataFrame(match_rows, columns=self.match_cols)

        return [
            pd.DataFrame.from_dict(team_rows, orient="index", columns=['teamName']),
            pd.DataFrame.from_dict(event_rows, orient="index", columns=['eventName']),
            pd.DataFrame.from_dict(player_dim_rows, orient="index", columns=['playerName', 'playerNick',
                                                                             'nationality']),
            match_df,
            maps_df,
            playerstats_df
        ]
