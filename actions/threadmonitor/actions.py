from sema4ai.actions import action
import requests
from datetime import datetime
import json

@action
def get_latest_thread() -> str:
    """
    Gets the latest thread of an agent.

    Returns:
        The content of the thread.
    """

    assistant_id = "8a9fba54-b3f7-4791-aa47-947d3c938775"

    resp = requests.get('http://127.0.0.1:8100/threads/')
    threads = resp.json()

    # Filter threads for the given assistant
    assistant_threads = [thread for thread in threads if thread['assistant_id'] == assistant_id]

    if assistant_threads:
        # Convert the 'updated_at' string to a datetime object for comparison
        for thread in assistant_threads:
            thread['updated_at'] = datetime.fromisoformat(thread['updated_at'].replace('Z', '+00:00'))

        # Find the thread with the latest 'updated_at' timestamp
        latest_thread = max(assistant_threads, key=lambda thread: thread['updated_at'])

        thread_id = latest_thread['thread_id']
        print(f"Thread we are looking at is: {thread_id}")

        resp = requests.get(f'http://127.0.0.1:8100/threads/{thread_id}/history')
        json_data = json.loads(resp.content)

        # Extract messages
        messages = json_data[0]['values']['messages']
        # Initialize summary string
        summary = []

        print(messages)

        # Process messages
        for message in messages:
            if message['type'] == 'ai' and not message['tool_calls']:
                summary.append(f"AI: {message['content']}")
            elif message['type'] == 'human':
                summary.append(f"Human: {message['content']}")
            elif message['type'] == 'tool':
                summary.append(f"Tool: {message['name']}\n  Response: {message['content'][:100]}")

        # Join summary into a single string
        summary_string = "\n\n".join(summary)

        # Print summary string
        return summary_string
    else:
        return "Did not find threads"

@action
def get_all_agents() -> str:
    """
    Gets all agent ids available.
    
    Returns:
        List of agent names and their ids.
    """

    resp = requests.get('http://127.0.0.1:8100/assistants/')
    agents = resp.json()

    agent_info = ""
    for agent in agents:
        agent_info += f"Name: {agent['name']}, ID: {agent['assistant_id']}\n"

    return f"Available agents are:\n{agent_info}"