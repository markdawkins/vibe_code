import requests
import getpass
import sys

# Disable SSL warnings if your company uses SSL inspection
requests.packages.urllib3.disable_warnings()

INSTANCE_URL = "https://com.service-now.com"
TABLE = "sc_req_item"

def main():
    username = input("ServiceNow username: ")
    password = getpass.getpass("ServiceNow password: ")

    url = f"{INSTANCE_URL}/api/now/table/{TABLE}"

    headers = {
        "Accept": "application/json"
    }

    # Query:
    # assigned_to = current user
    # active = true
    params = {
        "sysparm_query": "assigned_to.user_name={}".format(username),
        "sysparm_fields": "number,short_description,state,opened_at",
        "sysparm_limit": 20
    }

    try:
        response = requests.get(
            url,
            auth=(username, password),
            headers=headers,
            params=params,
            verify=False,
            timeout=15
        )
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        sys.exit(1)

    if response.status_code != 200:
        print(f"Failed to query ServiceNow: {response.status_code}")
        print(response.text)
        sys.exit(1)

    results = response.json().get("result", [])

    if not results:
        print("No assigned requests found.")
        return

    print("\nAssigned Requests:\n" + "-" * 60)
    for r in results:
        print(f"Number: {r['number']}")
        print(f"Opened: {r['opened_at']}")
        print(f"State: {r['state']}")
        print(f"Description: {r['short_description']}")
        print("-" * 60)


if __name__ == "__main__":
    main()
