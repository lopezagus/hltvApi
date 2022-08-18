init_database = "CREATE SCHEMA `hltv_schema`;"

team_dim = "DROP TABLE IF EXISTS `schema.team_dim`; " \
           "CREATE TABLE `schema.team_dimension` " \
           "(`teamid` INT NOT NULL," \
           "`teamname` VARCHAR(100) NOT NULL, "\
           "PRIMARY KEY (`teamid`));"

event_dim = "CREATE TABLE IF NOT EXISTS `hltv_schema`.`event_dim` (" \
            "`eventid` INT NOT NULL," \
            "`eventname` VARCHAR(100) NOT NULL," \
            "PRIMARY KEY (`eventid`));"

player_dim = "CREATE TABLE IF NOT EXISTS `hltv_schema`.`player_dim` (" \
             "`playerid` INT NOT NULL," \
             "`playerName` VARCHAR(100) NOT NULL," \
             "`playerNick` VARCHAR(45) NOT NULL," \
             "`nationality` VARCHAR(45) NULL," \
             "PRIMARY KEY (`playerid`));"

match_dim = "CREATE TABLE IF NOT EXISTS `hltv_schema`.`match_dim` " \
            "(`matchid` INT NOT NULL," \
            "`bestof` SMALLINT NOT NULL," \
            "`instance` VARCHAR(100) NULL," \
            "`eventid` INT NOT NULL," \
            "`lan` SMALLINT NOT NULL," \
            "`date` DATE NOT NULL," \
            "`team1id` INT NOT NULL," \
            "`team2id` INT NOT NULL," \
            "`winnerid` INT NOT NULL," \
            "PRIMARY KEY (`matchid`)," \
            "INDEX `team1id_idx` (`team1id` ASC) VISIBLE," \
            "INDEX `team2id_idx` (`team2id` ASC) VISIBLE," \
            "INDEX `eventid_idx` (`eventid` ASC) VISIBLE," \
            "INDEX `winnerid_idx` (`winnerid` ASC) VISIBLE," \
            "CONSTRAINT `team1id`" \
            "    FOREIGN KEY (`team1id`)" \
            "    REFERENCES `hltv_schema`.`team_dim` (`teamid`)" \
            "    ON DELETE NO ACTION" \
            "    ON UPDATE NO ACTION," \
            "CONSTRAINT `team2id`" \
            "    FOREIGN KEY (`team2id`)" \
            "    REFERENCES `hltv_schema`.`team_dim` (`teamid`)" \
            "    ON DELETE NO ACTION" \
            "    ON UPDATE NO ACTION," \
            "CONSTRAINT `eventid`" \
            "    FOREIGN KEY (`eventid`)" \
            "    REFERENCES `hltv_schema`.`event_dim` (`eventid`)" \
            "    ON DELETE CASCADE" \
            "    ON UPDATE CASCADE," \
            "CONSTRAINT `winnerid`" \
            "    FOREIGN KEY (`winnerid`)" \
            "    REFERENCES `hltv_schema`.`team_dim` (`teamid`)" \
            "    ON DELETE NO ACTION" \
            "    ON UPDATE NO ACTION);" 

maps_fact = "CREATE TABLE IF NOT EXISTS `hltv_schema`.`maps_fact` (" \
           "`mapid` INT NOT NULL," \
           "`matchid` INT NOT NULL," \
           "`teamid` INT NOT NULL," \
           "`map` VARCHAR(45) NOT NULL," \
           "`score` TINYINT NOT NULL," \
           "`enemy_score` TINYINT NOT NULL," \
           "`ct_result` TINYINT NOT NULL," \
           "`t_result` TINYINT NOT NULL," \
           "`overtime` TINYINT NULL," \
           "`won` TINYINT NULL," \
           "`pick` TINYINT NULL," \
           "PRIMARY KEY (`mapid`)," \
           "INDEX `teamid_idx` (`teamid` ASC) VISIBLE," \
           "INDEX `matchid_idx` (`matchid` ASC) VISIBLE," \
           "CONSTRAINT `teamid`" \
           "  FOREIGN KEY (`teamid`)" \
           "  REFERENCES `hltv_schema`.`team_dim` (`teamid`)" \
           "  ON DELETE NO ACTION" \
           "  ON UPDATE NO ACTION," \
           "CONSTRAINT `matchid`" \
           "  FOREIGN KEY (`matchid`)" \
           "  REFERENCES `hltv_schema`.`match_dim` (`matchid`)" \
           "  ON DELETE CASCADE" \
           "  ON UPDATE CASCADE)"

player_fact = "CREATE TABLE IF NOT EXISTS `hltv_schema`.`players_fact` (" \
              "`mapid` INT NOT NULL," \
              "`matchid` INT NOT NULL," \
              "`playerid` INT NOT NULL," \
              "`teamid` INT NOT NULL," \
              "`map` VARCHAR(100)," \
              "`ct_kills` TINYINT NOT NULL," \
              "`ct_deaths` TINYINT NOT NULL," \
              "`ct_adr` FLOAT NOT NULL," \
              "`t_kills` TINYINT NOT NULL," \
              "`t_deaths` TINYINT NOT NULL," \
              "`t_adr` FLOAT NOT NULL, " \
              "PRIMARY KEY (`mapid`, `playerid`)," \
              "INDEX `matchid_idx` (`matchid` ASC) VISIBLE," \
              "INDEX `teamid_idx` (`teamid` ASC) VISIBLE," \
              "CONSTRAINT `mapid`" \
              "  FOREIGN KEY (`mapid`) REFERENCES `hltv_schema`.`maps_fact` (`mapid`)," \
              "  ON DELETE CASCADE ON UPDATE CASCADE," \
              "CONSTRAINT `matchid`" \
              "  FOREIGN KEY (`matchid`) REFERENCES `hltv_schema`.`match_dim` (`matchid`)" \
              "  ON DELETE CASCADE ON UPDATE CASCADE," \
              "CONSTRAINT `playerid`" \
              "  FOREIGN KEY (`playerid`) REFERENCES `hltv_schema`.`player_dim` (`playerid`)" \
              "  ON DELETE NO ACTION ON UPDATE NO ACTION," \
              "CONSTRAINT `teamid`" \
              "  FOREIGN KEY (`teamid`) REFERENCES `hltv_schema`.`team_dim` (`teamid`)" \
              "  ON DELETE NO ACTION ON UPDATE NO ACTION);"

team_insert = "INSERT INTO `hltv_schema`.`team_dim` VALUES"
event_insert = "INSERT INTO `hltv_schema`.`event_dim` VALUES"
player_insert = "INSERT INTO `hltv_schema`.`player_dim` VALUES"
match_insert = "INSERT INTO `hltv_schema`.`match_dim` VALUES"
map_insert = "INSERT INTO `hltv_schema`.`maps_fact` VALUES"
player_stats_insert = "INSERT INTO `hltv_schema`.`players_fact` VALUES"
