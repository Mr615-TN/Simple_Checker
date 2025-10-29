document.addEventListener("DOMContentLoaded", () => {
    const checkButton = document.getElementById("check-button");
    const codeInput = document.getElementById("code-input");
    const userInfo = document.getElementById("user-info");
    const repoBrowser = document.getElementById("repo-browser");

    fetch("/api/user")
        .then(response => response.json())
        .then(data => {
            if (data.logged_in) {
                userInfo.innerHTML = `
                    <div class="d-flex align-items-center">
                        <img src="${data.avatar_url}" alt="avatar" width="40" height="40" class="rounded-circle me-2">
                        <span class="me-3">${data.username}</span>
                        <button id="logout-button" class="btn btn-secondary">Logout</button>
                    </div>
                `;
                repoBrowser.style.display = "block";
                loadRepos();

                document.getElementById("logout-button").addEventListener("click", () => {
                    fetch("/logout").then(() => window.location.reload());
                });

            } else {
                userInfo.innerHTML = '<a href="/login/github" class="btn btn-primary">Login with GitHub</a>';
            }
        });

    checkButton.addEventListener("click", () => {
        const code = codeInput.value;
        if (!code) {
            alert("Please enter some code to check.");
            return;
        }

        fetch("/check", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ code: code })
        })
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error("Something went wrong.");
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = url;
            a.download = "report.md";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Error checking code.");
        });
    });

    function loadRepos() {
        const repoList = document.getElementById("repo-list");

        fetch("/api/repos")
            .then(response => response.json())
            .then(repos => {
                repoList.innerHTML = "";
                repos.forEach(repo => {
                    const li = document.createElement("li");
                    li.textContent = repo.full_name;
                    li.style.cursor = "pointer";
                    li.addEventListener("click", () => {
                        const [owner, repoName] = repo.full_name.split("/");
                        document.getElementById("current-repo").textContent = repo.full_name;
                        loadFiles(owner, repoName, "");
                    });
                    repoList.appendChild(li);
                });
            });
    }

    function loadFiles(owner, repo, path) {
        const fileList = document.getElementById("file-list");

        fetch(`/api/repos/${owner}/${repo}/contents?path=${path}`)
            .then(response => response.json())
            .then(contents => {
                fileList.innerHTML = "";
                if (path !== "") {
                    const parentLi = document.createElement("li");
                    parentLi.textContent = "../";
                    parentLi.style.cursor = "pointer";
                    parentLi.addEventListener("click", () => {
                        const parentPath = path.substring(0, path.lastIndexOf("/"));
                        loadFiles(owner, repo, parentPath);
                    });
                    fileList.appendChild(parentLi);
                }

                contents.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = item.name + (item.type === "dir" ? "/" : "");
                    li.style.cursor = "pointer";
                    li.addEventListener("click", () => {
                        if (item.type === "dir") {
                            loadFiles(owner, repo, item.path);
                        } else {
                            fetch(`/api/repos/${owner}/${repo}/contents/${item.path}`)
                                .then(response => response.json())
                                .then(data => {
                                    codeInput.value = data.content;
                                });
                        }
                    });
                    fileList.appendChild(li);
                });
            });
    }
});
