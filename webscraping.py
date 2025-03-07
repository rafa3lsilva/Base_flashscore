import pandas as pd
pd.set_option('display.max_columns', None)

from tinydb import TinyDB, Query
from tqdm.auto import tqdm

import logging
import warnings
warnings.filterwarnings('ignore')

from time import sleep

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Configuração do logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def drop_reset_index(df):
    df = df.dropna()
    df = df.reset_index(drop=True)
    df.index += 1
    return df

def Dados_Jogo(id_jogo, dictionary, driver):
    """Captura informações básicas do jogo: data, times, liga e rodada."""
    try:
        driver.get(f'https://www.flashscore.com/match/{id_jogo}/#/match-summary/match-summary')
        dictionary['Id'] = id_jogo

        # Extrair país, data, hora e liga
        country = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'span.tournamentHeader__country'))
        ).text.split(':')[0]

        date_time = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.duelParticipant__startTime'))
        ).text.split(' ')
        dictionary['Date'] = date_time[0].replace('.', '/')
        dictionary['Time'] = date_time[1]

        league = driver.find_element(By.CSS_SELECTOR, 'span.tournamentHeader__country > a').text.split(' -')[0]
        dictionary['League'] = f'{country} - {league}'

        # Extrair times
        dictionary['Home'] = driver.find_element(By.CSS_SELECTOR, 'div.duelParticipant__home div.participant__participantName').text
        dictionary['Away'] = driver.find_element(By.CSS_SELECTOR, 'div.duelParticipant__away div.participant__participantName').text

        # Extrair rodada (se disponível)
        try:
            dictionary['Round'] = driver.find_element(By.CSS_SELECTOR, 'span.tournamentHeader__country > a').text.split('- ')[1]
        except:
            dictionary['Round'] = '-'
    except Exception as e:
        logging.error(f"Erro em Dados_Jogo: {e}")

def Temporada(dictionary,season):
    dictionary['Season'] = season

def Odds_Math_Odds_HT(id_jogo,dictionary,driver):
    url_match_odds_ht = f'https://www.flashscore.com/match/{id_jogo}/#/odds-comparison/1x2-odds/1st-half'
    driver.get(url_match_odds_ht)
    sleep(1)
    if driver.current_url == url_match_odds_ht:
        WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'div.ui-table')))
        table_odds = driver.find_element(By.CSS_SELECTOR,'div.ui-table')
        linha_ml_ht = table_odds.find_element(By.CSS_SELECTOR,'div.ui-table__row')
        dictionary['Odd_H_HT'] = float(linha_ml_ht.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
        dictionary['Odd_D_HT'] = float(linha_ml_ht.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
        dictionary['Odd_A_HT'] = float(linha_ml_ht.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[2].text)

def Odds_Math_Odds_FT(id_jogo,dictionary,driver):
    url_match_odds_ft = f'https://www.flashscore.com/match/{id_jogo}/#/odds-comparison/1x2-odds/full-time'
    driver.get(url_match_odds_ft)
    sleep(1)
    if driver.current_url == url_match_odds_ft:
        WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'div.ui-table')))
        table_odds = driver.find_element(By.CSS_SELECTOR,'div.ui-table')
        linha_ml_ft = table_odds.find_element(By.CSS_SELECTOR,'div.ui-table__row')
        dictionary['Odd_H_FT'] = float(linha_ml_ft.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
        dictionary['Odd_D_FT'] = float(linha_ml_ft.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
        dictionary['Odd_A_FT'] = float(linha_ml_ft.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[2].text)
        
def Odds_Over_Under_HT(id_jogo,dictionary,driver):
    url_over_under = f'https://www.flashscore.com/match/{id_jogo}/#/odds-comparison/over-under/1st-half'
    driver.get(url_over_under)
    sleep(1)
    if driver.current_url == url_over_under:
        WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'div.ui-table')))
        linhas = driver.find_elements(By.CSS_SELECTOR,'div.ui-table__body')
        for linha in linhas:
            if (len(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')) > 1):
                total_gols = linha.find_element(By.CSS_SELECTOR,'span.oddsCell__noOddsCell').text.replace('.','')
                if total_gols == '05':
                    over = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
                    under = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
                    dictionary[f'Odd_Over{total_gols}_HT'] = over
                    dictionary[f'Odd_Under{total_gols}_HT'] = under
                elif total_gols == '15':
                    over = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
                    under = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
                    dictionary[f'Odd_Over{total_gols}_HT'] = over
                    dictionary[f'Odd_Under{total_gols}_HT'] = under
                elif total_gols == '25':
                    over = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
                    under = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
                    dictionary[f'Odd_Over{total_gols}_HT'] = over
                    dictionary[f'Odd_Under{total_gols}_HT'] = under
        
def Odds_Over_Under_FT(id_jogo,dictionary,driver):
    url_over_under = f'https://www.flashscore.com/match/{id_jogo}/#/odds-comparison/over-under/full-time'
    driver.get(url_over_under)
    sleep(1)
    if driver.current_url == url_over_under:
        WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'div.ui-table')))
        linhas = driver.find_elements(By.CSS_SELECTOR,'div.ui-table__body')
        for linha in linhas:
            if (len(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')) > 1):
                total_gols = linha.find_element(By.CSS_SELECTOR,'span.oddsCell__noOddsCell').text.replace('.','')
                if total_gols == '05':
                    over = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
                    under = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
                    dictionary[f'Odd_Over{total_gols}_FT'] = over
                    dictionary[f'Odd_Under{total_gols}_FT'] = under
                elif total_gols == '15':
                    over = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
                    under = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
                    dictionary[f'Odd_Over{total_gols}_FT'] = over
                    dictionary[f'Odd_Under{total_gols}_FT'] = under
                elif total_gols == '25':
                    over = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
                    under = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
                    dictionary[f'Odd_Over{total_gols}_FT'] = over
                    dictionary[f'Odd_Under{total_gols}_FT'] = under
                elif total_gols == '35':
                    over = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
                    under = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
                    dictionary[f'Odd_Over{total_gols}_FT'] = over
                    dictionary[f'Odd_Under{total_gols}_FT'] = under
                elif total_gols == '45':
                    over = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
                    under = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
                    dictionary[f'Odd_Over{total_gols}_FT'] = over
                    dictionary[f'Odd_Under{total_gols}_FT'] = under
                
def Odds_BTTS(id_jogo,dictionary,driver):
    url_btts = f'https://www.flashscore.com/match/{id_jogo}/#/odds-comparison/both-teams-to-score/full-time'
    driver.get(url_btts)
    sleep(1)
    if driver.current_url == url_btts:
        WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'div.ui-table')))
        linha = driver.find_element(By.CSS_SELECTOR,'div.ui-table__row')
        dictionary['Odd_BTTS_Yes'] = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
        dictionary['Odd_BTTS_No'] = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
        
def Odds_Dupla_Chance(id_jogo,dictionary,driver):
    url_dupla_chance = f'https://www.flashscore.com/match/{id_jogo}/#/odds-comparison/double-chance/full-time'
    driver.get(url_dupla_chance)
    sleep(1)
    if driver.current_url == url_dupla_chance:
        WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'div.ui-table')))
        linha = driver.find_element(By.CSS_SELECTOR,'div.ui-table__row')
        dictionary['Odd_1X'] = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[0].text)
        dictionary['Odd_12'] = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[1].text)
        dictionary['Odd_X2'] = float(linha.find_elements(By.CSS_SELECTOR,'a.oddsCell__odd')[2].text)


def Goals_HT_FT(id_jogo, dictionary, driver):
    try:
        # Navigate to the match URL
        central_info_url = f'https://www.flashscore.com/match/{id_jogo}/#/match-summary/match-summary'
        driver.get(central_info_url)
        sleep(5)

        # Wait for the page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.smv__verticalSections'))
        )

        # Check if the match was "Awarded" or "Postponed"
        try:
            awarded_element = driver.find_element(By.CSS_SELECTOR, 'span.fixedHeaderDuel__detailStatus')
            if awarded_element.text.strip().lower() in ["awarded", "postponed"]:
                print(f"Jogo {id_jogo} não se realizou. Ignorando HT e ST.")
                dictionary['Goals_H_HT'] = None
                dictionary['Goals_A_HT'] = None
                dictionary['Goals_H_FT'] = None
                dictionary['Goals_A_FT'] = None
                return dictionary
        except NoSuchElementException:
            pass  # Continue if the status element is not found

        # Extract HT (1st Half) score
        try:
            ht_element = driver.find_element(By.XPATH, '//span[@data-testid="wcl-scores-overline-02" and contains(text(), "1st Half")]/following-sibling::span/div')
            ht_score = ht_element.text.strip()
            if ht_score and '-' in ht_score:
                dictionary['Goals_H_HT'], dictionary['Goals_A_HT'] = map(int, ht_score.split(' - '))
            else:
                dictionary['Goals_H_HT'], dictionary['Goals_A_HT'] = None, None
                print(f"1st Half não disponível para o jogo {id_jogo}.")
        except NoSuchElementException:
            dictionary['Goals_H_HT'], dictionary['Goals_A_HT'] = None, None
            print(f"1st Half não encontrado para o jogo {id_jogo}.")


        # Extract FT (Full Time) score
        try:
            ft_element = driver.find_element(By.CSS_SELECTOR, 'div.detailScore__wrapper')
            ft_score = ft_element.text.strip()
            if ft_score and '-' in ft_score:
                home_goals_ft, away_goals_ft = ft_score.split('-')
                dictionary['Goals_H_FT'] = int(home_goals_ft.strip())
                dictionary['Goals_A_FT'] = int(away_goals_ft.strip())
            else:
                dictionary['Goals_H_FT'], dictionary['Goals_A_FT'] = None, None
                print(f"Full Time não disponível para o jogo {id_jogo}.")
        except NoSuchElementException:
            dictionary['Goals_H_FT'], dictionary['Goals_A_FT'] = None, None
            print(f"Full Time não encontrado para o jogo {id_jogo}.")

    except Exception as e:
        print(f"Erro geral ao processar o jogo {id_jogo}: {e}")
        dictionary['Goals_H_HT'], dictionary['Goals_A_HT'] = None, None
        dictionary['Goals_H_FT'], dictionary['Goals_A_FT'] = None, None

    return dictionary

def Minutos_dos_Gols(id_jogo,dictionary,driver):
    def trata_minuto(minuto):
        minuto = minuto
        if "'" in minuto:
            minuto = minuto.replace("'","")
        if ":" in minuto:
            minuto = minuto.split(':')[0]
        if "+" in minuto:
            minuto = minuto.split('+')[0]
        return int(minuto)
    url = f'https://www.flashscore.com/match/{id_jogo}/#/match-summary/match-summary'
    if driver.current_url != url:
        driver.get(url)
    try:
        WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'div.smv__verticalSections')))
        soup = driver.page_source
        soup = BeautifulSoup(driver.page_source)
        min_goals_home = []
        min_goals_away = []
        try:
            home_incidents = soup.find_all('div',{"class":['smv__homeParticipant']})
            for i in home_incidents:
                if ('smv__incidentHomeScore' in str(i)) | ('footballOwnGoal-ico' in str(i)):
                    min_goals_home.append(trata_minuto(i.find('div',{"class":['smv__timeBox']}).text))
            dictionary['Goals_Minutes_Home'] = min_goals_home
        except:
            dictionary['Goals_Minutes_Home'] = min_goals_home
        try:
            away_incidents = soup.find_all('div',{"class":['smv__awayParticipant']})
            for i in away_incidents:
                if ('smv__incidentAwayScore' in str(i)) | ('footballOwnGoal-ico' in str(i)):
                    min_goals_away.append(trata_minuto(i.find('div',{"class":['smv__timeBox']}).text))
            dictionary['Goals_Minutes_Away'] = min_goals_away
        except:
                dictionary['Goals_Minutes_Away'] = min_goals_away
    except:
        pass                    