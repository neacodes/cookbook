import requests
def main():
    resp = requests.post('http://127.0.0.1:8100/assistants', json={
      "name" : "My Runbook Tutor",
      "config" : {
        "configurable" : {
          "type==agent/retrieval_description" : "Can be used to look up information that was uploaded to this assistant.\nIf the user is referencing particular files, that is often a good hint that information may be here.\nIf the user asks a vague question, they are likely meaning to look up info from this retriever, and you should call it!",
          "type==agent/agent_type" : "GPT 4 Turbo",
          "type==agent/system_message" : "This is the system prompt.",
          "type==agent/tools" : [
            {
              "config": {
                "name": "Retrieval"
              },
              "type": "retrieval",
              # "name": "Retrieval",
              # "description": "Look up information in uploaded files."
            }
          ],
          "type" : "agent",
          "type==agent/interrupt_before_action" : False,
          "type==agent/description" : "This is the description"
        }
      }
    })




if __name__ == "__main__":
    main()