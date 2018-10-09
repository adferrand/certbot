$script_path = $PSCommandPath
$repo_path = $script_path -replace "\\windows-installer\\construct\.ps1$"
$build_path = "$repo_path\windows-installer\build"

$venv_path = "$build_path\venv-config"
$installer_cfg_path = "$build_path\installer.cfg"
$wheels_path = "$build_path\wheels"

Push-Location $repo_path; $certbot_version = py -c "import certbot; print(certbot.__version__)"; Pop-Location

$certbot_packages = @("acme", "certbot")
$certbot_packages += Get-ChildItem "$repo_path\certbot-dns-*" | Where-Object { $_.PSIsContainer } | Foreach-Object { $_.Name }

"### Copy assets ###"

New-Item $build_path -ItemType directory -ErrorAction Ignore | Out-Null
Copy-Item -Path "$repo_path\windows-installer\certbot.ico" -Destination $build_path -Force
Copy-Item -Path "$repo_path\windows-installer\run_cmd.py" -Destination $build_path -Force

"### Prepare pynsist config ###"

"
[Application]
name=Certbot
version=$certbot_version
icon=certbot.ico
script=run_cmd.py

[Build]
directory=nsis
installer_name=certbot-$certbot_version-win32_install.exe

[Python]
version=3.7.0

[Include]
local_wheels=wheels\*.whl

[Command certbot]
entry_point=certbot.main:main
" | Set-Content -Path $installer_cfg_path

"### Prepare build environment ###"

Remove-Item -Recurse -Force -ErrorAction Ignore -Path $venv_path
py -m venv $venv_path

Push-Location $venv_path
.\Scripts\Activate.ps1
python -m pip install --upgrade pip
Pop-Location

Remove-Item -Recurse -Force -ErrorAction Ignore -Path $wheels_path
New-Item $wheels_path -ItemType directory | Out-Null
pip install wheel pynsist

"### Compile wheels ###"

$wheels_projects = $certbot_packages -replace "^certbot$" | ForEach-Object {"$repo_path\$_"}
pip wheel $wheels_projects -w $wheels_path

"### Build the installer ###"

Push-Location $build_path
pynsist $installer_cfg_path
Pop-Location

"### Clean environment ###"

deactivate