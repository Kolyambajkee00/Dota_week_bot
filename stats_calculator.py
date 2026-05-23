

def calculate_stats(matches):
    total_matches = len(matches)
    wins = 0
    radiant_games = 0
    radiant_wins = 0
    dire_games = 0
    dire_wins = 0
    total_kills = 0
    total_deaths = 0
    total_assists = 0
    heroes = {}

    for match in matches:
        player_slot = match.get('player_slot', 0)
        radiant_win = match.get('radiant_win', False)

        won = (player_slot < 128 and radiant_win) or (player_slot >= 128 and not radiant_win)
        if won:
            wins += 1

        if player_slot < 128:
            radiant_games += 1
            if won:
                radiant_wins += 1
        else:
            dire_games += 1
            if won:
                dire_wins += 1

        total_kills += match.get('kills', 0)
        total_deaths += match.get('deaths', 0)
        total_assists += match.get('assists', 0)

        hero_id = match.get('hero_id')
        if hero_id is not None:
            hero_id = int(hero_id)
            if hero_id not in heroes:
                heroes[hero_id] = {'games': 0, 'wins': 0}
            heroes[hero_id]['games'] += 1
            if won:
                heroes[hero_id]['wins'] += 1

    if total_deaths > 0:
        avg_kda = (total_kills + total_assists) / total_deaths
    else:
        avg_kda = total_kills + total_assists

    winrate = (wins / total_matches * 100) if total_matches > 0 else 0
    radiant_winrate = (radiant_wins / radiant_games * 100) if radiant_games > 0 else 0
    dire_winrate = (dire_wins / dire_games * 100) if dire_games > 0 else 0
    sorted_heroes = sorted(heroes.items(), key=lambda x: x[1]['games'], reverse=True)[:5]

    return {
        'total_matches': total_matches,
        'wins': wins,
        'winrate': round(winrate, 1),
        'radiant_games': radiant_games,
        'radiant_wins': radiant_wins,
        'radiant_winrate': round(radiant_winrate, 1),
        'dire_games': dire_games,
        'dire_wins': dire_wins,
        'dire_winrate': round(dire_winrate, 1),
        'avg_kda': round(avg_kda, 2),
        'heroes': heroes,
        'sorted_heroes': sorted_heroes
    }