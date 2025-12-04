Set WshShell = CreateObject("WScript.Shell")

' 获取命令行参数
Set args = WScript.Arguments
If args.Count < 1 Then
    MsgBox "错误: 未提供XML文件路径", vbCritical, "Ant Build Menu"
    WScript.Quit 1
End If

xmlFile = args(0)

' 检查文件是否存在
Set fso = CreateObject("Scripting.FileSystemObject")
If Not fso.FileExists(xmlFile) Then
    MsgBox "错误: 文件不存在: " & xmlFile, vbCritical, "Ant Build Menu"
    WScript.Quit 1
End If

' 检查是否为XML文件
If Not LCase(Right(xmlFile, 4)) = ".xml" Then
    MsgBox "错误: 只能运行XML文件" & vbCrLf & "当前文件: " & fso.GetFileName(xmlFile), vbCritical, "Ant Build Menu"
    WScript.Quit 1
End If

' 获取脚本所在目录，然后找到main.exe
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
parentDir = fso.GetParentFolderName(scriptDir)
exePath = parentDir & "\main.exe"

' 检查main.exe是否存在
If Not fso.FileExists(exePath) Then
    MsgBox "错误: 找不到主程序: " & exePath, vbCritical, "Ant Build Menu"
    WScript.Quit 1
End If

' 正常启动主程序（1表示正常窗口，False表示不等待）
WshShell.Run Chr(34) & exePath & Chr(34) & " " & Chr(34) & xmlFile & Chr(34), 1, False