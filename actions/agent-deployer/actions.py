"""
Deploys an agent to desktop that will use the provided system prompt as it's Runbook.
"""

import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict

import requests
import yaml
from sema4ai.actions import action

ACTION_ROOT = Path(__file__).parent
DEVDATA = ACTION_ROOT / "devdata"
TEMPLATE = ACTION_ROOT / "template.yml"


def handle_relative_file_path(file_path: str) -> Path:
    path = Path(file_path)
    if not path.is_absolute():
        return ACTION_ROOT / file_path
    return path


# Load the YAML file
def load_yaml_file(file_path: str) -> Dict[str, Any]:
    print(f"Loading Agent Runtime Bundle: {file_path}")
    with open(handle_relative_file_path(file_path), "r") as file:
        data = yaml.safe_load(file)  # type: Dict[str, Any]
    return data


def read_binary_file(file_path: str) -> bytes:
    with open(
        handle_relative_file_path(file_path), "rb"
    ) as file:  # Note the 'rb' mode for binary files
        content = file.read()  # Read the entire file into a bytes object
    return content


def read_text_file(file_path: str) -> str:
    with open(handle_relative_file_path(file_path), "r") as file:
        content = file.read()  # Read the entire file into a single string
    return content


def get_mime_type(file_path: str) -> str:
    if file_path.endswith(".md"):
        return "text/plain"
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type if mime_type is not None else "application/octet-stream"


def deploy_agent(agent: dict, action_server_tools: list[dict] | None = None) -> str:
    print(f"Deploying agent: {agent['name']}")

    print(f"Loading runbook/system prompt: {agent['system-prompt']}")
    try:
        system_prompt = read_text_file(agent["system-prompt"])
    except (FileNotFoundError, OSError):
        system_prompt = agent["system-prompt"]

    print(f"Loading retrieval prompt: {agent['retrieval-prompt']}")
    retrieval_prompt = read_text_file(agent["retrieval-prompt"])

    tools = []
    if "tools" in agent:
        for t in agent["tools"]:
            print(f"Adding tool: {t}")
            tools.append({"config": {"name": t.title()}, "type": t, "name": t.title()})

    if action_server_tools:
        for tool in action_server_tools:
            print(f"Adding action server tool: {tool}")
            tools.append(tool)

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
        },
    }

    resp = requests.post("http://localhost:8100/assistants", json=jsn)
    assistant = json.loads(resp.content)
    assistant_id = assistant["assistant_id"]
    print(resp.content)
    # print(assistant)

    if "files" in agent:
        print(f"Uploading files for agent: {agent['name']}")

        for file_path in agent["files"]:
            # Get the filename
            filename = os.path.basename(file_path)
            print(f"Uploading file: {filename}")
            # Guess the MIME type of the file or use 'application/octet-stream' if unknown
            mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            # Open the file in binary mode and add to the files dictionary
            files = {"files": (filename, open(file_path, "rb"), mime_type)}

            config = {
                "configurable": {
                    # RAG files can be attached to thread or assistants, but not both
                    # 'thread_id': thread['thread_id'],
                    "assistant_id": assistant_id,
                }
            }

            config = {"config": json.dumps(config)}

            response = requests.post(
                "http://localhost:8100/ingest",
                files=files,
                data=config,
                headers={"accept": "application/json"},
            )
            print(response.content)

    jsn = {
        "name": "Welcome",
        "assistant_id": assistant_id,
        "starting_message": "Hi! How can I help you with today?",
    }
    resp = requests.post("http://localhost:8100/threads", json=jsn)
    print(resp.content)
    thread_id = json.loads(resp.content)["thread_id"]

    return assistant_id, thread_id


def create_action_server_config(action_name: str, port: int) -> dict:
    """
    Create the config for a tool that is a action server.
    """
    return {
        "type": "action_server_by_sema4ai",
        "name": "Action Server by Sema4.ai",
        "description": "Run AI actions with [Sema4.ai Action Server](https://github.com/Sema4AI/actions).",
        "config": {
            "url": f"http://localhost:{port}",
            "api_key": "APIKEY",
            "name": action_name,
            "isBundled": "false",
        },
    }


@action
def deploy_agent_to_desktop(
    name: str, description: str, system_prompt: str, tool_names: str
) -> str:
    """
    Deploys an agent to desktop that will use the provided system prompt as it's Runbook.

    Args:
        name: The name of the agent to deploy.
        description: The description of the agent to deploy.
        system_prompt: The system prompt to use for the agent.
        tool_names: The names of the tools to use for the agent as a JSON string representation of
            a list of dictionaries with the example form:

            ```
            [
                {
                    "tool_name": "Dummy Tool",
                    "port": 8101
                },
                {
                    ...
                }
            ]
            ```

    Returns:
        The assistant ID of the deployed agent.
    """
    bundle = load_yaml_file(TEMPLATE)["s4d-bundle"]
    agent_to_deploy = bundle["agents"][0]["agent"]
    agent_to_deploy["name"] = name
    agent_to_deploy["description"] = description
    agent_to_deploy["system-prompt"] = system_prompt
    tools = []
    for tool in json.loads(tool_names):
        tools.append(create_action_server_config(tool["name"], tool["port"]))
    agent_to_deploy["tools"] = tools
    assistant_id, thread_id = deploy_agent(agent_to_deploy)

    out = {
        "assistant_id": assistant_id,
        "thread_id": thread_id,
    }
    return repr(out)
