from abc import abstractmethod
from scraper import scraper
from collections import deque
from typing import Union

import requests
import constants
import pandas as pd
import time


class HltvApi(scraper.Scraper):
    """
    Main interface to request HLTV data for many matches. Individual statistics can be obtained through the Scraper
    subclass. Most work is delegated to the subclass while looping and data loading to other sources will be done
    in this class
    """

    def __init__(self):
        super().__init__()

    @abstractmethod
    def process_match(self, mdict: dict) -> list:
        """
        Takes a dictionary with match information and parses it to normalize data for a match table row
        :param mdict: dictionary returned by extract_match_info method
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
        container.append((mdict["team1"]["id"] if mdict["team1"]
                          ["won"] is True else mdict["team2"]["id"]))

        return container

    @abstractmethod
    def process_results(self, mdict: dict) -> list:
        """
        Takes a dictionary with match information and parses it to normalize data for a map table row
        :param mdict: dictionary returned by extract_match_info method
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
                        dct["first_team"]["round_results"][0][1],
                        dct["first_team"]["round_results"][1][1],
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
    def process_players(self, mdict: dict, player_container: dict) -> list:
        """
        Takes a dictionary with match information and parses it to normalize data for a player stats table row
        :param mdict: dictionary returned by extract_match_info method
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
                # Avoid global stats and get only map specific stats
                if key == "global_stats":
                    for team in mdict["player_stats"]["global_stats"].values():
                        for player in team.keys():
                            if team[player]["playerID"] not in player_container:
                                player_container[team[player]["playerID"]] = {
                                    "playerName": team[player]["playerName"],
                                    "nationality": team[player]["nationality"]
                                }

                else:
                    for player, stats in dct["first_team"].items():
                        container.append(
                            [mdict["map_results"][key]["mapID"],
                             mdict["match_info"]["match_id"],
                             stats["playerID"],
                             mdict["team1"]["id"],
                             key,
                             stats["ct"]["kd"].split("-")[0],
                             stats["ct"]["kd"].split("-")[1],
                             stats["ct"]["adr"],
                             stats["t"]["kd"].split("-")[0],
                             stats["t"]["kd"].split("-")[1],
                             stats["t"]["adr"],
                             ]
                        )
                    for player, stats in dct["second_team"].items():
                        container.append(
                            [mdict["map_results"][key]["mapID"],
                             mdict["match_info"]["match_id"],
                             stats["playerID"],
                             mdict["team2"]["id"],
                             key,
                             stats["ct"]["kd"].split("-")[0],
                             stats["ct"]["kd"].split("-")[1],
                             stats["ct"]["adr"],
                             stats["t"]["kd"].split("-")[0],
                             stats["t"]["kd"].split("-")[1],
                             stats["t"]["adr"],
                             ]
                        )
            return container
        else:
            pass

    def start_matches_queue(self, matches: Union[list[tuple], deque]) -> list[pd.DataFrame]:
        """
        This method starts a deque object with a list or receives one that contains tuples (matchid, matchlink) and
        iterates over them to return matches, maps, players, teams and events information in a list of dataframes
        in the order they are mentioned. For specific statistics, call methods player_queue, map_queue, match_queue, 
        get_event_info or get_team_info
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
        sleeping_time = 0
        agg = 0

        # Create requests session
        session = requests.Session()

        # Loop over matches
        while len(match_container) > 0:
            # Limit to 15 requests and 15 seconds sleep
            if (sleeping_time % 15) == 0:
                time.sleep(15)

            # Extract and request match data while measuring time taken
            current = match_container.pop()
            print("PROCESSING MAP: ", current)
            start = time.time()

            try:
                match = self.extract_match_info(current, session)

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
        playerstats_df = pd.DataFrame(player_rows, columns=constants.columns["player_rows"])
        maps_df = pd.DataFrame(map_rows, columns=constants.columns["map_rows"])
        match_df = pd.DataFrame(match_rows, columns=constants.columns["match_rows"])

        return [playerstats_df, maps_df, match_df, event_rows, team_rows, player_dim_rows]
