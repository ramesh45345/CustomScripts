@ECHO OFF
echo Set Execution Policy 64 Bit
cmd.exe /c powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Force
echo Set Execution Policy 32 Bit
C:\Windows\SysWOW64\cmd.exe /c powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Force

REM Install Chocolatey
@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
"%ALLUSERSPROFILE%\chocolatey\bin\choco.exe" upgrade -y powershell-core

REM Install Winget
@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -ExecutionPolicy Bypass -NoProfile -Command "iex (iwr -useb https://gist.githubusercontent.com/sht2017/3abf2fcb0cf9524004847b25e7375049/raw/getwinget.ps1)"
