# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class LeagueItem(scrapy.Item):
    sport = scrapy.Field()
    country = scrapy.Field()
    league = scrapy.Field()
    driver = scrapy.Field()
    pass

class FixtureItem(scrapy.Item):
    sport = scrapy.Field()
    country = scrapy.Field()
    league = scrapy.Field()
    season = scrapy.Field()
    match_time = scrapy.Field()
    home_team = scrapy.Field()
    away_team = scrapy.Field()
    scraped_date = scrapy.Field()
    pass

class StandingItem(scrapy.Item):
    sport = scrapy.Field()
    country = scrapy.Field()
    league = scrapy.Field()
    season = scrapy.Field()
    team = scrapy.Field()
    overall_rank = scrapy.Field()
    home_rank = scrapy.Field()
    home_mp = scrapy.Field()
    home_w = scrapy.Field()
    home_d = scrapy.Field()
    home_l = scrapy.Field()
    home_gf = scrapy.Field()
    home_ga = scrapy.Field()
    home_pts = scrapy.Field()
    home_wo = scrapy.Field()
    home_lo = scrapy.Field()
    away_rank = scrapy.Field()
    away_mp = scrapy.Field()
    away_w = scrapy.Field()
    away_d = scrapy.Field()
    away_l = scrapy.Field()
    away_gf = scrapy.Field()
    away_ga = scrapy.Field()
    away_pts = scrapy.Field()
    away_wo = scrapy.Field()
    away_lo = scrapy.Field()
    scraped_date = scrapy.Field()
    pass
