"""
This action package is used by the Runbook Tutor to retrieve available actions from the Sema4
Desktop action servers. The returned actions will include their names and descriptions, but will
exclude actions used by the Runbook Tutor itself.
"""

import json
import os
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sema4ai.actions import action

ACTION_ROOT = Path(__file__).parent
DEVDATA = ACTION_ROOT / "devdata"
load_dotenv(DEVDATA / ".env")

SEMA4_DESKTOPHOME = os.environ["SEMA4AIDESKTOP_HOME"]


class ActionPackage(BaseModel):
    name: Annotated[str, Field(description="The name of the action.")]
    api_spec: Annotated[
        dict,
        Field(
            description="The API specification of the action "
            "retrieved from the action server."
        ),
    ]


class ActionPackages(BaseModel):
    actions: Annotated[
        list[ActionPackage],
        Field(
            description="A list of actions available on the Sema4 Desktop action servers."
        ),
    ]


class InternalActionPackages(BaseModel):
    names: Annotated[list[str], Field(description="The names of the internal actions.")]


HARDCODED_INTERNAL_ACTIONS = InternalActionPackages(
    names=[
        "Sema4 Desktop Action Getter",
        "Thread Monitor",
        "Agent Deployer",
        "Retreival",
    ]
)


@action
def get_actions(internal_actions: InternalActionPackages) -> ActionPackages:
    """
    Retrieve available actions from the Sema4 Desktop action servers. The returned actions will
    include their names, descriptns and full OpenAI tool specification. You can exclude
    certain actions from the return by passing them as internal actions.

    Args:
        internal_actions: A list of actions to exclude from the return.

    Returns:
        A list of actions available on the Sema4 Desktop action servers.
    """
    with open(f"{SEMA4_DESKTOPHOME}/config.json") as f:
        config = json.loads(f.read())
    actions = []
    for action_mapping in config["ActionPackageMapping"]:
        action_path = action_mapping["path"]
        with open(f"{action_path}/metadata.json") as f:
            api_spec = json.loads(f.read())
        if action_mapping["name"] in internal_actions.names:
            continue
        actions.append(
            ActionPackage(
                name=action_mapping["name"],
                api_spec=api_spec,
            )
        )
    return ActionPackages(actions=actions)
