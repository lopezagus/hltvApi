init_database = "CREATE DATABASE IF NOT EXISTS `hltv_schema` DEFAULT CHARACTER SET 'utf8'"

team_dim = "CREATE TABLE IF NOT EXISTS `TeamDim` " \
           "(`teamId` INT NOT NULL," \
           "`teamName` VARCHAR(100) NOT NULL, " \
           "PRIMARY KEY (`teamId`));"

event_dim = "CREATE TABLE IF NOT EXISTS `hltv_schema`.`EventDim` (" \
            "`eventId` INT NOT NULL," \
            "`eventName` VARCHAR(100) NOT NULL," \
            "PRIMARY KEY (`eventId`));"

player_dim = "CREATE TABLE IF NOT EXISTS `hltv_schema`.`PlayerDim` (" \
             "`playerId` INT NOT NULL," \
             "`playerName` VARCHAR(100) NOT NULL," \
             "`playerNick` VARCHAR(45) NOT NULL," \
             "`nationality` VARCHAR(45) NULL," \
             "PRIMARY KEY (`playerId`));"

match_dim = "CREATE TABLE IF NOT EXISTS `hltv_schema`.`MatchDim` " \
            "(`matchId` INT NOT NULL," \
            "`bestOf` SMALLINT NOT NULL," \
            "`instance` VARCHAR(300) NULL," \
            "`eventId` INT NOT NULL," \
            "`lan` SMALLINT NOT NULL," \
            "`date` DATE NOT NULL," \
            "`team1Id` INT NOT NULL," \
            "`team2Id` INT NOT NULL," \
            "`winnerId` INT NOT NULL," \
            "PRIMARY KEY (`matchid`)," \
            "INDEX `team1Id_idx` (`team1Id` ASC) VISIBLE," \
            "INDEX `team2Id_idx` (`team2Id` ASC) VISIBLE," \
            "INDEX `eventId_idx` (`eventId` ASC) VISIBLE," \
            "INDEX `winnerid_idx` (`winnerId` ASC) VISIBLE," \
            "CONSTRAINT `FK_MatchDim_BY_team1Id_TO_TeamDim_BY_teamId`" \
            "    FOREIGN KEY (`team1Id`)" \
            "    REFERENCES `hltv_schema`.`TeamDim` (`teamId`)" \
            "    ON DELETE NO ACTION" \
            "    ON UPDATE NO ACTION," \
            "CONSTRAINT `FK_MatchDim_BY_team2Id_TO_TeamDim_BY_teamId`" \
            "    FOREIGN KEY (`team2Id`)" \
            "    REFERENCES `hltv_schema`.`TeamDim` (`teamId`)" \
            "    ON DELETE NO ACTION" \
            "    ON UPDATE NO ACTION," \
            "CONSTRAINT `FK_MatchDim_TO_EventDim_BY_eventId`" \
            "    FOREIGN KEY (`eventId`)" \
            "    REFERENCES `hltv_schema`.`EventDim` (`eventId`)" \
            "    ON DELETE CASCADE" \
            "    ON UPDATE CASCADE," \
            "CONSTRAINT `FK_MatchDim_BY_winnerId_TO_TeamDim_BY_teamId`" \
            "    FOREIGN KEY (`winnerId`)" \
            "    REFERENCES `hltv_schema`.`TeamDim` (`teamId`)" \
            "    ON DELETE NO ACTION" \
            "    ON UPDATE NO ACTION);"

maps_fact = "CREATE TABLE IF NOT EXISTS `hltv_schema`.`MapsFact` (" \
            "`mapId` INT NOT NULL," \
            "`matchId` INT NOT NULL," \
            "`teamId` INT NOT NULL," \
            "`map` VARCHAR(45) NOT NULL," \
            "`score` TINYINT NOT NULL," \
            "`enemy_score` TINYINT NOT NULL," \
            "`ct_result` TINYINT NOT NULL," \
            "`t_result` TINYINT NOT NULL," \
            "`overtime` TINYINT NULL," \
            "`won` TINYINT NULL," \
            "`pick` TINYINT NULL," \
            "PRIMARY KEY (`mapId`, `teamId`)," \
            "INDEX `teamId_idx` (`teamId` ASC) VISIBLE," \
            "INDEX `matchId_idx` (`matchId` ASC) VISIBLE," \
            "CONSTRAINT `FK_MapsFact_TO_TeamDim_BY_teamId`" \
            "  FOREIGN KEY (`teamId`)" \
            "  REFERENCES `hltv_schema`.`TeamDim` (`teamId`)" \
            "  ON DELETE NO ACTION" \
            "  ON UPDATE NO ACTION," \
            "CONSTRAINT `FK_MapsFact_TO_MatchDim_BY_matchId`" \
            "  FOREIGN KEY (`matchId`)" \
            "  REFERENCES `hltv_schema`.`MatchDim` (`matchId`)" \
            "  ON DELETE CASCADE" \
            "  ON UPDATE CASCADE)"

player_fact = "CREATE TABLE IF NOT EXISTS `PlayersFact` (" \
              "`mapId` INT NOT NULL," \
              "`teamId` INT NOT NULL," \
              "`matchId` INT NOT NULL," \
              "`playerId` INT NOT NULL," \
              "`map` VARCHAR(100)," \
              "`ct_kills` TINYINT NOT NULL," \
              "`ct_deaths` TINYINT NOT NULL," \
              "`ct_adr` FLOAT NOT NULL," \
              "`t_kills` TINYINT NOT NULL," \
              "`t_deaths` TINYINT NOT NULL," \
              "`t_adr` FLOAT NOT NULL, " \
              "PRIMARY KEY (`mapId`, `matchId`, `playerId`)," \
              "CONSTRAINT `FK_PlayersFact_TO_MatchDim_BY_matchId`" \
              "  FOREIGN KEY (`matchId`) " \
              "  REFERENCES `hltv_schema`.`MatchDim` (`matchId`)" \
              "  ON DELETE CASCADE ON UPDATE CASCADE," \
              "CONSTRAINT `FK_PlayersFact_TO_PlayerDim_BY_playerId`" \
              "  FOREIGN KEY (`playerId`) " \
              "  REFERENCES `hltv_schema`.`PlayerDim` (`playerId`)" \
              "  ON DELETE NO ACTION ON UPDATE NO ACTION," \
              "CONSTRAINT `FK_PlayersFact_TO_TeamDim_BY_teamId`" \
              "  FOREIGN KEY (`teamId`) " \
              "  REFERENCES `hltv_schema`.`TeamDim` (`teamId`)" \
              "  ON DELETE NO ACTION ON UPDATE NO ACTION);"

team_insert = "INSERT INTO `hltv_schema`.`TeamDim` VALUES"
event_insert = "INSERT INTO `hltv_schema`.`EventDim` VALUES"
player_insert = "INSERT INTO `hltv_schema`.`PlayerDim` VALUES"
match_insert = "INSERT INTO `hltv_schema`.`MatchDim` VALUES"
map_insert = "INSERT INTO `hltv_schema`.`MapsFact` VALUES"
player_stats_insert = "INSERT INTO `hltv_schema`.`PlayersFact` VALUES"

# "INDEX `mapsFact_idx` (`mapId` ASC, `teamId` ASC) VISIBLE," \
# "CONSTRAINT `FK_PlayersFact_TO_MapsFact_BY_mapId_teamId`" \
# "  FOREIGN KEY (`mapId`, `teamId`)" \
# "  REFERENCES `hltv_schema`.`MapsFact` (`mapId`, `teamId`)" \
# "  ON DELETE CASCADE ON UPDATE CASCADE,"
