from typing import Union
from bs4 import BeautifulSoup
from dateutil.parser import parse
from .extractor import extract_ids, Parser

import time
import requests
import re


class Scraper:
    """
    This class handles requests and information extraction
    """
    def __init__(self):
        self.base = "https://www.hltv.org/"
        self.ranks = "https://www.hltv.org/ranking/teams/"
        self.results = "https://www.hltv.org/results?team="
        self.matches = "https://www.hltv.org/results?"

    def get_event_info(self):
        pass

    def get_team_info(self):
        pass

    def get_player_info(self):
        pass

    def get_teamids(self) -> list[str]:
        """
        Obtains the top 30 current team ids from HLTV
        :return: list with top 30 team ids
        :rtype: list
        """
        try:
            html = requests.get(self.ranks)
            html.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("An exception was raised:", e)
            raise e

        soup = BeautifulSoup(html.text, "html.parser")

        # Find team links
        teamlinks = soup.find_all('a', class_="moreLink", text="HLTV Team profile")
        links = [x.get('href') for x in teamlinks]

        # Extract id's from link
        team_ids = extract_ids("".join(links))

        return team_ids

    def get_last_matches(self, limit: int = 100) -> list[tuple]:
        """
        Returns all the last limit specified matches posted on hltv
        :param limit: limits the number of retrieved matches, defaults to 100 to prevent extracting all hltv records
        :type limit: int
        :return: list of tuples with format (matchID, matchlink)
        :rtype: List[tuple(int, str)]
        """
        try:
            session = requests.Session()
            html = session.get(self.matches)
            html.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print("An exception was raised:", e)
            raise e

        soup = BeautifulSoup(html.text, "html.parser")

        # Obtain match links and max number of matches for limit purpouses
        matches = [Parser.parse_match_links(match) for match in soup.find_all("div", class_="result-con")]
        max_matches = int(soup.find("span", class_="pagination-data").text.split()[-1])

        offset = 0
        while max_matches > 100:
            # Create request with offset
            offset += 100
            offset_url = self.matches + "?offset=" + str(offset)

            # If limit is requested, offset should not be more than limit
            if offset >= limit:
                break

            # Make request
            try:
                html = session.get(offset_url)
                html.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print("An exception was raised:", e)
                raise e

            # Parse and add matches to match list
            soup = BeautifulSoup(html.text, "html.parser")
            for match in soup.find_all("div", class_="result-con"):
                matches.append(Parser.parse_match_links(match))

            # Progress to base case, page has less than 100 matches which means all match links were scraped
            max_matches -= 100

        # Prune the list to return only the amount of matches requested
        try:
            return matches[:limit]

        except IndexError:
            raise IndexError

    def get_matches_teamid(self, teamid: Union[str, int], limit: int = 100) -> list[tuple]:
        """
        Obtains all the matches for a specified team
        :param teamid: str with team id numbers
        :type teamid: str
        :param limit: specifies how many matches to return
        :type limit: int
        :return: list with all the links to historical matches results
        :rtype: List[tuple(id, link)]
        """
        if isinstance(teamid, int):
            link = self.results + str(teamid)
        elif isinstance(teamid, str):
            link = self.results + teamid
        else:
            raise TypeError("Invalid teamid type for get_matches_teamid, only str or int are allowed")

        # Get team historical matches results
        try:
            session = requests.Session()
            html = session.get(link)
            html.raise_for_status()

        except requests.exceptions.HTTPError as e:
            print("An exception was raised:", e)
            raise e

        soup = BeautifulSoup(html.text, "html.parser")
        # Obtain all competitive matches number for offset
        matches_number = int(soup.find("span", class_="pagination-data").text.split()[-1])

        # Obtain all matches links to scrape match data
        matches = [Parser.parse_match_links(match) for match in soup.find_all("div", class_="result-con")]

        # If team has more matches than the max shown in the page, loop to get the rest
        offset = 0
        while matches_number > 100:
            # Create request with offset
            offset += 100
            offset_url = link + "&offset=" + str(offset)

            # If limit is requested, offset should not be more than limit
            if limit and isinstance(limit, int) and offset >= limit:
                break

            # Make request
            start = time.time()
            try:
                html = session.get(offset_url)
                html.raise_for_status()

            except requests.exceptions.HTTPError as e:
                print("An exception was raised:", e)
                raise e

            # Parse and add matches to match list
            soup = BeautifulSoup(html.text, "html.parser")
            for match in soup.find_all("div", class_="result-con"):
                matches.append(Parser.parse_match_links(match))

            # Progress to base case, page has less than 100 matches which means all match links were scraped
            matches_number -= 100

        # If a limit is requested, return only the specified amount of matches
        if limit and isinstance(limit, int):
            try:
                matches = matches[:limit]
            # If team has fewer matches than limit, IndexError is raised, in this case, just return matches
            except IndexError:
                return matches

        return matches

    def extract_match_info(self, match_id: tuple, session: requests.Session = False) -> dict:
        """
        Extracts all relevant match information and puts it into a dictionary for further use
        :param match_id: tuple with (match id number, match link)
        :type match_id: tuple
        :param session: requests session object to leverage one connection across requests
        :type session: requests.Session
        :return: dictionary with match information
        :rtype: dict
        """
        # Get match link
        link = self.base + match_id[1]

        # Make html request
        try:
            if session:
                html = session.get(link)
                html.raise_for_status()
            else:
                html = requests.get(link)
                html.raise_for_status()

        except Exception as e:
            print(e)
            raise e

        soup = BeautifulSoup(html.text, "html.parser")

        # Find both divs containing team info (id, name, result)
        match_team_results_info = soup.find_all("div", class_=re.compile(r"team[0-9]+-gradient"))

        # Containers for team info
        team1_info = Parser.parse_team_info(match_team_results_info[0])
        team2_info = Parser.parse_team_info(match_team_results_info[1])

        # Find div containing match date, time and event link
        div = match_date_event_info = soup.find("div", class_="timeAndEvent")
        date_div = div.find("div", class_="date")
        time_div = div.find("div", class_="time")
        event_div = div.find("div", class_="event")

        # Obtain event information
        event = event_div.a["href"].split('/')[-2:]
        event_info = {"id": event[0],
                      "name": event[1],
                      "link": event_div.a["href"]}

        # Obtain match datetime
        dt = parse(date_div.text + " " + time_div.text)

        # Find div containing match info (bans, picks, results, type: bo?, instance)
        div = match_info = soup.find("div", class_="g-grid maps").div
        match_info = Parser.parse_match_info(div)
        match_info["date"] = str(dt)
        match_info["match_id"] = int(match_id[0])
        match_info["event_id"] = int(event_info["id"])

        # Find divs containing match results info
        divs = soup.find_all("div", class_="mapholder")
        results_info = Parser.parse_results_info(divs)

        # Find div with player stats info, first div contains global stats, the next ones have the map stats in order
        divs = soup.find_all("div", class_="stats-content")

        # If divs result set is empty, match was forfeit and no map was played
        if list(divs):
            # Create container dict for player stats
            map_names = list(results_info.keys())
            team1, team2 = Parser.parse_player_stats(divs[0])
            player_stats = {"global_stats": {"first_team": team1,
                                             "second_team": team2}}
            counter = 0
            for div in divs[1:]:
                # Each table has data for first team global, ct, t stats, then next team, 6 teams per div
                if map_names[counter] == "Default":
                    counter += 1
                    pass
                else:
                    team1, team2 = Parser.parse_player_stats(div)
                    player_stats[map_names[counter]] = {"first_team": team1,
                                                        "second_team": team2}
                    counter += 1
        else:
            player_stats = None

        final_dict = {
            "team1": team1_info,
            "team2": team2_info,
            "event": event_info,
            "match_info": match_info,
            "map_results": results_info,
            "player_stats": player_stats
        }

        return final_dict
