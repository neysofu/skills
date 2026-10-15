on run argv
    if (count of argv) is not 2 then error "Usage: open_ghostty_tab.applescript WORKTREE_PATH TAB_TITLE"
    set worktreePath to item 1 of argv
    set tabTitle to item 2 of argv
    if worktreePath does not start with "/" then error "Worktree path must be absolute."
    if tabTitle is "" then error "Tab title must not be empty."
    set worktreeFolder to POSIX file worktreePath as alias
    if not (folder of (info for worktreeFolder)) then error "Worktree path must be a directory."

    if application "Ghostty" is not running then return "skipped: Ghostty is not running"
    tell application "Ghostty"
        if (count of windows) is 0 then return "skipped: Ghostty has no open window"
        set cfg to new surface configuration
        set initial working directory of cfg to worktreePath
        set createdTab to new tab in front window with configuration cfg
        set createdID to id of createdTab
        try
            set targetTerminal to focused terminal of createdTab
            set titleApplied to perform action ("set_tab_title:" & tabTitle) on targetTerminal
            if not titleApplied then error "Ghostty did not apply the tab title."

            -- Shell integration may publish the working directory after creation.
            repeat 30 times
                set currentDirectory to working directory of targetTerminal
                if (name of createdTab) is tabTitle and currentDirectory is not "" then
                    if my sameFolder(currentDirectory, worktreeFolder) then
                        return "created: " & createdID & "; title: " & tabTitle & "; directory: " & currentDirectory
                    end if
                end if
                delay 0.1
            end repeat
            error "Could not verify the requested title and working directory."
        on error messageText number errorNumber
            error "Created Ghostty tab " & createdID & "; " & messageText & " Inspect that tab before retrying." number errorNumber
        end try
    end tell
end run

on sameFolder(directoryPath, expectedFolder)
    try
        return (POSIX file directoryPath as alias) is expectedFolder
    on error
        return false
    end try
end sameFolder
