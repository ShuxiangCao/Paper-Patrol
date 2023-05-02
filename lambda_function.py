import os
import json
import requests
from datetime import timedelta, date, datetime
from typing import List, Dict, Union, Any

import arxiv
import openai

# Set OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')


def obtain_latest_papers(category: str = 'quant-ph', max_results: int = 100) -> List[arxiv.Result]:
    """
    Obtain a list of the latest papers from arXiv in the given category.

    :param category: The category to search for papers, defaults to 'quant-ph'.
    :param max_results: The maximum number of papers to return, defaults to 100.
    :return: A list of arxiv.Result objects containing information about the latest papers.
    """
    # Get the latest 100 papers, ordered by submission date
    search = arxiv.Search(
        query=f"cat:{category}",
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    results = [x for x in search.results()]
    latest_date = date.today() - timedelta(days=1)

    # Create a list to store papers submitted on the same date as the first paper
    same_day_papers = []

    # Iterate over all the returned papers
    for paper in results:
        # Parse the submission date of the paper
        submission_date = paper.published.date()

        # Check if the submission date matches the latest_date
        if submission_date == latest_date:
            # If it does, add the paper to the same_day_papers list
            same_day_papers.append(paper)

    return same_day_papers


def get_gpt_reply(message: str) -> str:
    """
    Get a GPT-3.5-turbo reply for the given message.

    :param message: The message to get a reply for.
    :return: The GPT-3.5-turbo reply as a string.
    """
    message = [{"role": "user", "content": message}]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=1000,
        temperature=0,
        messages=message
    )

    return response['choices'][0]['message']['content']


def ask_gpt(title: str, abstract: str) -> Dict[str, Union[str, List[str]]]:
    """
    Ask GPT to read the title and abstract of a paper and answer some questions about it.

    :param title: The title of the paper.
    :param abstract: The abstract of the paper.
    :return: A dictionary containing the GPT answers.
    """
    prompt = f"""
    Can you read the following title and abstract of an academic paper, and tell me the following questions? \
    If a question is not applicable, return null.
    
    - Type: Is this work mainly focused on theoretical proposals (including quantum algorithms) or actual quantum\
     hardware experiments? Return 'Theory' or 'Experiment'.
    - Platform: If it is an experiment result, what type of hardware is the experiment implemented with? Return\
     'Superconducting circuits', 'Spin qubits', 'Ion trap', 'Photonics', or 'Others:<The type of the hardware>'.
    - Topic: If it is about a quantum algorithm, does it fall into the following categories? Return category \
    'Error-correction', 'Fault-tolerated quantum algorithms', 'Near-term quantum algorithms', or\
     'Others:<A category within two words>'.
    - Summary: Write a one-sentence summary about this work.
    
    Title: {title}
    Abstract: {abstract}
    
    Return your answer in JSON format.
    """

    result = get_gpt_reply(prompt)
    result = json.loads(result)
    return result


def post_message_to_slack(fields: Dict[str, Any], channel: str) -> requests.Response:
    """
    Post a message to a Slack channel.
    :param fields: A dictionary containing the information to post.
    :param channel: The name of the Slack channel to post the message to.
    :return: A requests.Response object containing information about the POST request.
    """

    if channel == 'bottest':
        web_hook = 'https://hooks.slack.com/services/<your-url>'
    elif channel == 'journal_hub':
        web_hook = 'https://hooks.slack.com/services/<your-url>'
    elif channel == 'theory':
        web_hook = 'https://hooks.slack.com/services/<your-url>'

    resp = requests.post(
        web_hook,
        json.dumps(fields)
    )

    return resp


def generate_slack_message_block(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    Structure a paper into a dictionary containing blocks for slack.
    :param paper: A dictionary containing information about the paper.
    :return: A dictionary containing the structured blocks for slack.
    """

    blocks = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": paper['title'],
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{paper['Type']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Platform:*\n{paper['Platform']}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Topic:*\n{paper['Topic']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*URL:*\n{paper['url']}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{paper['Summary']}"
                },
            }
        ]
    }
    return blocks


def run() -> None:
    """
    Main function to run the script.
    """

    latest_papers = obtain_latest_papers()
    papers_with_annotation = []

    for paper in latest_papers:
        annotation = ask_gpt(paper.title, paper.summary)
        annotation.update({
            'title': paper.title,
            'authors': ", ".join([x.name for x in paper.authors]),
            'abstract': paper.summary,
            'url': f'{paper.entry_id}'
        })
        papers_with_annotation.append(annotation)

        # Handle your papers here.
        if annotation['Platform'] == 'Superconducting circuits':
            blocks = generate_slack_message_block(annotation)
            post_message_to_slack(fields=blocks, channel='journal_hub')
        elif annotation['Type'] == 'Experiment':
            pass
        else:
            blocks = generate_slack_message_block(annotation)
            post_message_to_slack(fields=blocks, channel='theory')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, str]:
    """
    AWS Lambda handler function to run the script.

    :param event: A dictionary containing information about the triggering event.
    :param context: A context object containing information about the runtime.
    :return: A dictionary containing the status of the execution.
    """

    try:
        run()
    except Exception as e:
        return {"status": False, "error": str(e)}

    return {"status": 'True'}
