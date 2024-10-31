import os
import re
import json
import subprocess

from utils import clone_repo, detect_extension, convert_diff_section_to_snapshot, check_language, snapshot2file, find_code_structure

def extract_hunks(commit_url: str):
    """
    Given commit url, extract edit hunks from the commit, with its file path and code logic path
    
    Args:
        commit_url: str, the url of the commit
        
    Returns:
        TBD
    """
    commit_sha = commit_url.split("/")[-1]
    project_name = commit_url.split("/")[-3]
    user_name = commit_url.split("/")[-4]
    repo_path = os.path.join("./repos", project_name)
    
    # if not exist, clone to local
    if not os.path.exists("./repos"):
        os.mkdir("./repos")
    if not os.path.exists(repo_path):
        clone_repo(user_name, project_name)
    
    command = f'git -C {repo_path} diff -U10000000 {commit_sha}^ {commit_sha}'
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except:
        raise ValueError(f'1 {commit_url} Error: Error in git diff')
    git_diff_str = result.stdout
    
    file_name_matches = re.finditer(r'diff --git a/(.+) b/(.+)', git_diff_str)
    file_names = []
    for match in file_name_matches:
        before_filename = match.group(1)
        after_filename = match.group(2)
        try:
            assert before_filename == after_filename
        except:
            raise ValueError(f"{commit_url} Error: Contain edit changes file name: {before_filename} -> {after_filename}")
        file_names.append(before_filename)
    
    if detect_extension(file_names):
        raise ValueError(f'{commit_url} Error: Contain edit on non-source files')
    
    # Split into diff section, 1 section = 1 file
    diff_sections = re.findall(r'diff --git[^\n]*\n.*?(?=\ndiff --git|$)', git_diff_str, re.DOTALL)
    all_edit_num = 0
    commit_snapshots = {}
    for i, section in enumerate(diff_sections):
        # Parse file name (w/ path), make sure edit don't change file name
        file_name_match = re.match(r'diff --git a/(.+) b/(.+)', section)
        if file_name_match:
            file_name = file_name_match.group(1)
        else:
            raise ValueError(f"5 {commit_url} Error: file name contain non-ascii char")
        
        # Get the diff of the whole file
        # (if -U{number} is set large enough, a file should contain only 1 @@ -xx,xx +xx,xx @@)
        # we can only make snapshot based on the diff of the whole file
        match = re.search(r'@@[^\n]*\n(.+)', section, re.DOTALL)
        if not match:
            raise ValueError(f"4 {commit_url} Error: Edit fail to match @@ -xx,xx +xx,xx @@")
        # 匹配@@行之后的内容
        after_at_symbol_content = match.group(1)
        # form snapshot: each element:
        # type 1: list of line of code, unchanged
        # type 2: dict of edit, have key: "type", "before", "after"
        snapshot, _ = convert_diff_section_to_snapshot(after_at_symbol_content)
        
        commit_snapshots[file_name] = snapshot
        
    # extract code logic path for each hunk
    for file_path, snapshot in commit_snapshots.items():
        file_path = os.path.join(repo_path, file_path)
        for window in snapshot:
            if type(window) is list:
                continue
            # only deal with edit hunks

            line_index = window["start_at_line"]
            language = check_language(file_path)
            if window["before"] == []:
                file_content = snapshot2file(snapshot, window)
            else:
                with open(file_path, "r") as f:
                    file_content = f.read()
            logic_path = find_code_structure(file_content, line_index, language)
            window["logic_path"] = logic_path
            
    return commit_snapshots

if __name__ == "__main__":
    commit_url = "https://github.com/huggingface/transformers/commit/c17e7cde326640a135bc7236a0e41ae52471cb90"
    commit_snapshots = extract_hunks(commit_url)
    with open("commit_snapshots.json", "w") as f:
        json.dump(commit_snapshots, f, indent=4)