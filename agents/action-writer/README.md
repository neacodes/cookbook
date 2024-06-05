## Action Writer Agent
Great agents rely on actions, but what happens when you can't find an action you need? This agent helps you quickly write new actions using publicly available API documentation. It makes sure you understand how to:

* Add depdendencies
* Write a function that works with our Action framework, including using Secrets to handle sensitive parameters
* Create input data
* Use VSCode to test your Action

```Help me create an action to send a message to my Vestaboard using this API: https://docs.vestaboard.com/docs/read-write-api/endpoints/```

### Example Output
To create an action that sends a message to your Vestaboard using their API, you'll need to use the POST method to the endpoint https://rw.vestaboard.com/. You can send either a plain text message or an array of arrays representing the new state of the board.

Here's how you can create a Python function with the @action annotation to achieve this. You'll also need to handle the API key securely using the Secret type.

First, add the requests package to your package.yaml:

```dependencies:
  pypi:
    - requests=2.28.1
```
Now, here's the Python function:
```
from sema4ai.actions import action, Secret
import requests
import os

@action
def send_vestaboard_message(message: str, api_key: Secret = Secret.model_validate(os.getenv('VESTABOARD_API_KEY', ''))) -> str:
    """
    Sends a message to the Vestaboard.

    Args:
        message (str): The message to send. Can be plain text or a JSON string representing an array of arrays for character codes.
        api_key (Secret): The API key for Vestaboard authentication.

    Returns:
        str: The response from the Vestaboard API.
    """
    headers = {
        'X-Vestaboard-Read-Write-Key': api_key.value,
        'Content-Type': 'application/json'
    }
    data = {'text': message}
    response = requests.post('https://rw.vestaboard.com/', headers=headers, json=data)
    return response.text
```
**Testing the Action**

To test this function, you can create a file in the "devdata" folder of your project with the following naming structure and contents:
```
input_send_vestaboard_message.json

{
    "message": "Hello World",
    "api_key": "your_api_key_here"
}
```
To run the function, use the VSCode and type in "Command" + "Shift" + "P" and choose "Sema4.ai Run Action (from Action Package)". This will run the function using the input data provided.