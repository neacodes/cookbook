#! /usr/bin/env python
import json
from typing import Dict, Any
import mimetypes
import os
import requests
import yaml

# Load the YAML file
def load_yaml_file(file_path: str) -> Dict[str, Any]:
    print(f"Loading Agent Runtime Bundle: {file_path}")
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)  # type: Dict[str, Any]
    return data

def read_binary_file(file_path: str) -> bytes:
    with open(file_path, 'rb') as file:  # Note the 'rb' mode for binary files
        content = file.read()  # Read the entire file into a bytes object
    return content

def read_text_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        content = file.read()  # Read the entire file into a single string
    return content


def get_mime_type(file_path: str) -> str:
    if file_path.endswith(".md"):
        return "text/plain"
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type if mime_type is not None else 'application/octet-stream'


def deploy_agent(agent: dict):
    print(f"Deploying agent: {agent['name']}")

    print(f"Loading runbook/system prompt: {agent['system-prompt']}")
    system_prompt = read_text_file(agent["system-prompt"])

    print(f"Loading retrieval prompt: {agent['retrieval-prompt']}")
    retrieval_prompt = read_text_file(agent["retrieval-prompt"])

    tools = []
    if "tools" in agent:
        for t in agent["tools"]:
            print(f"Adding tool: {t}")
            tools.append({"config": { "name": t.title() }, "type": t})

    jsn = {
        "name": agent["name"],
        "config": {
            "configurable": {
                "type==agent/retrieval_description": retrieval_prompt,
                "type==agent/agent_type": agent["model"],
                "type==agent/system_message": system_prompt,
                "type==agent/tools": tools,
                "type": "agent",
                "type==agent/interrupt_before_action": False,
                "type==agent/description": agent["description"],
            }
        }
    }

    resp = requests.post('http://localhost:8100/assistants', json=jsn)
    assistant = json.loads(resp.content)
    assistant_id = assistant["assistant_id"]
    # print(assistant)

    if "files" in agent:
        print(f"Uploading files for agent: {agent['name']}")

        for file_path in agent["files"]:
            # Get the filename
            filename = os.path.basename(file_path)
            print(f"Uploading file: {filename}")
            # Guess the MIME type of the file or use 'application/octet-stream' if unknown
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            # Open the file in binary mode and add to the files dictionary
            files = {
                'files': (filename, open(file_path, 'rb'), mime_type)
            }

            config = {
                'configurable': {
                    # RAG files can be attached to thread or assistants, but not both
                    # 'thread_id': thread['thread_id'],
                    'assistant_id': assistant_id,
                }
            }

            config = {"config": json.dumps(config)}

            response = requests.post('http://localhost:8100/ingest', files=files, data=config,
                                     headers={'accept': 'application/json'})
            # print(response.content)



def main():

    bundle = load_yaml_file("runbook_tutor.yml")["s4d-bundle"]
    agent_count = len(bundle["agents"])
    print(f"Found {agent_count} agents to deploy.")
    for agent in bundle["agents"]:
        deploy_agent(agent["agent"])



if __name__ == "__main__":
    main()