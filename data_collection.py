# Collects disaster-relevant data from various APIs, and stores it in Redis.
import os
import sys
import logging
from dotenv import load_dotenv
load_dotenv()
import json
import requests
import redis

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

nws_county_code = os.getenv("NWS_COUNTY_CODE")

# Import openai library
from openai import OpenAI
OAIclient = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

# Search the web using OpenAI for relevant disaster news
def get_disaster_news_from_openai(user_location, disaster_type="", user_message=""):
    try:
        prompt = (
            f"The user's message activating this request was: '{user_message}'. Tailor your response to any specific user request, inquiry, or circumstance."
            "Search for information about any current or ongoing emergency or disaster affecting the user's vicinity."
            f"If the user didn't provide a location, use the default of {user_location}."
            "Search for any relevant news, state or federal bulletins or announcements, curfews, evacuations, or other emergency information. "
            "If the user did not specify the disaster, be on the look out for any serious events: for example, hurricane, tornado, flooding, wildfire, earthquake, nuclear disaster, train derailment, terrorist attack, ICBM alert, cyberattack, etc. "
            "Focus on essential information that would be useful to someone lacking power or connectivity: what's happening, what to do, and any official government recommendations. "
            "If the cause or nature of the disaster is still unclear, just include the most helpful information. "
            "Non-severe weather information is not needed. "
            "If no emergency or disaster is found, simply state so."
            "Respond with a summary of the useful information, organized by source."
        )

        logger.info(f"Prompt for OpenAI: {prompt}")

        response = OAIclient.chat.completions.create(
            model="gpt-5-search-api",
            messages=[
                {"role": "system", "content": "You are providing a response as part of the back end of an emergency SMS service."},
                {"role": "user", "content": prompt}
            ]
        )

        if response.choices and response.choices[0].message and response.choices[0].message.content:
            search_response = response.choices[0].message.content.strip()
            logger.info(f"Successfully fetched news from OpenAI. Response: {search_response}")
            return search_response
        else:
            logger.info(f"No news found from OpenAI for {user_location} - {disaster_type}")
            return None

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        return None

def collect_data(user_message=None):
    nws_alerts_url = f'https://api.weather.gov/alerts/active/zone/{nws_county_code}'
    nws_forecast_url = f'https://api.weather.gov/zones/county/{nws_county_code}/forecast'
    
    apis = [
        {'name': 'NWS_alerts', 'url': nws_alerts_url},
        {'name': 'NWS_forecast', 'url': nws_forecast_url}
    ]
    user_location = os.getenv("LOCATION")

    #initialize redis
    r = redis.Redis(host='redis', port=6379, db=0)

    # Collect data from APIs
    for api in apis:
        if not api['url']:
            logger.warning(f"URL for {api['name']} is not defined. Skipping API call.")
            continue
        try:
            response = requests.get(api['url'])
            if response.status_code == 200:
                response_data = response.json()
                #remove lengthy 'geometry' key from response
                if 'geometry' in response_data:
                    response_data.pop('geometry')
                r.setex(api['name'], 86400, str(response_data))
                logger.info(f"Saved data for {api['name']}") # Removed response.json() from log for brevity
            else:
                logger.error(f"Failed to fetch data from {api['name']}: {response.status_code}")
                #existing data in redis from last successful pull will remain
        except Exception as e:
            logger.error(f"Error collecting data from {api['name']}: {str(e)}")
            #existing data in redis from last successful pull will remain

    # Call OpenAI for disaster news using specific location and disaster type.
    # The result is stored in Redis under 'websearch_disaster_news_summary' with a 1-day expiration.
    try:
        news_stories = get_disaster_news_from_openai(user_location, disaster_type="any critical events", user_message=user_message)
        if news_stories:
            r.setex('websearch_disaster_news_summary', 86400, news_stories)  
            logger.info("Successfully fetched and stored disaster news from OpenAI.")
        else:
            logger.info("No disaster news obtained from OpenAI or an error occurred")
            #existing data in redis from last successful pull will remain
    except Exception as e:
        logger.error(f"Error in getting or storing OpenAI disaster news: {str(e)}")

if __name__ == "__main__":
    #for testing this module as a standalone script
    test_msg = "What's happening? The power and internet is out."
    collect_data(test_msg)
    print("Data collection completed. Here are the keys in Redis:")
    r = redis.Redis(host='redis', port=6379, db=0)
    keys = r.keys('*')
    keys = [key.decode('utf-8') for key in keys]
    for key in keys:
        value = r.get(key)
        print(f"{key.title()}: {value.decode('utf-8')} \n\n")

# Add a flag for cron job execution
if len(sys.argv) > 1 and sys.argv[1] == '--cron':
    logger.info("Running data collection as cron job")
    collect_data()
    logger.info("Cron job data collection completed")
    sys.exit(0)
