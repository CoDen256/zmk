Set WshShell = CreateObject("WScript.Shell" )
WshShell.Run """C:\setup\win_layout_aou.ahk""", 0 'Must quote command if it has spaces; must escape quotes
Set WshShell = Nothing