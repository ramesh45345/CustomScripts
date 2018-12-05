# Provision script for unattended installs or packer.

# Check if dot sourced.
$isDotSourced = $MyInvocation.InvocationName -eq '.' -or $MyInvocation.Line -eq ''


### Variables ###
$CSRootPath = $env:USERPROFILE
$RepoUser = "ramesh45345"
$RepoName = "CustomScripts"
$Repo = "$RepoUser/$RepoName"
$RepoLocalPath = "$CSRootPath\$RepoName"
# Check if Virtual Machine
$VMstring = gwmi -q "select * from win32_computersystem"
if ( $VMstring.Model -imatch "vmware" ) {
  $IsVM = $true
  $VMtype = 3
} elseif ( $VMstring.Model -imatch "virtualbox" ) {
  $IsVM = $true
  $VMtype = 1
} elseif ( $VMstring.Manufacturer -imatch "qemu" ) {
  $IsVM = $true
  $VMtype = 2
} else {
  $IsVM = $false
}
# Test for Server Core.
# Basically see if exlorer.exe is present.
# https://serverfault.com/questions/529124/identify-windows-2012-server-core#529131
if (Test-Path "$env:windir\explorer.exe"){
  $core = $false
} else {
  $core = $true
}


### Functions ###

# Install chocolatey
function Fcn-InstallChocolatey {
  iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

# Add path to environment.
# https://stackoverflow.com/questions/714877/setting-windows-powershell-path-variable#1333717
# https://gist.github.com/mkropat/c1226e0cc2ca941b23a9
function Add-EnvPath {
    param(
        [Parameter(Mandatory=$true)]
        [string] $Path,

        [ValidateSet('Machine', 'User', 'Session')]
        [string] $Container = 'Session'
    )

    if ($Container -ne 'Session') {
        $containerMapping = @{
            Machine = [EnvironmentVariableTarget]::Machine
            User = [EnvironmentVariableTarget]::User
        }
        $containerType = $containerMapping[$Container]

        $persistedPaths = [Environment]::GetEnvironmentVariable('Path', $containerType) -split ';'
        if ($persistedPaths -notcontains $Path) {
            $persistedPaths = $persistedPaths + $Path | where { $_ }
            [Environment]::SetEnvironmentVariable('Path', $persistedPaths -join ';', $containerType)
        }
    }

    $envPaths = $env:Path -split ';'
    if ($envPaths -notcontains $Path) {
        $envPaths = $envPaths + $Path | where { $_ }
        $env:Path = $envPaths -join ';'
    }
}

# Rudimentary CS Clone.
function Fcn-CSClone {
  # Ensure git is installed.
  choco install -y git
  # Git executable
  $gitcmdpath = "C:\Program Files\Git\bin"

  cd $env:USERPROFILE
  if (-Not (Test-Path "$RepoLocalPath")) {
    Start-Process -Wait "$gitcmdpath\git.exe" -ArgumentList "clone","https://github.com/$Repo.git"
  }
  cd "$RepoLocalPath"
  # If ssh configuration exists, use updated remote url.
  if (Test-Path "$env:USERPROFILE\.ssh\config"){
    Start-Process -Wait "$gitcmdpath\git.exe" -ArgumentList "config","remote.origin.url","git@gitserv:$Repo.git"
  } else {
    Start-Process -Wait "$gitcmdpath\git.exe" -ArgumentList "config","remote.origin.url","https://github.com/$Repo.git"
  }

  Start-Process -Wait "$gitcmdpath\git.exe" -ArgumentList "pull"

  # Add CS to path.
  Add-EnvPath "$RepoLocalPath" 'User'

  # Create scheduled task.
  # https://stackoverflow.com/questions/23953926/how-to-execute-a-powershell-script-automatically-using-windows-task-scheduler

  $taskName = "csupdate"
  $taskExists = Get-ScheduledTask | Where-Object {$_.TaskName -like $taskName }

  if($taskExists) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
  }

  $action = New-ScheduledTaskAction -Execute 'Powershell.exe' -Argument '-ExecutionPolicy Bypass -WindowStyle Hidden -command "&git pull"' -WorkingDirectory $RepoLocalPath
  $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSPan -Hours 1)
  # This task is registered as a normal user for now. By default, it will pop up a small window briefly, and will only run if the user is logged in. To get rid of the window, enable the "Run whether user is logged on or not" option in Task Scheduler for this task.
  # https://stackoverflow.com/questions/1802127/how-to-run-a-powershell-script-without-displaying-a-window#1802836
  Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "csupdate" -Description "Hourly Update of $RepoName" -User $env:UserName
  # Set the scheduled task password if the password was set correctly.
  $cs_userpassword = "INSERTPASSWORDHERE"
  $cs_username = "INSERTUSERHERE"
  if ( -Not ( $cs_userpassword.Contains("PASSWORD") ) ) {
    schtasks /Change /RU $cs_username /RP $cs_userpassword /TN "csupdate"
  }
}

# Prompt for password to make CSUpdate a background task
function Fcn-csauto {
  schtasks /Change /RP * /TN "csupdate"
}

# Software Function
function Fcn-Software {
  # Required Basics
  choco upgrade -y dotnetfx powershell
  # Install universal apps
  choco upgrade -y 7zip
  # Libraries
  choco upgrade -y vcredist-all git python
  $gitcmdpath = "C:\Program Files\Git\bin"

  # Install VM Tools
  if ( $IsVM -eq $true ) {
    Write-Output "Installing VM Tools"
    # Handle VMTools
    $temppath = "C:\Windows\Temp"
    $winiso = "C:\Windows\Temp\windows.iso"
    $vmfolder = "$temppath\vmfolder"
    if (Test-Path $winiso) {
      Start-Process -Wait "C:\Program Files\7-Zip\7z.exe" -ArgumentList "x","$winiso","-o$vmfolder"

      if (Test-Path "$vmfolder\setup64.exe") {
        Write-Output "Installing VMWare tools"
        Start-Process -Wait "$vmfolder\setup64.exe" -ArgumentList "/s","/v/qr","REBOOT=R"
      }

      if (Test-Path "$vmfolder\VBoxWindowsAdditions.exe") {
        Write-Output "Installing Virtualbox tools"
        Start-Process -Wait "$vmfolder\cert\VBoxCertUtil.exe" -ArgumentList "add-trusted-publisher","$vmfolder\cert\vbox-sha1.cer" | Out-Null
        Start-Process -Wait "$vmfolder\VBoxWindowsAdditions.exe" -ArgumentList "/S"
      }

      # Clean up vmtools
      Write-Output "Cleaning up VMTools"
      Remove-Item -Recurse -Force $winiso
      Remove-Item -Recurse -Force $vmfolder
    }

    # QEMU
    if ($VMtype -eq 2) {
      Write-Output "Installing SPICE/QEMU tools"
      $kvmguestfolder = "$temppath\kvm-guest-drivers-windows"
      Start-Process -Wait "$gitcmdpath\git.exe" -ArgumentList "clone","https://github.com/virtio-win/kvm-guest-drivers-windows","$kvmguestfolder"
      Start-Process -Wait "$kvmguestfolder\Tools\InstallCertificate.bat" -WorkingDirectory "$kvmguestfolder\Tools\"
      $kvm_exefolder = "$env:PUBLIC\Desktop\"
      Invoke-WebRequest -Uri https://www.spice-space.org/download/windows/spice-guest-tools/spice-guest-tools-latest.exe -OutFile "$kvm_exefolder\spice-guest-tools-latest.exe"
      Start-Process -Wait "$kvm_exefolder\spice-guest-tools-latest.exe" -ArgumentList "/S"
      Remove-Item -Recurse -Force $kvmguestfolder
    }
  }

  # Install packages not for core.
  if ( $core -eq $false ) {
    Write-Output "Installing Desktop Apps"
    # GUI Apps
    choco upgrade -y googlechrome notepadplusplus tortoisegit bleachbit putty chocolateygui conemu VisualStudioCode winmerge libreoffice-fresh sumatrapdf nomacs jre8 WizTree
    # Tablacus
    Fcn-Tablacus
    # Install for Windows 8 or above.
    if ([Environment]::OSVersion.Version.Major -ge 8){
      choco upgrade -y classic-shell ShutUp10
    }
    # Install for lower than Windows 8
    if ([Environment]::OSVersion.Version.Major -lt 8){
      choco upgrade -y ie11
    }
  }

  # Chocolatey Configuration
  choco feature enable -n allowGlobalConfirmation

  # Non-vm software
  if ( $IsVM -eq $false ) {
    # Install packer
    choco upgrade -y packer
    # Install python dependancies
    Start-Process -Wait "C:\Python37\Scripts\pip.exe" -ArgumentList "install","passlib"
  }
}

# Enable Hyper-V
function Fcn-HypervEn {
  # Windows 10
  # https://docs.microsoft.com/en-us/powershell/module/dism/get-windowsoptionalfeature?view=win10-ps
  # Search for optional features:
  # Get-WindowsOptionalFeature -Online | Select-String <nameoffeature>
  Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart
  # Windows Server
  # https://docs.microsoft.com/en-us/powershell/module/microsoft.windows.servermanager.migration/install-windowsfeature?view=win10-ps
  Install-WindowsFeature -Name Hyper-V -IncludeManagementTools
  # Create Ethernet adapter
  New-VMSwitch -name "External VM Switch" -NetAdapterName "Ethernet" -AllowManagementOS $true
}

# Disable Hyper-V
function Fcn-HypervDis {
  # Remove VMSwitch first
  Remove-VMSwitch "External VM Switch"
  # Windows 10
  Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart
  # Windows Server
  Uninstall-WindowsFeature -Name Hyper-V -IncludeManagementTools
}

# Tablacus Function
function Fcn-Tablacus {
  # Install/upgrade Tablacus
  choco upgrade -y tablacus

  # Tablacus configuration
  $pathtotablacus = "$env:PROGRAMDATA\chocolatey\lib\tablacus\tools\"
  if(Test-Path -Path $pathtotablacus){
    # Set rwx everyone permissions for tablacus folder
    $Acl = Get-ACL $pathtotablacus
    $AccessRule= New-Object System.Security.AccessControl.FileSystemAccessRule("everyone","full","ContainerInherit,Objectinherit","none","Allow")
    $Acl.AddAccessRule($AccessRule)
    Set-Acl $pathtotablacus $Acl
    # Create shortcut for tablacus
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\Tablacus.lnk")
    $Shortcut.TargetPath = "$pathtotablacus\TE64.exe"
    $Shortcut.WorkingDirectory = "$pathtotablacus"
    $Shortcut.Save()
  }
}

# Customize Function
function Fcn-Customize {
  # Power customizations
  if ( $IsVM -eq $true ) {
    # Set the High Performance mode for VMs.
    # powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
    powercfg -Change -monitor-timeout-ac 0
    powercfg -Change -monitor-timeout-dc 0
  }
  else {
    powercfg -Change -monitor-timeout-ac 10
    powercfg -Change -monitor-timeout-dc 10
  }
  # Set other timeouts (as listed in "powercfg /?" )
  powercfg /hibernate off
  powercfg -Change -disk-timeout-ac 0
  powercfg -Change -disk-timeout-dc 0
  powercfg -Change -standby-timeout-ac 0
  powercfg -Change -standby-timeout-dc 0
  powercfg -Change -hibernate-timeout-ac 0
  powercfg -Change -hibernate-timeout-dc 0
  # https://superuser.com/questions/874849/change-what-closing-the-lid-does-from-the-commandline
  # Set the lid close to do nothing for high performance profile.
  powercfg -setdcvalueindex 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 4f971e89-eebd-4455-a8de-9e59040e7347 5ca83367-6e45-459f-a27b-476b1d01c936 000
  powercfg -setacvalueindex 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 4f971e89-eebd-4455-a8de-9e59040e7347 5ca83367-6e45-459f-a27b-476b1d01c936 000
  # Set the lid close to do nothing for balanced profile.
  powercfg -setdcvalueindex 381b4222-f694-41f0-9685-ff5bb260df2e 4f971e89-eebd-4455-a8de-9e59040e7347 5ca83367-6e45-459f-a27b-476b1d01c936 000
  powercfg -setacvalueindex 381b4222-f694-41f0-9685-ff5bb260df2e 4f971e89-eebd-4455-a8de-9e59040e7347 5ca83367-6e45-459f-a27b-476b1d01c936 000

  # Windows customizations
  Write-Output "Extra Folder Options"
  # Show OS Files
  New-ItemProperty -Path Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name ShowSuperHidden -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  # Launch Windows Explorer in ThisPC
  New-ItemProperty -Path Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name LaunchTo -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  # Don't hide file extensions
  New-ItemProperty -Path Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name HideFileExt -Value 0 -Force -ErrorAction SilentlyContinue | Out-Null
  # Show hidden files
  New-ItemProperty -Path Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name Hidden -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  # Display full paths
  New-ItemProperty -Path Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name FullPath -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  New-ItemProperty -Path Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name FullPathAddress -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  Write-Output "Hide Search bar"
  New-ItemProperty -Path Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Search -Name SearchboxTaskbarMode -Value 0 -Force -ErrorAction SilentlyContinue | Out-Null
  Write-Output "Set small icons for taskbar"
  New-ItemProperty -Path Registry::HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name TaskbarSmallIcons -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  Write-Output "Show taskbar on multiple displays"
  New-ItemProperty -Path Registry::HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name MMTaskbarEnabled -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  New-ItemProperty -Path Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name MMTaskbarMode -Value 2 -Force -ErrorAction SilentlyContinue | Out-Null
  Write-Output "Combine taskbar items only when full"
  New-ItemProperty -Path Registry::HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name TaskbarGlomLevel -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  New-ItemProperty -Path Registry::HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name MMTaskbarGlomLevel -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  # Remove people button
  # https://www.tenforums.com/tutorials/83096-add-remove-people-button-taskbar-windows-10-a.html
  New-ItemProperty -Path Registry::HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced\People -Name PeopleBand -Value 0 -Force -ErrorAction SilentlyContinue | Out-Null
  # Disable Snap Assist (only the next window part)
  # https://www.tenforums.com/tutorials/4343-turn-off-aero-snap-windows-10-a.html#option3
  New-ItemProperty -Path "Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" -Name SnapAssist -Value 0 -Force -ErrorAction SilentlyContinue | Out-Null
  # Disable onedrive startup.
  New-ItemProperty -Path "Registry::HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run" -Name "OneDrive" -Value ([byte[]](0x03,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00)) -Force -ErrorAction SilentlyContinue | Out-Null
  # Enable quickedit in shells
  New-ItemProperty -Path Registry::HKCU\Console -Name QuickEdit -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  # Set Control Panel Icon Size
  Write-Output "Control Panel icon changes"
  New-ItemProperty -Path Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ControlPanel -Name AllItemsIconView -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  New-ItemProperty -Path Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ControlPanel -Name StartupPage -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null

  # Set pagefile
  wmic computersystem set AutomaticManagedPagefile=False
  wmic pagefileset delete
  wmic pagefileset create name="$ENV:SystemDrive\pagefile.sys"
  $PageFile = Get-WmiObject -Class Win32_PageFileSetting
  $PageFile.InitialSize = 64
  $PageFile.MaximumSize = 2048
  $PageFile.Put()

  # Disable thumbs.db on lower than Windows 8
  if ([Environment]::OSVersion.Version.Major -lt 8){
    Write-Output "Disable Thumbs.db"
    New-ItemProperty -Path Registry::HKCU\Software\Policies\Microsoft\Windows\Explorer -Name DisableThumbsDBOnNetworkFolders -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
    New-ItemProperty -Path Registry::HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced -Name DisableThumbnailCache -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  }

  # Set EST as timezone
  tzutil /s "Eastern Standard Time"
  # Set system clock as UTC
  New-ItemProperty -Path Registry::HKLM\System\CurrentControlSet\Control\TimeZoneInformation -Name RealTimeIsUniversal -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null

  # Add windows defender exclusions
  Add-MpPreference -ExclusionPath "$env:windir\Temp\SppExtComObjHook.dll"
  Add-MpPreference -ExclusionPath "$env:USERPROFILE\Desktop"
  Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\Temp\SppExtComObjHook.dll"
  Add-MpPreference -ExclusionPath "$env:windir\AutoKMS"
}

# Remove Windows Defender
function Fcn-DisableDefender {
  # Windows Server
  Uninstall-WindowsFeature Windows-Defender-GUI
  Uninstall-WindowsFeature Windows-Defender

  # Windows 10
  # Disable Sample submission
  Set-MpPreference -SubmitSamplesConsent 2
  Set-MpPreference -MAPSReporting 0
  # Disable real-time monitoring
  Set-MpPreference -DisableRealtimeMonitoring $True
  # Disable via registry
  # https://www.tenforums.com/tutorials/5918-turn-off-windows-defender-windows-10-a.html
  New-ItemProperty -Path "Registry::HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" -Name DisableAntiSpyware -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
  # Hide Defender system tray (only for 1803 and above)
  # https://www.tenforums.com/tutorials/11974-hide-show-windows-defender-notification-area-icon-windows-10-a.html#option4
  New-ItemProperty -Path "Registry::HKLM\SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Systray" -Name HideSystray -Value 1 -Force -ErrorAction SilentlyContinue | Out-Null
}

# Enable Windows Defender
function Fcn-EnableDefender {
  # Windows Server
  Install-WindowsFeature -Name Windows-Defender-GUI

  # Windows 10
  # Enable via registry
  # https://www.tenforums.com/tutorials/5918-turn-off-windows-defender-windows-10-a.html
  New-ItemProperty -Path "Registry::HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" -Name DisableAntiSpyware -Value 0 -Force -ErrorAction SilentlyContinue | Out-Null
  # Show Defender system tray (only for 1803 and above)
  # https://www.tenforums.com/tutorials/11974-hide-show-windows-defender-notification-area-icon-windows-10-a.html#option4
  New-ItemProperty -Path "Registry::HKLM\SOFTWARE\Policies\Microsoft\Windows Defender Security Center\Systray" -Name HideSystray -Value 0 -Force -ErrorAction SilentlyContinue | Out-Null
  # Sample submission
  Set-MpPreference -SubmitSamplesConsent 0
  Set-MpPreference -MAPSReporting 0
  # Real-time monitoring
  Set-MpPreference -DisableRealtimeMonitoring $False
}

# Remove all items from Windows 10 Stock Start Menu
function Fcn-StartMenuRemoveAll {
  if ( $core -eq $false ) {
    # https://www.tenforums.com/customization/21002-how-automatically-cmd-powershell-script-unpin-all-apps-start.html
    # Loop through every item, and remove pin.
    ((New-Object -Com Shell.Application).NameSpace('shell:::{4234d49b-0245-4df3-b780-3893943456e1}').Items() | ?{$_.Name}).Verbs() | ?{$_.Name.replace('&','') -match 'From "Start" UnPin|Unpin from Start'} | %{$_.DoIt()}
    # http://www.thewindowsclub.com/erase-default-preinstalled-modern-apps-windows-8
    # List all Modern Apps on system
    #Get-AppxPackage -allusers | Select Name, PackageFullName
    # Remove Apps
    Get-AppxPackage -allusers *king.com* | Remove-AppxPackage
  }
}

# Disable WinRM
function Fcn-DisableWinRM {
  $winrmService = Get-Service -Name WinRM
  if ($winrmService.Status -eq "Running"){
      Disable-PSRemoting -Force
  }
  Stop-Service winrm
  Set-Service -Name winrm -StartupType Disabled
}

# Disable OneDrive
function Fcn-OnedriveDisable {
  Write-Output "Onedrive: Kill Process"
  taskkill.exe /F /IM "OneDrive.exe"

  Write-Output "Onedrive: Uninstall"
  if (Test-Path "$env:systemroot\System32\OneDriveSetup.exe") {
    Start-Process -Wait "$env:systemroot\System32\OneDriveSetup.exe" -ArgumentList "/uninstall"
  }
  if (Test-Path "$env:systemroot\SysWOW64\OneDriveSetup.exe") {
    Start-Process -Wait "$env:systemroot\SysWOW64\OneDriveSetup.exe" -ArgumentList "/uninstall"
  }

  Write-Output "Onedrive: Removing leftovers trash"
  rm -Recurse -Force -ErrorAction SilentlyContinue "$env:localappdata\Microsoft\OneDrive"
  rm -Recurse -Force -ErrorAction SilentlyContinue "$env:programdata\Microsoft OneDrive"
  rm -Recurse -Force -ErrorAction SilentlyContinue "C:\OneDriveTemp"

  Write-Output "Onedrive: Remove from explorer sidebar"
  New-PSDrive -PSProvider "Registry" -Root "HKEY_CLASSES_ROOT" -Name "HKCR"
  mkdir -Force "HKCR:\CLSID\{018D5C66-4533-4307-9B53-224DE2ED1FE6}"
  sp "HKCR:\CLSID\{018D5C66-4533-4307-9B53-224DE2ED1FE6}" "System.IsPinnedToNameSpaceTree" 0
  mkdir -Force "HKCR:\Wow6432Node\CLSID\{018D5C66-4533-4307-9B53-224DE2ED1FE6}"
  sp "HKCR:\Wow6432Node\CLSID\{018D5C66-4533-4307-9B53-224DE2ED1FE6}" "System.IsPinnedToNameSpaceTree" 0
  Remove-PSDrive "HKCR"

  Write-Output "Onedrive: Removing run option for new users"
  reg load "hku\Default" "C:\Users\Default\NTUSER.DAT"
  reg delete "HKEY_USERS\Default\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "OneDriveSetup" /f
  reg unload "hku\Default"

  Write-Output "Onedrive: Removing startmenu junk entry"
  rm -Force -ErrorAction SilentlyContinue "$env:userprofile\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\OneDrive.lnk"
}

### Begin Code ###
if (-Not $isDotSourced) {
  Write-Output "Running provision script."
  Fcn-InstallChocolatey
  Fcn-CSClone
  Fcn-Software
  Fcn-OnedriveDisable
  Fcn-Customize
  if ( $core -eq $true -Or $IsVM -eq $true ) {
    Fcn-DisableDefender
  }
  Fcn-StartMenuRemoveAll
  Fcn-DisableWinRM
}
