from flask import Flask, request, redirect, url_for, session, jsonify, send_file
import requests
import os
import subprocess
import tempfile
import base64 # Added for base64 decoding

app = Flask(__name__, static_folder='frontend', static_url_path='')

# You will need to replace these with your actual GitHub OAuth App credentials
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "YOUR_GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "YOUR_GITHUB_CLIENT_SECRET")
SECRET_KEY = os.environ.get("SECRET_KEY", "a_strong_secret_key")
app.secret_key = SECRET_KEY

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/login/github")
def github_login():
    github_auth_url = f"{GITHUB_AUTH_URL}?client_id={GITHUB_CLIENT_ID}&scope=repo"
    return redirect(github_auth_url)

@app.route("/login/github/authorized")
def github_authorized():
    code = request.args.get("code")
    if not code:
        return "Authorization failed.", 400

    response = requests.post(
        GITHUB_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
        },
    )
    response_json = response.json()
    access_token = response_json.get("access_token")

    if not access_token:
        return "Failed to get access token.", 400

    session["access_token"] = access_token
    return redirect(url_for("index"))

@app.route("/api/user")
def get_user():
    if "access_token" not in session:
        return jsonify({"logged_in": False})

    headers = {"Authorization": f"token {session['access_token']}"}
    response = requests.get(f"{GITHUB_API_URL}/user", headers=headers)

    if response.status_code != 200:
        return jsonify({"logged_in": False})

    user_data = response.json()
    return jsonify({
        "logged_in": True,
        "username": user_data.get("login"),
        "avatar_url": user_data.get("avatar_url"),
    })

@app.route("/check", methods=["POST"])
def check_code():
    data = request.get_json()
    code = data.get("code")

    if not code:
        return "No code provided.", 400

    # Create a temporary file to hold the user's code
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as tmp_file:
        tmp_file.write(code)
        tmp_file_path = tmp_file.name
    # os.chmod(tmp_file_path, 0o755) # Removed unnecessary chmod

    try:
        # CORRECTED: Run simple_checker.py, passing it the command to execute (python3 {user's code file})
        process = subprocess.run(
            [
                "python3", 
                "simple_checker.py", 
                "python3", 
                tmp_file_path
            ],
            capture_output=True,
            text=True,
            check=True
        )
        report = f"# Simple Checker Report\n\n## Output\n\n```\n{process.stdout}\n```"
    except subprocess.CalledProcessError as e:
        # Include both stdout and stderr on error
        report = f"# Simple Checker Report\n\n## Error\n\n```\n{e.stderr}\n```\n\n## STDOUT (before error)\n\n```\n{e.stdout}\n```"
    finally:
        os.remove(tmp_file_path)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as tmp_report:
        tmp_report.write(report)
        tmp_report_path = tmp_report.name

    return send_file(tmp_report_path, as_attachment=True, download_name="report.md", mimetype="text/markdown")

@app.route("/logout")
def logout():
    session.pop("access_token", None)
    return redirect(url_for("index"))

@app.route("/api/repos")
def get_repos():
    if "access_token" not in session:
        return jsonify([]), 401

    headers = {"Authorization": f"token {session['access_token']}"}
    response = requests.get(f"{GITHUB_API_URL}/user/repos", headers=headers)

    if response.status_code != 200:
        return jsonify([]), response.status_code

    repos = response.json()
    return jsonify([{"full_name": repo["full_name"]} for repo in repos])

@app.route("/api/repos/<owner>/<repo>/contents")
def get_repo_contents(owner, repo):
    if "access_token" not in session:
        return jsonify([]), 401

    headers = {"Authorization": f"token {session['access_token']}"}
    path = request.args.get("path", "")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{path}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify([]), response.status_code

    contents = response.json()
    return jsonify(contents)

# CORRECTED: Route to retrieve and decode base64 file content from GitHub
@app.route("/api/repos/<owner>/<repo>/contents/<path:path>")
def get_file_content(owner, repo, path):
    if "access_token" not in session:
        return jsonify({}), 401

    # Remove raw content header to get the default JSON response
    headers = {"Authorization": f"token {session['access_token']}"} 
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contents/{path}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({}), response.status_code

    file_data = response.json()
    
    # Check if content exists and is base64 encoded
    content = file_data.get('content')
    encoding = file_data.get('encoding')
    
    if content and encoding == 'base64':
        try:
            # Decode the base64 content
            decoded_content = base64.b64decode(content).decode('utf-8')
            return jsonify({"content": decoded_content}) 
        except Exception as e:
            return jsonify({"content": f"Error decoding file content: {e}"}), 500
    else:
        return jsonify({"content": f"Could not retrieve base64 content for file at {path}"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
