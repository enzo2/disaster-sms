from dotenv import load_dotenv
load_dotenv()
import os
import sys
import logging
import redis
from openai import OpenAI

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

OAIclient = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
RedisClient = redis.Redis(host='redis', port=6379, db=0)

def summarize_data(user_message=None):
    prompt = {}
    
    keys = RedisClient.keys('*')  #get all keys stored in redis
    keys = [key.decode('utf-8') for key in keys]  # Decode the keys from bytes to strings
    for key in keys:
        value = RedisClient.get(key)
        if value:
            try:
                prompt[key] = value.decode('utf-8')
            except UnicodeDecodeError:
                logger.error(f"{key.title()}: Unable to decode value")
        else:
            logger.warning(f"{key.title()}: No value found")

    if user_message:
        prompt['user_message'] = user_message

    logger.info(f"Prompt: {prompt}")

    response = OAIclient.chat.completions.create(
      messages=[
        {
          "role": "system",
          "content": "Your task is to summarize the provided data to aid users in a potential emergency. The user has requested information. Your summary will be provided to users who might be disconnected from the Internet, whose only form of connectivity is MMS/SMS. Inform the user of any pertinent information that they may need to know in an emergency scenario, such as weather, government messages, breaking news. If the user provided a specific request and/or location, tailor the response accordingly and focus on locally pertinent information. Lastly, if it does seem there is an emergency, analyze the overall situation to provide tailored advice. Avoid a detailed weather forecast except for severe weather. Include the start and end date/time of any NWS alerts. Avoid generic advice--there is no need for basic reminders like keeping the fridge closed, using generators outdoors, having a med kit, etc. Ignore irrelevant information. Be as concise as possible, as your response will be sent via MMS/SMS. Don't use any line breaks."
        },
        {
            "role": "user",
            "content": str(prompt),
        }
      ],
      model="gpt-5-mini",
      max_tokens=400
    )

    summary = None
    if (
        hasattr(response, 'choices') and response.choices and
        hasattr(response.choices[0], 'message') and response.choices[0].message and
        hasattr(response.choices[0].message, 'content') and response.choices[0].message.content
    ):
        summary = response.choices[0].message.content.strip()
        logger.info(f"Response summary: {summary}")
    else:
        logger.warning("OpenAI returned no content.")

    if not summary:
        summary = "Could not retrieve a summary at this time."
        logger.warning("OpenAI returned an empty summary.")

    # Store the summary in Redis
    try:
        RedisClient.set('summary', summary)
        logger.info("Summary stored in Redis successfully")
    except Exception as e:
        logger.error(f"Error storing summary in Redis: {str(e)}")

    return summary

if __name__ == "__main__":
    #for testing this module as a standalone script
    try:
        summarize_data("Just testing!")
    except Exception as e:
        logger.error(f"Error during standalone test: {e}")

# Add a flag for cron job execution
if len(sys.argv) > 1 and sys.argv[1] == '--cron':
    logger.info("Running data summarization as cron job")
    summarize_data()
    logger.info("Cron job data summarization completed")
    sys.exit(0)
