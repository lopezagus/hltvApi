from typing import List
from bs4 import Tag
from bs4.element import ResultSet

import re


def extract_ids(text: str) -> List[str]:
    """
    Extracts the id's from a link supposing it's all numeric
    :param text: link containing id information
    :type text: str
    :return: list where each string is an id
    :rtype: list
    """
    numbers = text.split("/")
    ids = []
    for x in numbers:
        if x.isnumeric():
            ids.append(x)
        else:
            pass
    return ids


class Parser:
    def parse_match_links(self: Tag) -> tuple:
        # Link info is contained inside the <a> tag of the div tag
        links = self.a.get("href")
        ids = int(extract_ids(links).pop())
        match = (ids, links)
        return match

    def parse_team_info(self: Tag) -> dict:
        team_link = self.a['href']
        team_id = extract_ids(team_link)
        team_name = self.a.div.text
        result = self.a.find_next_sibling()
        team_result = result.text

        return {"id": int(team_id[0]),
                "name": team_name,
                "result": int(team_result),
                "won": (True if result["class"][0] == "won" else False)}

    def parse_match_info(self: Tag) -> dict:
        """
        Receives a bs4 tag object with match properties and returns a dict with relevant information
        :return: dict with relevant match properties ["bestof", "instance", "lan", "banphase"]
        :rtype: dict
        """

        def parse_picks(html: str) -> tuple:
            """
            Parses html to find the pick/ban phase information
            :return: a tuple indicating (team, pick/ban/decider, map)
            :rtype: tuple
            """
            # Split text into different strings to parse information
            # Map is always last, team is second, after event number and before picked/removed keyword
            splits = html.split()
            # Map was removed
            if "removed" in splits:
                maps = splits[-1]
                team = " ".join(splits[1:-2])
                data = (team, "ban", maps)
                # Add removed map to match properties
                if "removed" in match_properties:
                    match_properties['removed'].append(maps)
                else:
                    match_properties['removed'] = [maps]
                return data
            # Map was picked
            elif "picked" in splits:
                maps = splits[-1]
                team = " ".join(splits[1:-2])
                data = (team, "pick", maps)
                # Add picked map to match properties
                if "maps" in match_properties:
                    match_properties['maps'].append(maps)
                else:
                    match_properties['maps'] = [maps]
                return data
            # Map was left over as decider
            else:
                maps = splits[1]
                data = (None, "decider", maps)
                match_properties['decider'] = maps
                return data

        # First preformatted-text div has match type (bo?) and instance after "*" character
        text = self.find("div", class_="preformatted-text").text.split("*")
        # Extract info from div
        instance = text[1][1:].rstrip()
        lan = (True if "LAN" in text[0] else False)
        bestof = re.findall(r"\d", text[0])[0]

        match_properties = {"bestof": int(bestof),
                            "instance": instance,
                            "lan": lan,
                            "banphase": []}

        # Bans and picks are inside the first .div children of the second veto-box div. Each child contains a pick/ban
        try:
            divs = self.find_all(
                "div", class_="veto-box")[1].div.find_all("div")
            for div in divs:
                match_properties["banphase"].append(parse_picks(div.text))
        except IndexError:
            match_properties["status"] = "Match was forfeit"
            return match_properties

        return match_properties

    def parse_results_info(self: ResultSet) -> dict:
        map_stats = {}
        for mapholder in self:
            # Get map name from div
            map_name = mapholder.find("div", class_="mapname").text

            # Handle abnormal cases where map was not played:
            # If first div has class optional, the decider map was not played
            if "optional" in mapholder.div["class"]:
                break
            # If map name has default, map was forfeit
            elif "Default" == map_name:
                result_left = mapholder.find(class_="results-left")
                result_right = mapholder.find(class_="results-right")
                map_stats["Default"] = {
                    "first_team": {"team": result_left.find("div", class_="results-teamname").text,
                                   "won": (True if "won" in result_left["class"] else False)
                                   },
                    "second_team": {"team": result_right.find("div", class_="results-teamname").text,
                                    "won": (True if "won" in result_right["class"] else False)}
                }
                continue
            # If map name is TBA, match was forfeit, no info to add
            elif "TBA" == map_name:
                break

            # Extract left team stats, if result side has a class "tie" in it, map was not played and canceled
            result_left = mapholder.find(class_="results-left")
            if "tie" in result_left["class"]:
                print("A TIE WAS FOUND")
                continue

            first_team = {"team": result_left.find("div", class_="results-teamname").text,
                          "score": result_left.find(class_="results-team-score").text,
                          "won": (True if "won" in result_left["class"] else False),
                          "pick": (True if "pick" in result_left["class"] else False),
                          "round_results": []
                          }
            # Extract right team stats
            result_right = mapholder.find(class_="results-right")
            second_team = {"team": result_right.find("div", class_="results-teamname").text,
                           "score": result_right.find(class_="results-team-score").text,
                           "won": (True if "won" in result_right["class"] else False),
                           "pick": (True if "pick" in result_right["class"] else False),
                           "round_results": []
                           }

            # Detailed match side info, score is span text and side is the class
            side_info = mapholder.find(
                "div", class_="results-center-half-score")
            counter = 0
            for span in side_info:
                # The div contains many spans, these are the ones with scores on left side
                if counter in (1, 5):
                    score = (span["class"][0], int(span.text))
                    first_team["round_results"].append(score)
                # These contain scores on the right side
                elif counter in (3, 7):
                    score = (span["class"][0], int(span.text))
                    second_team["round_results"].append(score)
                # If counter reached this stage, we had overtime, first is left side, second right
                elif counter == 11:
                    score = ("overtime", int(span.text))
                    first_team["overtime"] = True
                    first_team["round_results"].append(score)
                elif counter == 13:
                    score = ("overtime", int(span.text))
                    second_team["overtime"] = True
                    second_team["round_results"].append(score)
                counter += 1

            # Add info to the stats dictionary
            map_stats[map_name] = {"mapID": int(extract_ids(mapholder.find("a", class_="results-stats")["href"])[0]),
                                   "first_team": first_team,
                                   "second_team": second_team,
                                   "global_score": (first_team["score"], second_team["score"]),
                                   "overtime": (True if counter > 11 else False)}
        return map_stats

    def parse_player_stats(self: Tag) -> tuple:
        """
        Receives a div class stats-content with child tables containing player stats information. First div is always the
        global player stats for all maps and has id = 'all-content', next ones are map specific with id = ('id'-content)
        """
        # First three tables are global, ct and t data from first_team, next three are for the second team
        tables = self.find_all("table")

        # Create container dict for player stats
        team1_dict = {}
        team2_dict = {}

        # Find first team player info
        # Global (terrorist + counter-terrorist side) stats
        for x in tables[0].find_all("tr", class_=""):
            nick = x.find("span", class_="player-nick").text
            team1_dict[nick] = {
                "playerID": int(extract_ids(x.find("a", class_="flagAlign")["href"])[0]),
                "global": {"kd": x.find("td", class_="kd").text,
                           "adr": float(x.find("td", class_="adr").text)}
            }
            # Append player props only to global (all-maps) stats to avoid redundancy (global stats has id all-content)
            if self["id"] == "all-content":
                team1_dict[nick]["playerName"] = x.find(
                    "div", class_="statsPlayerName").text
                team1_dict[nick]["nationality"] = x.find("img")["title"]

        # Counterterrorist first team stats
        for x in tables[1].find_all("tr", class_=""):
            team1_dict[x.find("span", class_="player-nick").text]["ct"] = {
                "kd": x.find("td", class_="kd").text,
                "adr": float(x.find("td", class_="adr").text)
            }

        # Terrorist first team stats
        for x in tables[2].find_all("tr", class_=""):
            team1_dict[x.find("span", class_="player-nick").text]["t"] = {
                "kd": x.find("td", class_="kd").text,
                "adr": float(x.find("td", class_="adr").text)
            }

        # Find second team player info
        # Global (terrorist + counter-terrorist side) stats
        for x in tables[3].find_all("tr", class_=""):
            nick = x.find("span", class_="player-nick").text
            team2_dict[nick] = {
                "playerID": int(extract_ids(x.find("a", class_="flagAlign")["href"])[0]),
                "global": {"kd": x.find("td", class_="kd").text,
                           "adr": float(x.find("td", class_="adr").text)}
            }
            # Append player props only to global (all-maps) stats to avoid redundancy (global stats has id all-content)
            if self["id"] == "all-content":
                team2_dict[nick]["playerName"] = x.find(
                    "div", class_="statsPlayerName").text
                team2_dict[nick]["nationality"] = x.find("img")["title"]

        # Counterterrorist second team stats
        for x in tables[4].find_all("tr", class_=""):
            team2_dict[x.find("span", class_="player-nick").text]["ct"] = {
                "kd": x.find("td", class_="kd").text,
                "adr": float(x.find("td", class_="adr").text)
            }

        # Terrorist second team stats
        for x in tables[5].find_all("tr", class_=""):
            team2_dict[x.find("span", class_="player-nick").text]["t"] = {
                "kd": x.find("td", class_="kd").text,
                "adr": float(x.find("td", class_="adr").text)
            }
        return team1_dict, team2_dict
