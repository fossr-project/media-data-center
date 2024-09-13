# -*- coding: UTF-8 -*-
import sqlite3
from sqlite3 import Error
import mylib
import configparser

config = configparser.ConfigParser()
config.read("conf.ini")

DB_FILENAME = config["DEFAULT"]["DB_FILENAME"]


def main():
  sql_create_harvestingOperation_table = """CREATE TABLE IF NOT EXISTS harvestingOperation (
                  id integer PRIMARY KEY,
                  date text NOT NULL,
                  byAgent text,
                  type text NOT NULL,
                  dataFile text,
                  dataFileWithPath text
                );"""
  
  sql_create_zenodoItem_table = """CREATE TABLE IF NOT EXISTS zenodoItem (
                  id integer PRIMARY KEY,
                  date text NOT NULL,
                  doiResource text,
                  doiUrlResource text,
                  idHarvestingOperation integer
                );"""
                
  # see https://www.rssboard.org/media-rss#media-content
  sql_create_multipleMediaItem_table = """CREATE TABLE IF NOT EXISTS multipleMediaItem (
                  id integer PRIMARY KEY,
                  creationDate text,
                  byAgent text NOT NULL,
                  type text,
                  status text NOT NULL,
                  publicationDate text,
                  idHarvestingOperation integer
                );"""
  
  sql_create_zenodoMMRelation_table = """CREATE TABLE IF NOT EXISTS zenodoMMRelation (
                  idZenodoItem integer NOT NULL,
                  idMultipleMedia integer NOT NULL,
                  FOREIGN KEY (idZenodoItem) REFERENCES zenodoItem(id),
                  FOREIGN KEY (idMultipleMedia) REFERENCES multipleMediaItem(id),
                  PRIMARY KEY (idZenodoItem, idMultipleMedia)
                );"""

  sql_create_facebookPost_table = """CREATE TABLE IF NOT EXISTS facebookPost (
                  id integer PRIMARY KEY,
                  lastModDate text NOT NULL,
                  msg text NOT NULL,
                  imageUrl text,
                  modifiedBy text,
                  status text NOT NULL,
                  scheduledPublicationDate text,
                  publicationDate text,
                  idMultipleMedia integer NOT NULL,
                  FOREIGN KEY (idMultipleMedia) REFERENCES multipleMediaItem(id)
                );"""
                
  sql_create_linkedinPost_table = """CREATE TABLE IF NOT EXISTS linkedinPost (
                  id integer PRIMARY KEY,
                  lastModDate text NOT NULL,
                  msg text NOT NULL,
                  imageUrl text,
                  modifiedBy text,
                  status text NOT NULL,
                  scheduledPublicationDate text,
                  publicationDate text,
                  idMultipleMedia integer NOT NULL,
                  FOREIGN KEY (idMultipleMedia) REFERENCES multipleMediaItem(id)
                );"""
                
  sql_create_xPost_table = """CREATE TABLE IF NOT EXISTS xPost (
                  id integer PRIMARY KEY,
                  lastModDate text NOT NULL,
                  msg text NOT NULL,
                  imageUrl text,
                  modifiedBy text,
                  status text NOT NULL,
                  scheduledPublicationDate text,
                  publicationDate text,
                  idMultipleMedia integer NOT NULL,
                  FOREIGN KEY (idMultipleMedia) REFERENCES multipleMediaItem(id)
                );"""
  
  sql_create_feedItem_table = """CREATE TABLE IF NOT EXISTS feedItem (
                  id integer PRIMARY KEY,
                  lastModDate text NOT NULL,
                  title text NOT NULL,
                  link text,
                  description text,
                  category text,
                  enclosure text,
                  doiResource text,
                  doiUrlResource text,
                  modifiedBy text,
                  status text,
                  scheduledPublicationDate text,
                  publicationDate text,
                  idMultipleMedia integer NOT NULL,
                  FOREIGN KEY (idMultipleMedia) REFERENCES multipleMediaItem(id)
                );"""

  '''
  sql_create_curriculum_table = """ CREATE TABLE IF NOT EXISTS curriculum (
                    id integer PRIMARY KEY,
                    authorId integer,
                    annoAsn text NOT NULL,
                    settore text NOT NULL,
                    ssd text,
                    quadrimestre integer NOT NULL,
                    fascia integer NOT NULL,
                    orcid text,
                    cognome text,
                    nome text,
                    bibl integer,
                    I1 integer NOT NULL,
                    I2 integer NOT NULL,
                    I3 integer NOT NULL,
                    idSoglia integer NOT NULL,
                    esito text NOT NULL,
                    FOREIGN KEY (idSoglia) REFERENCES sogliaAsn(id)
                    FOREIGN KEY (authorId) REFERENCES authorScopus(id)
                  ); """

 
  sql_create_cercauniversita_table = """CREATE TABLE IF NOT EXISTS cercauniversita (
                  id string PRIMARY KEY,
                  authorId integer,
                  anno text NOT NULL,
                  settore text NOT NULL,
                  ssd text,
                  fascia integer NOT NULL,
                  orcid text,
                  cognome text,
                  nome text,
                  genere text,
                  ateneo text,
                  facolta text,
                  strutturaAfferenza,
                  FOREIGN KEY (authorId) REFERENCES authorScopus(id)
                );"""
  
  sql_create_sogliaAsn_table = """ CREATE TABLE IF NOT EXISTS sogliaAsn (
                    id integer PRIMARY KEY,
                    annoAsn text NOT NULL,
                    settore text NOT NULL,
                    descrSettore string,
                    ssd text,
                    fascia integer NOT NULL,
                    S1 integer,
                    S2 integer,
                    S3 integer,
                    descrS1 string NOT NULL,
                    descrS2 string NOT NULL,
                    descrS3 string NOT NULL,
                    bibl integer
                  ); """

  sql_create_wroteRelation_table = """ CREATE TABLE IF NOT EXISTS wroteRelation (
                    authorId integer NOT NULL,
                    eid string,
                    FOREIGN KEY (eid) REFERENCES authorScopus(id),
                    FOREIGN KEY (eid) REFERENCES publication(eid)
                  ); """

  sql_create_publication_table = """ CREATE TABLE IF NOT EXISTS publication (
                    eid string PRIMARY KEY,
                    doi string,
                    publicationDate string,
                    publicationYear string NOT NULL,
                    title string NOT NULL,
                    venueName string NOT NULL
                  ); """

  sql_create_citesRelation_table = """ CREATE TABLE IF NOT EXISTS citesRelation (
                    eidCiting string,
                    eidCited string,
                    citationDate string,
                    citationYear string NOT NULL
                  ); """
  '''
  
  # create a database connection
  conn = mylib.create_connection(DB_FILENAME)
 
  # create tables
  if conn is not None:
    # create authorScopus table
    mylib.create_table(conn, sql_create_harvestingOperation_table)
    mylib.create_table(conn, sql_create_zenodoItem_table)
    mylib.create_table(conn, sql_create_multipleMediaItem_table)
    mylib.create_table(conn, sql_create_zenodoMMRelation_table)
    mylib.create_table(conn, sql_create_facebookPost_table)
    mylib.create_table(conn, sql_create_linkedinPost_table)
    mylib.create_table(conn, sql_create_xPost_table)
    mylib.create_table(conn, sql_create_feedItem_table)
    # INSERT MODEL FOR NEW POSTS
    mylib.insert_multipleMediaItem(conn, (None,"Media Data Center","","",None,None), 0)
    mylib.insert_facebookPost(conn, ("", "", None, None, "", None, None, 0), 0)
    mylib.insert_linkedinPost(conn, ("", "", None, None, "", None, None, 0), 0)
    mylib.insert_xPost(conn, ("", "", None, None, "", None, None, 0), 0)
    mylib.insert_feedItem(conn, ("", "", "", "", None, None, None, None, None, None, None, None, 0), 0)
    
    conn.close()
  else:
    print("Error! cannot create the database connection.")
  
  
if __name__ == '__main__':
  main()
