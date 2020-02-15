# ************************************************************
# Sequel Pro SQL dump
# Version (null)
#
# https://www.sequelpro.com/
# https://github.com/sequelpro/sequelpro
#
# Host: server.lan (MySQL 5.7.29-0ubuntu0.18.04.1)
# Database: garmin
# Generation Time: 2020-02-15 09:39:48 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
SET NAMES utf8mb4;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table activities
# ------------------------------------------------------------

DROP TABLE IF EXISTS `activities`;

CREATE TABLE `activities` (
  `activity_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `cs_user_id` bigint(20) unsigned DEFAULT NULL,
  `file_id` bigint(20) unsigned DEFAULT NULL,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `json` text,
  `startTimeInSeconds` bigint(20) unsigned DEFAULT NULL,
  `userId` varchar(128) DEFAULT NULL,
  `userAccessToken` varchar(128) DEFAULT NULL,
  `summaryId` varchar(128) DEFAULT NULL,
  `created_ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `parent_activity_id` bigint(20) unsigned DEFAULT NULL,
  PRIMARY KEY (`activity_id`),
  KEY `activities_startTimeInSeconds_index` (`startTimeInSeconds`),
  KEY `activities_cs_user_id` (`cs_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table assets
# ------------------------------------------------------------

DROP TABLE IF EXISTS `assets`;

CREATE TABLE `assets` (
  `asset_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `file_id` bigint(20) unsigned DEFAULT NULL,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `tablename` varchar(128) DEFAULT NULL,
  `filename` varchar(32) DEFAULT NULL,
  `path` varchar(128) DEFAULT NULL,
  `data` mediumblob,
  `created_ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`asset_id`),
  KEY `assets_file_id_index` (`file_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table cache_activities
# ------------------------------------------------------------

DROP TABLE IF EXISTS `cache_activities`;

CREATE TABLE `cache_activities` (
  `cache_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `started_ts` datetime DEFAULT NULL,
  `processed_ts` datetime DEFAULT NULL,
  `json` json,
  PRIMARY KEY (`cache_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table cache_activities_map
# ------------------------------------------------------------

DROP TABLE IF EXISTS `cache_activities_map`;

CREATE TABLE `cache_activities_map` (
  `activity_id` bigint(20) unsigned NOT NULL,
  `cache_id` bigint(20) unsigned DEFAULT NULL,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`activity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table cache_fitfiles
# ------------------------------------------------------------

DROP TABLE IF EXISTS `cache_fitfiles`;

CREATE TABLE `cache_fitfiles` (
  `cache_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `started_ts` datetime DEFAULT NULL,
  `processed_ts` datetime DEFAULT NULL,
  `json` json,
  PRIMARY KEY (`cache_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table cache_fitfiles_map
# ------------------------------------------------------------

DROP TABLE IF EXISTS `cache_fitfiles_map`;

CREATE TABLE `cache_fitfiles_map` (
  `file_id` bigint(20) unsigned NOT NULL,
  `cache_id` bigint(20) unsigned DEFAULT NULL,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`file_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table fitfiles
# ------------------------------------------------------------

DROP TABLE IF EXISTS `fitfiles`;

CREATE TABLE `fitfiles` (
  `file_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `activity_id` bigint(20) unsigned DEFAULT NULL,
  `asset_id` bigint(20) unsigned DEFAULT NULL,
  `cs_user_id` bigint(20) unsigned DEFAULT NULL,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `userId` varchar(128) DEFAULT NULL,
  `userAccessToken` varchar(128) DEFAULT NULL,
  `callbackURL` text,
  `startTimeInSeconds` bigint(20) unsigned DEFAULT NULL,
  `summaryId` varchar(128) DEFAULT NULL,
  `created_ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fileType` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`file_id`),
  KEY `fitfiles_startTimeInSeconds_index` (`startTimeInSeconds`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table fitsession
# ------------------------------------------------------------

DROP TABLE IF EXISTS `fitsession`;

CREATE TABLE `fitsession` (
  `file_id` bigint(20) unsigned NOT NULL,
  `cs_user_id` bigint(20) unsigned DEFAULT NULL,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `json` json,
  PRIMARY KEY (`file_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table schema
# ------------------------------------------------------------

DROP TABLE IF EXISTS `schema`;

CREATE TABLE `schema` (
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `version` bigint(20) unsigned DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table tokens
# ------------------------------------------------------------

DROP TABLE IF EXISTS `tokens`;

CREATE TABLE `tokens` (
  `token_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `cs_user_id` bigint(20) unsigned DEFAULT NULL,
  `userAccessToken` varchar(128) DEFAULT NULL,
  `userId` varchar(128) DEFAULT NULL,
  `userAccessTokenSecret` varchar(128) DEFAULT NULL,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`token_id`),
  KEY `tokens_userAccess` (`userAccessToken`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table usage
# ------------------------------------------------------------

DROP TABLE IF EXISTS `usage`;

CREATE TABLE `usage` (
  `usage_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `cs_user_id` bigint(20) unsigned DEFAULT NULL,
  `status` int(10) unsigned DEFAULT NULL,
  `REQUEST_URI` varchar(256) DEFAULT NULL,
  `SCRIPT_NAME` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`usage_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table users
# ------------------------------------------------------------

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `cs_user_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `userId` varchar(128) DEFAULT NULL,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`cs_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table weather
# ------------------------------------------------------------

DROP TABLE IF EXISTS `weather`;

CREATE TABLE `weather` (
  `file_id` bigint(20) unsigned NOT NULL,
  `cs_user_id` bigint(20) unsigned DEFAULT NULL,
  `ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `json` json,
  PRIMARY KEY (`file_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;




/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
