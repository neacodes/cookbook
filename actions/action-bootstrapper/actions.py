from sema4ai.actions import action
import os
import urllib.parse
import subprocess
import socket
import requests
import black
import json


@action
def bootstrap_action_package(action_package_name: str) -> str:
    """
    This action sets up an action package in the home directory of the user under the "actions_bootstrapper" folder.

    Args:
        action_package_name: Name of the action package

    Returns:
        The full path of the bootstrapped action package.
    """
    home_directory = os.path.expanduser("~")

    new_action_package_path = os.path.join(home_directory, "actions_bootstrapper")

    os.makedirs(new_action_package_path, exist_ok=True)

    cwd = os.getcwd()
    full_action_path = ""
    try:
        os.chdir(new_action_package_path)

        command = f"action-server new --name '{action_package_name}' --template minimal"
        subprocess.run(command, shell=True)

        full_action_path = get_action_package_path(action_package_name)
    finally:
        os.chdir(cwd)

    return f"Action successfully bootstrapped! Code available at {full_action_path}"


def find_available_port(start_port: int) -> int:
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except socket.error:
                port += 1


def get_action_package_path(action_package_name: str) -> str:
    home_directory = os.path.expanduser("~")

    new_action_package_path = os.path.join(home_directory, "actions_bootstrapper")

    full_action_path = os.path.join(new_action_package_path, action_package_name)

    return full_action_path


@action
def update_action_package_dependencies(
    action_package_name: str, action_package_dependencies_code: str
) -> str:
    """
    Update the action package dependencies (package.yaml) for
    a specified action package.

    Args:
        action_package_name: The name of the action package.
        action_package_dependencies_code: The YAML content to
            write into the package.yaml file.

    Returns:
        A success message.
    """

    package_yaml_path = os.path.join(
        os.path.expanduser("~"),
        "actions_bootstrapper",
        action_package_name,
        "package.yaml",
    )

    package_yaml = open(package_yaml_path, "w")
    try:
        package_yaml.write(action_package_dependencies_code)
    finally:
        package_yaml.close()

    return f"Successfully updated the package dependencies at: {package_yaml_path}"


@action
def update_action_package_action_dev_data(
    action_package_name: str,
    action_package_action_name: str,
    action_package_dev_data: str,
) -> str:
    """
    Update the action package dev data for a specified action package.

    Args:
        action_package_name: The name of the action package.
        action_package_action_name: The name of the action for which the devdata is intended
        action_package_dev_data: The JSON content to write into the dev data for this specific action

    Returns:
        Whether the dev data was successfully updated or not.

    """

    full_action_path = get_action_package_path(action_package_name)

    dev_data_path = os.path.join(full_action_path, "devdata")

    os.makedirs(dev_data_path, exist_ok=True)

    file_name = f"input_{action_package_action_name}.json"
    file_path = os.path.join(dev_data_path, file_name)

    with open(file_path, "w") as file:
        try:
            file.write(action_package_dev_data)
        finally:
            file.close()

    return f"dev data for {action_package_action_name} in the action package {action_package_name} successfully created!"


@action
def start_action_server(action_package_name: str, secrets: str) -> str:
    """
    This action starts the bootstrapped action package.

    Args:
        action_package_name: Name of the action package
        secrets: A JSON dictionary where each key is the secret name and the value is the secret value

    Returns:
        The address of the running action package.
    """

    full_action_path = get_action_package_path(action_package_name)

    cwd = os.getcwd()
    os.chdir(full_action_path)

    start_port = 8080
    available_port = find_available_port(start_port)

    start_command = f"action-server start -p {available_port}"

    command = f"python3 -c 'import subprocess, os; subprocess.Popen(\"{start_command}\", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)'"

    env = os.environ.copy()
    env["RC_ADD_SHUTDOWN_API"] = "1"

    if secrets != "":
        parsed_secrets = json.loads(secrets)
        env.update(parsed_secrets)

    res = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
        env=env,
    )
    os.chdir(cwd)

    return f"http://localhost:{available_port}"


@action
def stop_action_server(action_server_url: str) -> str:
    """
    This action shutdowns the running action package.

    Args:
        action_server_url: URL of the running action package

    Returns:
        Whether the shutdown was successful or not
    """

    headers = {
        "Content-Type": "application/json",
    }
    response = requests.post(f"{action_server_url}/api/shutdown", headers=headers)

    if response.status_code == 200:
        return "Successfully shutdown the action server"
    else:
        print("POST request failed.")
        print("Status code:", response.status_code)
        print("Response content:", response.text)
        return "Failed to stop the action server"


@action
def update_action_code(action_package_name: str, action_code: str) -> str:
    """
    Replaces actions.py content with the provided input.

    Args:
        action_package_name: The directory for the action to update
        action_code: The source code to place into the actions.py

    Returns:
        A success message.
    """

    # Format the code using black
    formatted_code = black.format_str(action_code, mode=black.FileMode())

    actions_py_path = os.path.join(
        os.path.expanduser("~"),
        "actions_bootstrapper",
        action_package_name,
        "actions.py",
    )

    actions_py = open(actions_py_path, "w")
    try:
        actions_py.write(formatted_code)
    finally:
        actions_py.close()

    return f"Successfully updated the actions at {actions_py_path}"


@action
def open_action_code(action_package_name: str) -> str:
    """
    This action opens the code of the action package with VSCode.

    Args:
        action_package_name: Name of the action package

    Returns:
        Whether the code was successfully displayed or not
    """

    full_action_path = get_action_package_path(action_package_name)
    command = ["code", full_action_path]

    subprocess.run(command)

    return f"{action_package_name} code opened with VScode"


@action
def get_action_run_logs(action_server_url: str, run_id: str) -> str:
    """
    Returns action run logs in plain text by requesting them from the
    provided action server URL.

    Args:
        action_server_url: The URL (base path) to the action server.
        run_id: The ID of the run to fetch logs for.

    Returns:
        The plain text from the output logs of the run.
    """

    artifact = "__action_server_output.txt"

    target_url = urllib.parse.urljoin(
        action_server_url,
        f"/api/runs/{run_id}/artifacts/text-content?artifact_names={artifact}",
    )

    response = requests.get(target_url)

    payload = response.json()
    output = payload[artifact]

    return output


@action
def get_action_run_logs_latest(action_server_url: str) -> str:
    """
    Returns action run logs in plain text by requesting them from the
    provided action server URL. Requests the latest run's logs.

    Args:
        action_server_url: The URL (base path) to the action server.

    Returns:
        The plain text from the output logs of the run.
    """

    runs_list_url = urllib.parse.urljoin(action_server_url, "/api/runs")

    runs_response = requests.get(runs_list_url)
    runs_payload = runs_response.json()

    last_run = runs_payload[-1]

    return get_action_run_logs(action_server_url, last_run["id"])
