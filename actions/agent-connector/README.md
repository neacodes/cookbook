In Sema4.ai Desktop, let your agents talk to each other seamlessly.

## Overview

The Agent Connector allows agents within the Sema4.ai platform to communicate with each other through a simple and
intuitive interface. This connector provides actions to create communication threads and send messages between agents,
facilitating smooth and efficient inter-agent communication.

## Actions

### create_thread

Creates a new thread for communication with an existing agent.

#### Args:

- `agent_name (str)`: The name of the existing agent.
- `thread_name (str)`: The name of the thread (user-defined).

#### Returns:

- `str`: The thread ID, or an error message if the call fails.

### send_message

Sends a message within a specified thread and retrieves the assistant's response.

#### Args:

- `thread_id (str)`: The ID of the thread.
- `message (str)`: The message content.

#### Returns:

- `str`: The assistant's response, or error message if the call fails.

## How It Works

1. **Creating a Communication Thread**:
    - The `create_thread` action allows you to create a new thread for communication with an agent by specifying the
      agent's name and a user-defined thread name. This action internally fetches the list of available agents and
      validates the agent name before creating the thread.

2. **Sending Messages**:
    - The `send_message` action enables you to send messages within a specified thread and retrieve the assistant's
      response. This action ensures smooth communication by providing only the relevant content of the response or an
      error message if the operation fails.

By using these actions, agents within the Sema4.ai platform can effectively communicate, enabling seamless collaboration
and information exchange.In Sema4.ai Desktop let your agents talk to each other.