-- MySQL dump 10.13  Distrib 5.7.11, for osx10.11 (x86_64)
--
-- Host: localhost    Database: deutsch
-- ------------------------------------------------------
-- Server version	5.7.11

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `gender_rules`
--

DROP TABLE IF EXISTS `gender_rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gender_rules` (
  `article` varchar(5) NOT NULL,
  `rule` varchar(128) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gender_rules`
--

LOCK TABLES `gender_rules` WRITE;
/*!40000 ALTER TABLE `gender_rules` DISABLE KEYS */;
INSERT INTO `gender_rules` VALUES ('der','nouns that refer to males'),('der','many that end with -en -er -el'),('der','days of the week'),('der','months'),('der','seasons'),('der','foreign words with accent on last syllable'),('der','nouns that are infinitive minus -en'),('der','many that form plural with umlaut + -e'),('der','end with -ich -ig -ismus -ist -ling -us'),('die','nouns that refer to females'),('die','numerals'),('die','some rivers'),('die','many that end with -e'),('die','females in professions that end with -in'),('die','many that end with -a'),('die','many that form plural with -(e)n'),('die','end with -ei -heit -keit -ie -ik -nz -schaft -ion -tät -ung -ur'),('das','diminutives that end in -chen or -lein'),('das','nouns formed from an infinitive'),('das','most that end with -nis'),('das','many with prefix ge-'),('das','metals'),('das','end with -ment'),('das','most that form plural with umlaut + er'),('das','end with -tel -tum -um');
/*!40000 ALTER TABLE `gender_rules` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-10-05 21:54:48
