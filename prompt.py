import json

with open("commit_snapshots.json", "r") as f:
    commit_snapshots = json.load(f)
    
edits = []
for file_path, snapshot in commit_snapshots.items():
    for widx, window in enumerate(snapshot):
        if type(window) is list:
            continue
        prev_window = snapshot[widx-1] if widx > 0 else None
        next_window = snapshot[widx+1] if widx < len(snapshot)-1 else None
        
        if prev_window is None:
            window["prefix"] = None
        else:
            window["prefix"] = prev_window[-1 * min(5, len(prev_window)):]
        
        if next_window is None:
            window["suffix"] = None
        else:
            window["suffix"] = next_window[:min(5, len(next_window))]
        
        diff_format = ""
        diff_format += f"--- {file_path}\n+++ {file_path}\n"
        # in diff format, the line number is 1-based
        diff_format += f"@@ {window["start_at_line_parent"]-len(window["prefix"])+1},{len(window['before'])} {window["start_at_line_child"]-len(window["prefix"])+1},{len(window['after'])} @@ "
        diff_format += " -> ".join(window["logic_path"]) + "\n"
        for line in window["prefix"]:
            diff_format += f" {line}"
        for line in window["before"]:
            diff_format += f"-{line}"
        for line in window["after"]:
            diff_format += f"+{line}"
        for line in window["suffix"]:
            diff_format += f" {line}"
        
        print(diff_format)
        print("-"* 30)
        edits.append(diff_format)
        

        