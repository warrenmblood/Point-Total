# author: Warren Blood
# last update: 1-16-2022

import numpy as np
import pandas as pd
import scrapy
from bs4 import BeautifulSoup
from bs4 import Comment
from datetime import datetime

# dict of team names and their corresponding code
codes = {'Arizona Cardinals': 'ARI',
         'Atlanta Falcons': 'ATL',
         'Baltimore Ravens': 'BAL',
         'Buffalo Bills': 'BUF',
         'Carolina Panthers': 'CAR',
         'Chicago Bears': 'CHI',
         'Cincinnati Bengals': 'CIN',
         'Cleveland Browns': 'CLE',
         'Dallas Cowboys': 'DAL',
         'Denver Broncos': 'DEN',
         'Detroit Lions': 'DET',
         'Green Bay Packers': 'GNB',
         'Houston Texans': 'HOU',
         'Indianapolis Colts': 'IND',
         'Jacksonville Jaguars': 'JAX',
         'Kansas City Chiefs': 'KAN',
         'Las Vegas Raiders': 'LVR',
         'Los Angeles Chargers': 'LAC',
         'Los Angeles Rams': 'LAR',
         'Miami Dolphins': 'MIA',
         'Minnesota Vikings': 'MIN',
         'New England Patriots': 'NWE',
         'New Orleans Saints': 'NOR',
         'New York Giants': 'NYG',
         'New York Jets': 'NYJ',
         'Oakland Raiders': 'OAK',
         'Philadelphia Eagles': 'PHI',
         'Pittsburgh Steelers': 'PIT',
         'San Diego Chargers': 'SDG',
         'San Francisco 49ers': 'SFO',
         'Seattle Seahawks': 'SEA',
         'St. Louis Rams': 'STL',
         'Tampa Bay Buccaneers': 'TAM',
         'Tennessee Titans': 'TEN',
         'Washington Football Team': 'WAS',
         'Washington Redskins': 'WAS'
}


class SpiderSpider(scrapy.Spider):
    
    name = 'spider'
    allowed_domains = ['pro-football-reference.com']
    start_urls = []
    handle_httpstatus_all = True
    
    domain = 'https://pro-football-reference.com/'
    
    start_year = 2006
    end_year = 2020
    
    # range of years of games to scrape
    years = np.arange(start_year, end_year + 1, 1)
    # range of weeks in NFL season (including postseason)
    week_nums = np.arange(1,22,1)
    
    # generate all week page urls and append to start_urls
    for i in range(len(years)):
        for j in range(len(week_nums)):
            start_urls.append(domain + 'years/' + str(years[i]) + '/week_' + str(week_nums[j]) + '.htm')
    for i in range(18):
        start_urls.append(domain + 'years/' + str(2021) + '/week_' + str(week_nums[i]) + '.htm')
        
    
    def get_seconds(self, clock, quarter):
    # return (potential) remaining game time in seconds (int) based on given game clock (str) and quarter (str)
        t = clock.split(':')  
        return (900 * (5 - int(quarter)) + 60 * int(t[0]) + int(t[1]))
    
    
    def get_player_team(self, player_url, game_date):
    # return the team code (str) of a player on a specified game date
        tables = pd.read_html(player_url)
        date = game_date.strftime("%Y-%m-%d")
        team = 'NO TEAM'
        for i in range(len(tables)):
            try:
                team = tables[i].to_numpy()[np.where(tables[i].to_numpy()[:,1] == date)[0][0]][5]
            except:
                pass
        return team
    
                    
    def parse(self, response):
    # main parse function: create requests from each week page 
        games = response.xpath('//div[@class="game_summaries"]/div[@class="game_summary expanded nohover"]')
        for g in games:
            game_url = self.domain + g.xpath('.//table[@class="teams"]/tbody/tr/td[@class="right gamelink"]/a/@href').extract_first()
            yield scrapy.Request(url=game_url, callback=self.parse_game)
            
            
    def parse_game(self, response):
    # parse data on each game page
    
        # extract data from page tables into arrays
        soup = BeautifulSoup(response.text, 'html.parser')
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        tables = []
        for c in comments:
            if 'table' in c:
                try:
                    tables.append(pd.read_html(c)[0])
                except:
                    pass
                
        game_info = tables[1].to_numpy()
        officials = tables[2].to_numpy()
        team_stats = tables[4].to_numpy()
        kick_punt_returns = tables[6].to_numpy()
        kicking_punting = tables[7].to_numpy()
        home_drives = tables[-3].to_numpy()
        away_drives = tables[-2].to_numpy()
        play_by_play = tables[-1].to_numpy()
        
        box_path = '//div[@class="scorebox_meta"]/'
        ls_path = '//table[@class="linescore nohover stats_table no_freeze"]/tbody[1]/'
        
        # general game information
        game_date = datetime.strptime(response.xpath(box_path + 'div[1]/text()').extract_first(), '%A %b %d, %Y')
        start_time = response.xpath(box_path + 'div[2]/text()').extract_first()[2:]
        stadium = response.xpath(box_path + 'div[3]/a/text()').extract_first()
        referee = officials[np.where(officials[:,0] == 'Referee')[0][0]][1]
        vegas_o_u = game_info[np.where(game_info[:,0] == 'Over/Under')[0][0]][1].split(' ')[0]
        vegas_spread = game_info[np.where(game_info[:,0] == 'Vegas Line')[0][0]][1]
        try:
            weather = game_info[np.where(game_info[:,0] == 'Weather')[0][0]][1]
        except:
            weather = '70 degrees, relative humidity 45%, no wind'
        
        home_team = response.xpath('//div[@class="scorebox"]/div[1]/div[1]/strong/a[@itemprop="name"]/text()').extract_first()
        home_coach = response.xpath('//div[@class="scorebox"]/div[1]/div[@class="datapoint"]/a/text()').extract_first()
        home_pts = response.xpath('//div[@class="scorebox"]/div[1]/div[@class="scores"]/div[@class="score"]/text()').extract_first()
        home_q1_pts, home_q2_pts, home_q3_pts, home_q4_pts = response.xpath(ls_path + 'tr[2]/td[3]/text()').extract_first(),\
                                                             response.xpath(ls_path + 'tr[2]/td[4]/text()').extract_first(),\
                                                             response.xpath(ls_path + 'tr[2]/td[5]/text()').extract_first(),\
                                                             response.xpath(ls_path + 'tr[2]/td[6]/text()').extract_first()
        
        away_team = response.xpath('//div[@class="scorebox"]/div[2]/div[1]/strong/a[@itemprop="name"]/text()').extract_first()
        away_coach = response.xpath('//div[@class="scorebox"]/div[2]/div[@class="datapoint"]/a/text()').extract_first()
        away_pts = response.xpath('//div[@class="scorebox"]/div[2]/div[@class="scores"]/div[@class="score"]/text()').extract_first()
        away_q1_pts, away_q2_pts, away_q3_pts, away_q4_pts = response.xpath(ls_path + 'tr[1]/td[3]/text()').extract_first(),\
                                                             response.xpath(ls_path + 'tr[1]/td[4]/text()').extract_first(),\
                                                             response.xpath(ls_path + 'tr[1]/td[5]/text()').extract_first(),\
                                                             response.xpath(ls_path + 'tr[1]/td[6]/text()').extract_first()
        
        team_codes = codes[home_team], codes[away_team]
        
        # team stats (stored in lists: list such that list[0] corresponds to home team and list[1] corresponds to away team)
        qb_kneels = [0, 0]
        qb_kneel_yds = [0, 0]
        rush_first_downs = [0, 0]
        early_down_rush_att = [0, 0]
        early_down_rush_successes = [0, 0]
        rushes_ends = [0, 0]
        qb_spikes = [0, 0]
        pass_first_downs = [0, 0]
        early_down_pass_att = [0, 0]
        early_down_pass_successes = [0, 0]
        pass_att_middle = [0, 0]
        completions_middle = [0, 0]
        short_pass_att = [0, 0]
        short_completions = [0, 0]
        deep_pass_att = [0, 0]
        deep_completions = [0, 0]
        explosive_plays = [0, 0]
        fourth_downs = [0, 0]
        kickoffs_received = [0, 0]
        fga_39 = [0, 0]
        fgm_39 = [0, 0]
        fga_40_49 = [0, 0]
        fgm_40_49 = [0, 0]
        fga_50 = [0, 0]
        fgm_50 = [0, 0]
        punts_inside_20 = [0, 0]
        off_pen_yds = [0, 0]
        def_pen_yds = [0, 0]
        drive_n = [0, 0]
        
        # off: team currently on offense. 0 represents home team on offense, 1 represents away team on offense, and -1 is unassigned
        off = -1
        clock = 5*900
        home_rz_arr, away_rz_arr = np.zeros(len(home_drives)), np.zeros(len(away_drives))
        
        # loop through all play-by-play descriptions
        for i in range(1, len(play_by_play)):
            
            quarter = play_by_play[i,0]
            if(quarter == 'OT'):
                quarter = '5'
            
            try:
                clock = self.get_seconds(play_by_play[i,1], quarter)
            except:
                pass
            
            if((clock == 3*900) | ((quarter == '5')*(play_by_play[i-1,0] == 'Quarter'))):
                off = -1
            
            down = play_by_play[i,2]
            to_go = play_by_play[i,3]
            
            try:
                description = str(play_by_play[i,5])
            except:
                description = ''
            
            play = '(no play)' not in description
            extra_pt = ' extra point ' in description
            two_pt_att = 'Two Point Attempt' in description
            field_goal = ' field goal ' in description
            kickoff = ' kicks off ' in description
            punt = ' punts ' in description
            pass_play = play*(not two_pt_att)*(' pass ' in description)
            sack = ' sacked ' in description
            complete = pass_play*(' pass complete ' in description)
            kneel = ' kneels for ' in description
            rush = play*(not extra_pt)*(not two_pt_att)*(not field_goal)*(not kickoff)*(not punt)*(not kneel)*(not sack)\
                *(' pass ' not in description)*(' for ' in description)
            
            try:
                penalty_detail = description.split('Penalty on ')[-1]
            except:
                penalty_detail = ''
                
            penalty_enforced = ('Penalty on ' in description)*((('(Declined)' not in penalty_detail)*('(declined)' not in penalty_detail)\
                                *('(Offsetting)' not in penalty_detail)*('(offsetting)' not in penalty_detail))\
                                |(('(Accepted)' in description)|('(accepted)' in description)))
            
            searching = True
            d = 0
            while(searching and (d < len(home_drives))):
                try:
                    drive_strt = self.get_seconds(home_drives[d, 2], home_drives[d, 1])
                except:
                    home_drives[d, 1] = home_drives[d - 1, 1]
                    drive_strt = self.get_seconds(home_drives[d, 2], home_drives[d, 1])
                
                if(clock <= drive_strt):
                    d += 1
                else:
                    searching = False
            drive_n[0] = d
            
            searching = True
            d = 0
            while(searching and (d < len(away_drives))):
                try:
                    drive_strt = self.get_seconds(away_drives[d, 2], away_drives[d, 1])
                except:
                    away_drives[d, 1] = away_drives[d - 1, 1]
                    drive_strt = self.get_seconds(away_drives[d, 2], away_drives[d, 1])
                
                if(clock <= drive_strt):
                    d += 1
                else:
                    searching = False
            drive_n[1] = d
            
            
            if(drive_n[0] == 0):
                off = 1
            elif(drive_n[1] == 0):
                off = 0
            elif(self.get_seconds(home_drives[drive_n[0] - 1, 2], home_drives[drive_n[0] - 1, 1]) \
               < self.get_seconds(away_drives[drive_n[1] - 1, 2], away_drives[drive_n[1] - 1, 1])):
                off = 0
            else:
                off = 1
            
            
            pen_yards = 0
            t_i = -1
            if(penalty_enforced):
                penalty_detail = description.split('Penalty on ')[-1]
                try:
                    pen_yards = int(penalty_detail.split(' yard')[0].split(' ')[-1])
                except:
                    pass
                    
                if(team_codes[0] in penalty_detail.split(' ')[0]):
                    pen_team_code = team_codes[0]
                elif(team_codes[1] in penalty_detail.split(' ')[0]):
                    pen_team_code = team_codes[1]
                else:
                    if(game_date.month < 3):
                        year = game_date.year - 1
                    else:
                        year = game_date.year 
                    
                    player_url = self.domain + str(comments).split(' id="pbp" ')[1].split('<tbody')[1].split('</tr>')[i].split('<td ')[5]\
                                    .split('<a href="')[-1].split('.htm')[0] + '/gamelog/' + str(year) + '/'
                    try:
                        pen_team_code = self.get_player_team(player_url, game_date)
                    except:
                        if(('Offensive' in penalty_detail) | ('offensive' in penalty_detail)):
                            pen_team_code = team_codes[off]
                        elif(('Defensive' in penalty_detail) | ('defensive' in penalty_detail)):
                            pen_team_code = team_codes[(-1)*off + 1]
                        else:
                            pen_team_code = 'NO TEAM'
                
                if(pen_team_code == team_codes[0]):
                    t_i = 0
                elif(pen_team_code == team_codes[1]):
                    t_i = 1
                else:
                    t_i = -1
                    
                if((off == t_i) | (play*(kickoff | punt))):
                    off_pen_yds[t_i] += pen_yards
                elif(t_i >= 0):
                    def_pen_yds[t_i] += pen_yards
            
            
            yd_line = 100
            try:
                location = play_by_play[i,4].split(' ')
                if(location[0] == team_codes[off]):
                    yd_line = int(location[1])
                else:
                    yd_line = 100 - int(location[1])
            except:
                 pass
            
            
            if(play*(drive_n[0] > 0)*(off == 0)*(100 > yd_line > 80)*(not extra_pt)*(not kickoff)*(not two_pt_att)\
               *(home_rz_arr[drive_n[0] - 1] == 0)):
                
                home_rz_arr[drive_n[0] - 1] = 1
                
            elif(play*(drive_n[1] > 0)*(off == 1)*(100 > yd_line > 80)*(not extra_pt)*(not kickoff)*(not two_pt_att)\
                 *(away_rz_arr[drive_n[1] - 1] == 0)):
                
                away_rz_arr[drive_n[1] - 1] = 1
            
            
            try:
                split_1 = description.split(' yard')[0]
                if('for no gain' in split_1):
                    yds = 0 - pen_yards*(off == t_i)
                else:
                    yds = int(split_1.split(' ')[-1]) - pen_yards*(off == t_i)
            except:
                yds = 0
            try:
                to_go = int(to_go)
            except:
                to_go = 100
            
            
            if(play*kickoff):
                if(game_date.month < 3):
                    year = game_date.year - 1
                else:
                    year = game_date.year 
                    
                player_url = self.domain + str(comments).split(' id="pbp" ')[1].split('<tbody')[1].split('</tr>')[i].split('<td ')[5]\
                                .split('<a href="')[1].split('.htm')[0] + '/gamelog/' + str(year) + '/'
                try:
                    kicking_team_code = self.get_player_team(player_url, game_date)
                except:
                    kicking_team_code = 'NO TEAM'
                    
                if(kicking_team_code == team_codes[0]):
                    kickoffs_received[1] += 1
                elif(kicking_team_code == team_codes[1]):
                    kickoffs_received[0] += 1
                
            
            qb_kneels[off] += play*kneel
            qb_kneel_yds[off] += play*kneel*yds
            rush_first_downs[off] += rush*(yds >= to_go)
            early_down_rush_att[off] += rush*(down in ['1','2'])
            early_down_rush_successes[off] += rush*(((down == '1')*(yds >= 0.4*to_go))|((down == '2')*(yds >= 0.6*to_go)))
            rushes_ends[off] += rush*(('left end' in description)|('right end' in description))
            qb_spikes[off] += play*('spiked the ball' in description)
            pass_first_downs[off] += complete*(yds >= to_go)
            early_down_pass_att[off] += pass_play*(down in ['1','2'])
            early_down_pass_successes[off] += complete*(((down == '1')*(yds >= 0.4*to_go))|((down == '2')*(yds >= 0.6*to_go)))
            pass_att_middle[off] += pass_play*(('short middle' in description)|('deep middle' in description))
            completions_middle[off] += complete*(('short middle' in description)|('deep middle' in description))
            short_pass_att[off] += pass_play*(('short right' in description)|('short middle' in description)|('short left' in description))
            short_completions[off]+=complete*(('short right' in description)|('short middle' in description)|('short left' in description))
            deep_pass_att[off] += pass_play*(('deep right' in description)|('deep middle' in description)|('deep left' in description))
            deep_completions[off] += complete*(('deep right' in description)|('deep middle' in description)|('deep left' in description))
            explosive_plays[off] += (rush*((down in ['1','2'])|(yds >= to_go))*(yds >= 12))\
                                      |(complete*((down in ['1','2'])|(yds >= to_go))*(yds >= 16))
            fourth_downs[off] += play*(down == '4')
            fga_39[off] += play*field_goal*(yds > 0)*(yds <= 39)
            fgm_39[off] += play*field_goal*(yds > 0)*(yds <= 39)*('field goal good' in description)
            fga_40_49[off] += play*field_goal*(yds >= 40)*(yds <= 49)
            fgm_40_49[off] += play*field_goal*(yds >= 40)*(yds <= 49)*('field goal good' in description)
            fga_50[off] += play*field_goal*(yds >= 50)
            fgm_50[off] += play*field_goal*(yds >= 50)*('field goal good' in description)
            punts_inside_20[off] += play*punt*((yd_line + yds) > 80)*('touchback' not in description)
            
            
 

        date = game_date.strftime("%Y-%m-%d")
        home_rush_yds = int(team_stats[np.where(team_stats[:,0] == 'Rush-Yds-TDs')[0][0]][2].split('-')[1]) - qb_kneel_yds[0]
        away_rush_yds = int(team_stats[np.where(team_stats[:,0] == 'Rush-Yds-TDs')[0][0]][1].split('-')[1]) - qb_kneel_yds[1]
        home_rush_plays = int(team_stats[np.where(team_stats[:,0] == 'Rush-Yds-TDs')[0][0]][2].split('-')[0]) - qb_kneels[0]
        away_rush_plays = int(team_stats[np.where(team_stats[:,0] == 'Rush-Yds-TDs')[0][0]][1].split('-')[0]) - qb_kneels[1]
        home_rush_tds = int(team_stats[np.where(team_stats[:,0] == 'Rush-Yds-TDs')[0][0]][2].split('-')[2])
        away_rush_tds = int(team_stats[np.where(team_stats[:,0] == 'Rush-Yds-TDs')[0][0]][1].split('-')[2])
        home_sacks_taken = int(team_stats[np.where(team_stats[:,0] == 'Sacked-Yards')[0][0]][2].split('-')[0])
        away_sacks_taken = int(team_stats[np.where(team_stats[:,0] == 'Sacked-Yards')[0][0]][1].split('-')[0])
        home_sack_yds_taken = int(team_stats[np.where(team_stats[:,0] == 'Sacked-Yards')[0][0]][2].split('-')[1])
        away_sack_yds_taken = int(team_stats[np.where(team_stats[:,0] == 'Sacked-Yards')[0][0]][1].split('-')[1])
        home_gross_pass_yds = int(team_stats[np.where(team_stats[:,0] == 'Cmp-Att-Yd-TD-INT')[0][0]][2].split('-')[2])
        away_gross_pass_yds = int(team_stats[np.where(team_stats[:,0] == 'Cmp-Att-Yd-TD-INT')[0][0]][1].split('-')[2])
        home_pass_att = int(team_stats[np.where(team_stats[:,0] == 'Cmp-Att-Yd-TD-INT')[0][0]][2].split('-')[1]) - qb_spikes[0]
        away_pass_att = int(team_stats[np.where(team_stats[:,0] == 'Cmp-Att-Yd-TD-INT')[0][0]][1].split('-')[1]) - qb_spikes[1]
        home_pass_compl = int(team_stats[np.where(team_stats[:,0] == 'Cmp-Att-Yd-TD-INT')[0][0]][2].split('-')[0])
        away_pass_compl = int(team_stats[np.where(team_stats[:,0] == 'Cmp-Att-Yd-TD-INT')[0][0]][1].split('-')[0])
        home_pass_tds = int(team_stats[np.where(team_stats[:,0] == 'Cmp-Att-Yd-TD-INT')[0][0]][2].split('-')[3])
        away_pass_tds = int(team_stats[np.where(team_stats[:,0] == 'Cmp-Att-Yd-TD-INT')[0][0]][1].split('-')[3])
        home_ints_thrown = int(team_stats[np.where(team_stats[:,0] == 'Cmp-Att-Yd-TD-INT')[0][0]][2].split('-')[4])
        away_ints_thrown = int(team_stats[np.where(team_stats[:,0] == 'Cmp-Att-Yd-TD-INT')[0][0]][1].split('-')[4])
        home_third_down_att = int(team_stats[np.where(team_stats[:,0] == 'Third Down Conv.')[0][0]][2].split('-')[1])
        away_third_down_att = int(team_stats[np.where(team_stats[:,0] == 'Third Down Conv.')[0][0]][1].split('-')[1])
        home_third_down_suc = int(team_stats[np.where(team_stats[:,0] == 'Third Down Conv.')[0][0]][2].split('-')[0])
        away_third_down_suc = int(team_stats[np.where(team_stats[:,0] == 'Third Down Conv.')[0][0]][1].split('-')[0])
        home_fourth_down_att = int(team_stats[np.where(team_stats[:,0] == 'Fourth Down Conv.')[0][0]][2].split('-')[1])
        away_fourth_down_att = int(team_stats[np.where(team_stats[:,0] == 'Fourth Down Conv.')[0][0]][1].split('-')[1])
        home_fourth_down_suc = int(team_stats[np.where(team_stats[:,0] == 'Fourth Down Conv.')[0][0]][2].split('-')[0])
        away_fourth_down_suc = int(team_stats[np.where(team_stats[:,0] == 'Fourth Down Conv.')[0][0]][1].split('-')[0])
        home_fumbles_lost = int(team_stats[np.where(team_stats[:,0] == 'Fumbles-Lost')[0][0]][2].split('-')[1])
        away_fumbles_lost = int(team_stats[np.where(team_stats[:,0] == 'Fumbles-Lost')[0][0]][1].split('-')[1])
        home_turnovers = int(team_stats[np.where(team_stats[:,0] == 'Turnovers')[0][0]][2])
        away_turnovers = int(team_stats[np.where(team_stats[:,0] == 'Turnovers')[0][0]][1])
        
        try:
            sep = np.where(kicking_punting[:,0] == 'Player')[0][0]
            if(kicking_punting[0,1] == team_codes[1]):
                away_punt_arr = kicking_punting[:sep-1]
                home_punt_arr = kicking_punting[sep+1:]
            else:
                away_punt_arr = kicking_punting[sep+1:]
                home_punt_arr = kicking_punting[:sep-1]
        except:
            if(kicking_punting[0,1] == team_codes[1]):
                home_punt_arr = np.zeros((1,10))
                away_punt_arr = kicking_punting
            else:
                away_punt_arr = np.zeros((1,10))
                home_punt_arr = kicking_punting
                
        inds = [6,7]
        for a in range(len(home_punt_arr)):
            for b in inds:
                try:
                    x = int(home_punt_arr[a,b])
                except:
                    home_punt_arr[a,b] = '0'
        for a in range(len(away_punt_arr)):
            for b in inds:
                try:
                    x = int(away_punt_arr[a,b])
                except:
                    away_punt_arr[a,b] = '0'
            
        home_punts = sum([int(home_punt_arr[i,6]) for i in range(len(home_punt_arr))])
        away_punts = sum([int(away_punt_arr[i,6]) for i in range(len(away_punt_arr))])
        home_punt_yds = sum([int(home_punt_arr[i,7]) for i in range(len(home_punt_arr))])
        away_punt_yds = sum([int(away_punt_arr[i,7]) for i in range(len(away_punt_arr))])
        
        try:
            sep = np.where(kick_punt_returns[:,0] == 'Player')[0][0]
            if(kick_punt_returns[0,1] == team_codes[1]):
                home_returns_arr = kick_punt_returns[sep+1:]
                away_returns_arr = kick_punt_returns[:sep-1]
            else:
                away_returns_arr = kick_punt_returns[sep+1:]
                home_returns_arr = kick_punt_returns[:sep-1]
        except:
            if(kick_punt_returns[0,1] == team_codes[1]):
                home_returns_arr = np.zeros((1,12))
                away_returns_arr = kick_punt_returns
            else:
                away_returns_arr = np.zeros((1,12))
                home_returns_arr = kick_punt_returns
        
        inds = [2,3,7,8]
        for a in range(len(home_returns_arr)):
            for b in inds:
                try:
                    x = int(home_returns_arr[a,b])
                except:
                    home_returns_arr[a,b] = '0'
        for a in range(len(away_returns_arr)):
            for b in inds:
                try:
                    x = int(away_returns_arr[a,b])
                except:
                    away_returns_arr[a,b] = '0'
        
        home_punt_returns = sum([int(home_returns_arr[i,7]) for i in range(len(home_returns_arr))])
        away_punt_returns = sum([int(away_returns_arr[i,7]) for i in range(len(away_returns_arr))])
        home_punt_return_yds = sum([int(home_returns_arr[i,8]) for i in range(len(home_returns_arr))])
        away_punt_return_yds = sum([int(away_returns_arr[i,8]) for i in range(len(away_returns_arr))])
        home_kickoff_returns = sum([int(home_returns_arr[i,2]) for i in range(len(home_returns_arr))])
        away_kickoff_returns = sum([int(away_returns_arr[i,2]) for i in range(len(away_returns_arr))])
        home_kickoff_return_yds = sum([int(home_returns_arr[i,3]) for i in range(len(home_returns_arr))])
        away_kickoff_return_yds = sum([int(away_returns_arr[i,3]) for i in range(len(away_returns_arr))])
        
        home_rz_trips = int(sum(home_rz_arr))
        away_rz_trips = int(sum(away_rz_arr))
        
        rz_tds = [0, 0]
        rz_arr = [home_rz_arr, away_rz_arr]
        drives = [home_drives, away_drives]
        poss_time = ['', '']
        avg_sfp = [0.0, 0.0]
        
        for i in range(2):
            sec = 0
            sfp = []
            for j in range(len(drives[i])):
                if(int(drives[i][j,1]) < 5):
                    t = drives[i][j,5].split(':')
                    sec += 60*int(t[0]) + int(t[1])
                try:
                    p = drives[i][j,3].split(' ')
                    if(p[0] == team_codes[i]):
                        sfp.append(int(p[1]))
                    else:
                        sfp.append(100-int(p[1]))
                except:
                    pass
                
            # poss_time: team possession time not including OT     
            poss_time[i] = sec / 60
            avg_sfp[i] = sum(sfp) / len(sfp)
            
            for j in range(len(rz_arr[i])):
                if((rz_arr[i][j] == 1)*(drives[i][j,7] == 'Touchdown')):
                    rz_tds[i] += 1
        
        # total_poss_time: team possession time including OT
        poss_row = team_stats[np.where(team_stats[:,0] == 'Time of Possession')[0][0]]
        home_total_poss_time = int(poss_row[2].split(':')[0]) + (int(poss_row[2].split(':')[1]) / 60)
        away_total_poss_time = int(poss_row[1].split(':')[0]) + (int(poss_row[1].split(':')[1]) / 60)
        
        pat_a = [0, 0]
        pat_m = [0, 0]
        two_pt_conv_att = [0, 0]
        two_pt_conv_suc = [0, 0]
        
        rows = len(response.xpath('//table[@id="scoring"]/tbody[1]').extract()[0].split('</tr>'))
        for r in range(1, rows):
            team = response.xpath('//table[@id="scoring"]/tbody[1]/tr[' + str(r) + ']/td[2]/text()').extract_first()
            desc = ''.join(response.xpath('//table[@id="scoring"]/tbody[1]/tr[' + str(r) + ']/td[3]/text()').getall())
            try:
                conv = desc.split('(')[1]
                if('kick' in conv):
                    if(team in home_team):
                        pat_a[0] += 1
                        if('failed' not in conv):
                            pat_m[0] += 1
                    elif(team in away_team):
                        pat_a[1] += 1
                        if('failed' not in conv):
                            pat_m[1] += 1
                elif(('pass' in conv)|('run' in conv)):
                    if(team in home_team):
                        two_pt_conv_att[0] += 1
                        if('failed' not in conv):
                            two_pt_conv_suc[0] += 1
                    elif(team in away_team):
                        two_pt_conv_att[1] += 1
                        if('failed' not in conv):
                            two_pt_conv_suc[1] += 1
            except:
                pass
        
        
        yield {
            'game_date': date,
            'game_time': start_time,
            'stadium': stadium,
            'weather': weather,
            'referee': referee,
            'vegas_o_u': vegas_o_u,
            'vegas_spread': vegas_spread,
            'home_team': home_team,
            'away_team': away_team,
            'home_team_code': team_codes[0],
            'away_team_code': team_codes[1],
            'home_coach': home_coach,
            'away_coach': away_coach,
            'home_pts': home_pts,
            'away_pts': away_pts,
            'home_q1_pts': home_q1_pts,
            'away_q1_pts': away_q1_pts,
            'home_q2_pts': home_q2_pts,
            'away_q2_pts': away_q2_pts,
            'home_q3_pts': home_q3_pts,
            'away_q3_pts': away_q3_pts,
            'home_q4_pts': home_q4_pts,
            'away_q4_pts': away_q4_pts,
            'home_rush_yds': home_rush_yds,
            'away_rush_yds': away_rush_yds,
            'home_rush_plays': home_rush_plays,
            'away_rush_plays': away_rush_plays,
            'home_rush_tds': home_rush_tds,
            'away_rush_tds': away_rush_tds,
            'home_rush_first_downs': rush_first_downs[0],
            'away_rush_first_downs': rush_first_downs[1],
            'home_early_down_rush_att': early_down_rush_att[0],
            'away_early_down_rush_att': early_down_rush_att[1],
            'home_early_down_rush_successes': early_down_rush_successes[0],
            'away_early_down_rush_successes': early_down_rush_successes[1],
            'home_rushes_ends': rushes_ends[0],
            'away_rushes_ends': rushes_ends[1],
            'home_gross_pass_yds': home_gross_pass_yds,
            'away_gross_pass_yds': away_gross_pass_yds,
            'home_pass_att': home_pass_att,
            'away_pass_att': away_pass_att,
            'home_pass_compl': home_pass_compl,
            'away_pass_compl': away_pass_compl,
            'home_pass_tds': home_pass_tds,
            'away_pass_tds': away_pass_tds,
            'home_ints_thrown': home_ints_thrown,
            'away_ints_thrown': away_ints_thrown,
            'home_pass_first_downs': pass_first_downs[0],
            'away_pass_first_downs': pass_first_downs[1],
            'home_sacks_taken': home_sacks_taken,
            'away_sacks_taken': away_sacks_taken,
            'home_sack_yds_taken': home_sack_yds_taken,
            'away_sack_yds_taken': away_sack_yds_taken,
            'home_early_down_pass_att': early_down_pass_att[0],
            'away_early_down_pass_att': early_down_pass_att[1],
            'home_early_down_pass_successes': early_down_pass_successes[0],
            'away_early_down_pass_successes': early_down_pass_successes[1],
            'home_pass_att_middle': pass_att_middle[0],
            'away_pass_att_middle': pass_att_middle[1],
            'home_completions_middle': completions_middle[0],
            'away_completions_middle': completions_middle[1],
            'home_short_pass_att': short_pass_att[0],
            'away_short_pass_att': short_pass_att[1],
            'home_short_completions': short_completions[0],
            'away_short_completions': short_completions[1],
            'home_deep_pass_att': deep_pass_att[0],
            'away_deep_pass_att': deep_pass_att[1],
            'home_deep_completions': deep_completions[0],
            'away_deep_completions': deep_completions[1],
            'home_explosive_plays': explosive_plays[0],
            'away_explosive_plays': explosive_plays[1],
            'home_third_down_att': home_third_down_att,
            'away_third_down_att': away_third_down_att,
            'home_third_down_suc': home_third_down_suc,
            'away_third_down_suc': away_third_down_suc,
            'home_fourth_downs': fourth_downs[0],
            'away_fourth_downs': fourth_downs[1],
            'home_fourth_down_att': home_fourth_down_att,
            'away_fourth_down_att': away_fourth_down_att,
            'home_fourth_down_suc': home_fourth_down_suc,
            'away_fourth_down_suc': away_fourth_down_suc,
            'home_2pt_att': two_pt_conv_att[0],
            'away_2pt_att': two_pt_conv_att[1],
            'home_2pt_conv_suc': two_pt_conv_suc[0],
            'away_2pt_conv_suc': two_pt_conv_suc[1],
            'home_rz_trips': home_rz_trips,
            'away_rz_trips': away_rz_trips,
            'home_rz_tds': rz_tds[0],
            'away_rz_tds': rz_tds[1],
            'home_fumbles_lost': home_fumbles_lost,
            'away_fumbles_lost': away_fumbles_lost,
            'home_turnovers': home_turnovers,
            'away_turnovers': away_turnovers,
            'home_punts': home_punts,
            'away_punts': away_punts,
            'home_punt_yds': home_punt_yds,
            'away_punt_yds': away_punt_yds,
            'home_punts_inside_20': punts_inside_20[0],
            'away_punts_inside_20': punts_inside_20[1],
            'home_punt_returns': home_punt_returns,
            'away_punt_returns': away_punt_returns,
            'home_punt_return_yds': home_punt_return_yds,
            'away_punt_return_yds': away_punt_return_yds,
            'home_kickoffs_received': kickoffs_received[0],
            'away_kickoffs_received': kickoffs_received[1],
            'home_kickoff_returns': home_kickoff_returns,
            'away_kickoff_returns': away_kickoff_returns,
            'home_kickoff_return_yds': home_kickoff_return_yds,
            'away_kickoff_return_yds': away_kickoff_return_yds,
            'home_pos_time': poss_time[0],
            'home_total_pos_time': home_total_poss_time,
            'away_pos_time': poss_time[1],
            'away_total_pos_time': away_total_poss_time,
            'home_avg_sfp': avg_sfp[0],
            'away_avg_sfp': avg_sfp[1],
            'home_pat_a': pat_a[0],
            'away_pat_a': pat_a[1],
            'home_pat_m': pat_m[0],
            'away_pat_m': pat_m[1],
            'home_fga_39': fga_39[0],
            'away_fga_39': fga_39[1],
            'home_fgm_39': fgm_39[0],
            'away_fgm_39': fgm_39[1],
            'home_fga_40_49': fga_40_49[0],
            'away_fga_40_49': fga_40_49[1],
            'home_fgm_40_49': fgm_40_49[0],
            'away_fgm_40_49': fgm_40_49[1],
            'home_fga_50': fga_50[0],
            'away_fga_50': fga_50[1],
            'home_fgm_50': fgm_50[0],
            'away_fgm_50': fgm_50[1],
            'home_off_pen_yds': off_pen_yds[0],
            'away_off_pen_yds': off_pen_yds[1],
            'home_def_pen_yds': def_pen_yds[0],
            'away_def_pen_yds': def_pen_yds[1]
        }
                                      

            
            
# class for scraping vegas line outcome trend data of specific team matchups (dating back further than main spider)    
class SpiderSpider2(scrapy.Spider):
    
    name = 'spider2'
    allowed_domains = ['pro-football-reference.com']
    start_urls = []
    handle_httpstatus_all = True
    
    domain = 'https://pro-football-reference.com/'
    
    start_year = 2003
    end_year = 2020
    
    years = np.arange(start_year, end_year + 1, 1)
    # range of weeks in season: 2000, 2003 - Present (2001 & 2002 have 20 weeks)
    week_nums = np.arange(1,22,1)
    
    # generate all week page urls and append to start_urls
    for i in range(len(week_nums)):
        start_urls.append(domain + 'years/' + str(2000) + '/week_' + str(week_nums[i]) + '.htm')
    for i in range(20):
        start_urls.append(domain + 'years/' + str(2001) + '/week_' + str(week_nums[i]) + '.htm')
        start_urls.append(domain + 'years/' + str(2002) + '/week_' + str(week_nums[i]) + '.htm')
    for i in range(len(years)):
        for j in range(len(week_nums)):
            start_urls.append(domain + 'years/' + str(years[i]) + '/week_' + str(week_nums[j]) + '.htm')
    for i in range(18):
        start_urls.append(domain + 'years/' + str(2021) + '/week_' + str(week_nums[i]) + '.htm')
        
    def parse(self, response):
    # main parse function: create requests from each week page
        games = response.xpath('//div[@class="game_summaries"]/div[@class="game_summary expanded nohover"]')
        for g in games:
            game_url = self.domain + g.xpath('.//table[@class="teams"]/tbody/tr/td[@class="right gamelink"]/a/@href').extract_first()
            yield scrapy.Request(url=game_url, callback=self.parse_game)
            
    def parse_game(self, response):
    # parse data on each game page
    
        # extract data from page tables into arrays
        soup = BeautifulSoup(response.text, 'html.parser')
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        tables = []
        for c in comments:
            if 'table' in c:
                try:
                    tables.append(pd.read_html(c)[0])
                except:
                    pass
                
        game_info = tables[1].to_numpy()
        
        box_path = '//div[@class="scorebox_meta"]/'
        
        game_date = datetime.strptime(response.xpath(box_path + 'div[1]/text()').extract_first(), '%A %b %d, %Y').strftime("%Y-%m-%d")
        vegas_o_u = game_info[np.where(game_info[:,0] == 'Over/Under')[0][0]][1].split(' ')[0]
        vegas_spread = game_info[np.where(game_info[:,0] == 'Vegas Line')[0][0]][1]
        home_team = response.xpath('//div[@class="scorebox"]/div[1]/div[1]/strong/a[@itemprop="name"]/text()').extract_first()
        away_team = response.xpath('//div[@class="scorebox"]/div[2]/div[1]/strong/a[@itemprop="name"]/text()').extract_first()
        team_codes = codes[home_team], codes[away_team]
        home_pts = response.xpath('//div[@class="scorebox"]/div[1]/div[@class="scores"]/div[@class="score"]/text()').extract_first()
        away_pts = response.xpath('//div[@class="scorebox"]/div[2]/div[@class="scores"]/div[@class="score"]/text()').extract_first()
        
        yield {
            'game_date': game_date,
            'home_team': home_team,
            'away_team': away_team,
            'home_team_code': team_codes[0],
            'away_team_code': team_codes[1],
            'home_pts': home_pts,
            'away_pts': away_pts,
            'vegas_o_u': vegas_o_u,
            'vegas_spread': vegas_spread
        }
    
     
