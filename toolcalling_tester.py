from langchain_ollama import ChatOllama
from langchain_core.tools import tool
import requests

API_KEY = "" #odds api key

@tool
def fetch_odds(team, market, bookmaker):
    """Return the specified bookmaker's odds for a given team's game.
    
    Args:
        team: The full name of an NBA team, e.g. New York Knicks.
        market: The odds market, e.g. spreads, h2h, or totals.  
        bookmaker: A sportsbook, e.g. FanDuel.
    """
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds?"
    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": market.lower(),
        "oddsFormat": "american",
        "bookmakers": bookmaker.lower()
    }
    team = team.lower()

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return f"Error from odds API: {response.text}"

    games_data = response.json()
    for game in games_data:
        if team == game["home_team"].lower() or team == game["away_team"].lower():
            for book_data in game["bookmakers"]:
                for mkt in book_data["markets"]:
                    if mkt["key"] == market:
                        for outcome in mkt["outcomes"]:
                            if outcome["name"].lower() == team:
                                return outcome["price"]

    return "Unable to fetch odds"

tools = [fetch_odds]

llm = ChatOllama(
    base_url="http://localhost:11434",  
    model="llama3.2:latest"                   
)

llm_with_tools = llm.bind_tools(tools)

query = "What is the Laker's moneyline on FanDuel"

model_output = llm_with_tools.invoke(query)
function_args = model_output.tool_calls[0]['args']

user_defined_market = function_args['market'] #use later to prompt the model

if user_defined_market == 'moneyline': #users will use moneyline, not h2h
    function_args['market'] = 'h2h'
elif user_defined_market == 'spread':
    function_args['market'] == 'spreads'

odds = fetch_odds.invoke(function_args)
#print(odds)

team_name = function_args['team']
bookmaker_name = function_args['bookmaker']

prompt = (
    f"The user asked for the {team_name}'s {user_defined_market} odds on {bookmaker_name}. "
    f"The current odds are {odds}. "
    "Respond with a sentence that tells the user the current odds."
)

final_answer = llm.invoke(prompt)

print(final_answer.content)
