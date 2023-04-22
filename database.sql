SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

DROP TABLE IF EXISTS `btipz_getlogs`;
CREATE TABLE `btipz_getlogs` (
  `log_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `address` varchar(42) NOT NULL,
  `block_number` bigint(20) NOT NULL,
  `block_timestamp` int(11) NOT NULL,
  `datetime` datetime DEFAULT current_timestamp(),
  `transaction_hash` varchar(70) NOT NULL,
  `transaction_index` bigint(20) NOT NULL,
  `log_index` int(11) NOT NULL,
  `topics` longtext DEFAULT NULL,
  `topic0` varchar(70) GENERATED ALWAYS AS (json_unquote(json_extract(`topics`,'$[0]'))) VIRTUAL,
  `topic1` varchar(42) GENERATED ALWAYS AS (concat('0x',right(json_unquote(json_extract(`topics`,'$[1]')),40))) VIRTUAL,
  `topic2` varchar(42) GENERATED ALWAYS AS (concat('0x',right(json_unquote(json_extract(`topics`,'$[2]')),40))) VIRTUAL,
  `topic3` varchar(42) GENERATED ALWAYS AS (concat('0x',right(json_unquote(json_extract(`topics`,'$[3]')),40))) VIRTUAL,
  `data` mediumtext DEFAULT NULL,
  `removed` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`log_id`),
  KEY `block_number` (`block_number`),
  KEY `block_timestamp` (`block_timestamp`),
  KEY `address` (`address`),
  KEY `transaction_hash` (`transaction_hash`),
  KEY `topic0` (`topic0`),
  KEY `topic1` (`topic1`),
  KEY `topic2` (`topic2`)
) ENGINE=InnoDB DEFAULT CHARSET=ascii COLLATE=ascii_general_ci ROW_FORMAT=COMPRESSED;

DROP TABLE IF EXISTS `btipz_tx_notified`;
CREATE TABLE `btipz_tx_notified` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ticker` varchar(32) NOT NULL,
  `decimal` tinyint(2) NOT NULL,
  `block_number` bigint(20) NOT NULL,
  `block_timestamp` int(11) NOT NULL,
  `transaction_hash` varchar(70) NOT NULL,
  `from_address` varchar(42) NOT NULL,
  `to_address` varchar(42) NOT NULL,
  `real_amount` decimal(48,20) NOT NULL,
  `notified_date` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `transaction_hash` (`transaction_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=ascii COLLATE=ascii_general_ci;
