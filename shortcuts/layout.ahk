#Requires AutoHotkey v2.0
#SingleInstance Force
#DllLoad "Imm32" ; for consoles compatibility, see docs.microsoft.com/en-us/windows/win32/api/imm/
; InstallKeybdHook
; KeyHistory
global imm := DllCall("GetModuleHandle", "Str","Imm32", "Ptr") ; better performance; lexikos.github.io/v2/docs/commands/DllCall.htm
global immGetDefaultIMEWnd := DllCall("GetProcAddress", "Ptr",imm, "AStr","ImmGetDefaultIMEWnd", "Ptr") ; docs.microsoft.com/en-us/windows/win32/api/imm/nf-imm-immgetdefaultimewnd


; https://stackoverflow.com/questions/71547669/use-multi-modifier-key-combination-in-autohotkey-to-replace-alt-tab
; using custom since its working, requires uninstalling copilot to disable win+shift+c or smth like that
; still sometimes tries to open some https link i dont now what it is
#+!c::{
    Send("{Shift Up}") ; allow circle forward(c) after circling back(g)
    Send("{Alt Down}{Tab}")
}

#+!g::{
    Send("{Alt Down}{Shift Down}{Tab}")
}

; add us english-us keyboard
; add russian keyboard
; add german-us keyboard
$#F11:: {
    SetInputLang(0x0419) ; 67699721
}

$#F12:: { ; win F12
    SetInputLang(0x0407) ; de-de
}

$#F10:: {
    SetInputLang(0x0409) ; english-ÜS
}


SetInputLang(Lang)
{
    hWnd := WinActive("A")
    PostMessage(0x50, 0, Lang, hWnd)
}

^!v:: {
	ClipSaved := A_Clipboard ; store temporärily original clipboard
	Length := StrLen(ClipSaved)

	Send("^v") ; Copy selected left character to the clipSleep 1000Sleep 1000Sleep 1000Sleep 1000Sleep 1000
	Sleep 50
	Send("{LShift down}")
	Loop Length{
		Send("{Left}")
	}
	
	Send("{LShift up}")

}

GetInputLocaleID() {
	foregroundWindow := DllCall("GetForegroundWindow") ; docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getforegroundwindow

	isConsole := WinActive("ahk_class ConsoleWindowClass") ; CMD, Powershell
	isVGUI := WinActive("ahk_class vguiPopupWindow") ; Popups
	isUWP := WinActive("ahk_class ApplicationFrameWindow") ; Steam, UWP apps: autohotkey.com/boards/viewtopic.php?f=76&t=69414

	if isConsole {
		IMEWnd := DllCall(immGetDefaultIMEWnd, "Ptr",foregroundWindow) ; DllCall("Imm32.dll\ImmGetDefaultIMEWnd", "Ptr",fgWin)
		if (IMEWnd == 0) {
			return
		} else {
			foregroundWindow := IMEWnd
		}
	} else if isVGUI or isUWP { 
		Focused	:= ControlGetFocus("A")
		if (Focused == 0) {
			return
		} else {
			ctrlID := ControlGetHwnd(Focused, "A")
			foregroundWindow := ctrlID
		}
	}
	threadId := DllCall("GetWindowThreadProcessId", "Ptr",foregroundWindow , "Ptr",0) ; docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowthreadprocessid
	inputLocaleId := DllCall("GetKeyboardLayout", "UInt",threadId) ; precise '0xfffffffff0c00409' value

	return inputLocaleId
}