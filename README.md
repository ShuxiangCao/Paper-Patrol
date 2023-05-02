# Paper Patrol for Quant-ph

This script fetches the latest quantum papers from arXiv, analyzes them using OpenAI's GPT-3.5-turbo, and posts the
information to specified Slack channels based on the paper's content.

## Dependencies

- arxiv (`pip install arxiv`)
- openai (`pip install openai`)
- requests (`pip install requests`)

## Usage

1. Set the `OPENAI_API_KEY` environment variable to your OpenAI API key.
2. Replace `<your-url>` in the `post_message_to_slack()` function with your Slack webhook URLs for each channel.
3. Run the `run()` function or use the `lambda_handler()` function as an AWS Lambda handler.

## Deploy to AWS

### Configure the Lambda function

Refer to https://docs.aws.amazon.com/lambda/latest/dg/getting-started.html

### Configure scheduled execution

Refer to https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/RunLambdaSchedule.html

## Functions

- `obtain_latest_papers(category: str, max_results: int) -> List[arxiv.Result]`: Fetches the latest papers from arXiv in
  the specified category.
- `get_gpt_reply(message: str) -> str`: Gets a reply from GPT-3.5-turbo for a given message.
- `ask_gpt_relation(title: str, abstract: str) -> Dict[str, Union[str, List[str]]]`: Asks GPT to analyze a paper's title
  and abstract and answer questions about its content.
- `post_message_to_slack(fields: Dict[str, Any], channel: str) -> requests.Response`: Posts a message to a specified
  Slack channel.
- `structure_paper(paper: Dict[str, Any]) -> Dict[str, Any]`: Structures a paper into a dictionary containing its
  blocks.
- `run() -> None`: Main function to run the script.
- `lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, str]`: AWS Lambda handler function to run the
  script.
