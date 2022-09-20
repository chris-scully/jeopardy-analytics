import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import json
from scraper.scraper_config import ScraperConfig
from scraper.parsers import parse_metadata, parse_rounds, parse_fj
from scraper.parser_utils import name_to_full_name_map

def scrape_episode(scraper: ScraperConfig \
                    , episode_num: int \
                    , html_parser: str \
                    , episode_base_url: str) -> pd.DataFrame:
    """
    The scraper that scrapes and parses over the entire episode.

    Args:
        scraper (ScraperConfig): a class to store the j-archive scraper
        episode_base_url (str): the standard URL format from j-archive
        episode_num (int): the episode number defined by j-archive,  which will
            determine which episode to scrape and parse

    Returns:
        pd.DataFrame: the complete game DataFrame
    """

    episode_url = episode_base_url + str(episode_num)
    page_html = scraper.get_page(episode_url)

    soup = BeautifulSoup(page_html, features=html_parser)

    meta = parse_metadata(soup)
    episode_date = meta['date']
    show_num = meta['show_num']
    contestants = meta['contestants']

    rounds_df = parse_rounds(soup, episode_date, html_parser)
    # A shortcut to put the data in the format I want
    rounds = rounds_df.to_json(orient='records')
    rounds = json.loads(rounds)
    rounds_df = pd.json_normalize(
        data = rounds,
        record_path = 'responders',
        meta=['clue_id', 'clue_location', 'answer', 'order_num', 'value',
              'was_daily_double', 'correct_response', 'category', 'round_num', 
              'was_triple_stumper', 'wager', 'was_revealed']
    )

    final_jep_df = parse_fj(soup, html_parser)
    episode_df = pd.concat([rounds_df, final_jep_df], ignore_index=True)

    episode_df['game_id'] = episode_num
    episode_df['date'] = episode_date
    episode_df['show_num'] = show_num

    contestants_short_names = episode_df[~episode_df['name'].isnull()]['name'].unique()
    name_map, id_map = name_to_full_name_map(contestants_short_names, contestants)
    episode_df['player_id'] = episode_df['name'].replace(id_map)
    episode_df['name'].replace(name_map, inplace=True)
    

    col_order = ['show_num', 'game_id', 'date', 'clue_id', 'clue_location', 
                'round_num', 'value', 'order_num', 'category','answer', 
                'correct_response', 'name', 'player_id', 'was_correct', 
                'was_revealed', 'was_triple_stumper', 'was_daily_double', 
                'wager']
    episode_df = episode_df[col_order]
    episode_df.sort_values(by=['round_num', 'order_num'], inplace=True)

    return episode_df