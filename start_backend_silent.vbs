Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = Chr(34) & currentDir & "\start_backend_always_on.bat" & Chr(34)
' 0 runs the window completely hidden in background
WshShell.Run batPath, 0, False
