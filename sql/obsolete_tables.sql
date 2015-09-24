-- MySQL dump 10.13  Distrib 5.5.34, for osx10.6 (i386)
--
-- Host: localhost    Database: deutsch
-- ------------------------------------------------------
-- Server version	5.5.34

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
-- Temporary table structure for view `quiz_attr_count`
--

DROP TABLE IF EXISTS `quiz_attr_count`;
/*!50001 DROP VIEW IF EXISTS `quiz_attr_count`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `quiz_attr_count` (
  `quiz_id` tinyint NOT NULL,
  `pos_id` tinyint NOT NULL,
  `attribute_id` tinyint NOT NULL,
  `attrcount` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `quiz_word_attr_count`
--

DROP TABLE IF EXISTS `quiz_word_attr_count`;
/*!50001 DROP VIEW IF EXISTS `quiz_word_attr_count`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `quiz_word_attr_count` (
  `quiz_id` tinyint NOT NULL,
  `pos_id` tinyint NOT NULL,
  `attribute_id` tinyint NOT NULL,
  `word_id` tinyint NOT NULL,
  `attrcount` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `quiz_attr_count`
--

/*!50001 DROP TABLE IF EXISTS `quiz_attr_count`*/;
/*!50001 DROP VIEW IF EXISTS `quiz_attr_count`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = latin1 */;
/*!50001 SET character_set_results     = latin1 */;
/*!50001 SET collation_connection      = latin1_swedish_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`german`@`dev13.plaxo.com` SQL SECURITY DEFINER */
/*!50001 VIEW `quiz_attr_count` AS select distinct `quiz`.`id` AS `quiz_id`,`qs`.`pos_id` AS `pos_id`,`qs`.`attribute_id` AS `attribute_id`,count(0) AS `attrcount` from (`quiz` join `quiz_structure` `qs` on((`quiz`.`id` = `qs`.`quiz_id`))) group by `quiz`.`id`,`qs`.`pos_id` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `quiz_word_attr_count`
--

/*!50001 DROP TABLE IF EXISTS `quiz_word_attr_count`*/;
/*!50001 DROP VIEW IF EXISTS `quiz_word_attr_count`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`german`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `quiz_word_attr_count` AS select `qs`.`quiz_id` AS `quiz_id`,`qs`.`pos_id` AS `pos_id`,`qs`.`attribute_id` AS `attribute_id`,`w`.`id` AS `word_id`,count(0) AS `attrcount` from ((`word` `w` join `quiz_structure` `qs`) join `word_attribute` `wa`) where ((`w`.`pos_id` = `qs`.`pos_id`) and (`wa`.`word_id` = `w`.`id`) and (`wa`.`attribute_id` = `qs`.`attribute_id`)) group by `qs`.`quiz_id`,`w`.`id` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-02-03 11:46:10
