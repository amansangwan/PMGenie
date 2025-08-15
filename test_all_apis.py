import requests
import json
from app.routes.ai import send_message

BASE_URL = "http://127.0.0.1:8000"

# Test credentials
TEST_EMAIL = "tester@example.com"
TEST_PASSWORD = "secret123"

def pretty(resp):
    try:
        return json.dumps(resp.json(), indent=2)
    except:
        return resp.text

def main():
    # 1. LOGIN
    print("1️⃣  Logging in...")
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    # print(pretty(r))
    assert r.status_code == 200, "Login failed"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. GET PROJECTS
    print("2️⃣  Fetching Jira projects...")
    r = requests.get(f"{BASE_URL}/projects", headers=headers)
    print(pretty(r))

    # 3. GET PROJECT DETAIL (if any project)
    projects = r.json()
    print(projects)
    if projects:
        proj_id = projects[0]["id"]
        proj_key = projects[0]["key"]

        print("3️⃣  Project detail...")
        r = requests.get(f"{BASE_URL}/projects/{proj_id}", headers=headers)
        print(pretty(r))

        print("4️⃣  Project tickets...")
        r = requests.get(f"{BASE_URL}/projects/{proj_key}/tickets", headers=headers)
        print(pretty(r))
    else:
        print("⚠️  No projects found in Jira.")




    files = {"file": ("sample.txt", open("sample.txt", "rb"), "text/plain")}
    data = {
        "projectId": proj_id,
        "chatSessionId": "session-1"
    }
    r = requests.post(
        f"{BASE_URL}/knowledge-base/upload",
        headers=headers,
        files=files,
        data=data
    )

    print("Upload KB file status:", r.status_code)
    try:
        resp_json = r.json()
        print("Response JSON:", resp_json)
        file_id = resp_json.get("file_id")
    except requests.exceptions.JSONDecodeError:
        print("Non-JSON response:", r.text)
        file_id = 1


    # # 4. UPLOAD CONTEXT FILE
    print("5️⃣  Uploading context file...")
    with open("sample.txt", "w") as f:
        f.write("This is a test context file.")
    with open("sample.txt", "rb") as f:
        files = {"file": ("sample.txt", f, "text/plain")}
        r = requests.post(f"{BASE_URL}/ai/context/upload", headers=headers, files=files)
        print(pretty(r))
        file_id = r.json()["file_id"]

    # # 5. UPLOAD KB FILE
    print("6️⃣  Uploading KB file...")
    with open("kb.txt", "w") as f:
        f.write("This is a KB file for testing.")
    with open("kb.txt", "rb") as f:
        files = {"file": ("kb.txt", f, "text/plain")}
        r = requests.post(f"{BASE_URL}/knowledge-base/upload", headers=headers, files=files)
        print(pretty(r))

    # 6. LIST KB FILES
    print("7️⃣  Listing KB files...")
    r = requests.get(f"{BASE_URL}/knowledge-base/files", headers=headers)
    print(pretty(r))

    # 7. SEND MESSAGE
    print("8️⃣  Sending AI message...")
    payload = {
        "query": "Summarize projectX progress",
        "projectId": "TESTPROJ",
        "chatSessionId": "sess1",
        "attachment_ids": [2]
    }
    # r = send_message(payload)
    r = requests.post(f"{BASE_URL}/ai/messages", headers=headers, json=payload)
    print(pretty(r))

    # # 8. GET CHAT HISTORY
    print("9️⃣  Getting chat history...")
    r = requests.get(f"{BASE_URL}/ai/messages/history", headers=headers)
    print(pretty(r))

    # # 9. SEARCH CHAT
    print("🔟  Searching chat messages...")
    r = requests.get(f"{BASE_URL}/ai/messages/search", headers=headers, params={"q": "progress"})
    print(pretty(r))

if __name__ == "__main__":
    main()
