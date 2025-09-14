import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join('.', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Add the project root to the Python path
sys.path.append('atlan_copilot')

from agents.classification_agent import ClassificationAgent

async def test_classification():
    # Test with one of the sample tickets
    test_ticket = {
        "subject": "How to surface sample rows and schema changes?",
        "body": "Hi, we've successfully connected our Redshift cluster, and the assets are showing up. However, my data analysts are asking how they can see sample data or recent schema changes directly within Atlan without having to go back to Redshift. Is this feature available? I feel like I'm missing something obvious."
    }

    print("Testing Classification Agent with tag definitions...")
    print(f"Subject: {test_ticket['subject']}")
    print(f"Body: {test_ticket['body'][:100]}...")

    agent = ClassificationAgent()
    if not agent.model:
        print("❌ Classification agent failed to initialize")
        return

    print("\nTag definitions loaded:")
    print(f"Raw tag_definitions: {agent.tag_definitions}")
    print(f"Topic tags: {[tag['name'] for tag in agent.tag_definitions.get('topic_tags', {}).get('tags', [])]}")
    print(f"Sentiment tags: {[tag['name'] for tag in agent.tag_definitions.get('sentiment', {}).get('tags', [])]}")
    print(f"Priority tags: {[tag['name'] for tag in agent.tag_definitions.get('priority', {}).get('tags', [])]}")

    # Test the _construct_prompt method
    print(f"\nTag definitions check: bool={bool(agent.tag_definitions)}, type={type(agent.tag_definitions)}")
    prompt = agent._construct_prompt(test_ticket['subject'], test_ticket['body'])
    print(f"Prompt result: {prompt}")
    print(f"Prompt type: {type(prompt)}")
    print(f"Prompt constructed successfully: {prompt is not None and len(prompt) > 0}")
    if prompt and len(prompt) < 500:
        print(f"Prompt: {prompt}")
    elif prompt:
        print(f"Prompt (first 500 chars): {prompt[:500]}...")

    print("\nRunning classification...")
    result = await agent.execute(test_ticket)

    print("\nClassification Result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_classification())
