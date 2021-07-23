#Requires -Version 5.0
[CmdletBinding()]
param()
begin {}
process {
    $eventSource = "certbot/auto-update.ps1"
    $logName = "CertbotAutoUpdate"
    $eventID = 1

    New-EventLog -Source $eventSource -LogName $logName -ErrorAction SilentlyContinue

    function Write-Message($message, $level = "Information") {
        Write-EventLog -Source $eventSource -LogName $logName -EventID $eventID -EntryType $level -Message $message
        Write-Host $message
    }

    function Throw-Error($message) {
        Write-EventLog -Source $eventSource -LogName $logName -EventID $eventID -EntryType Error -Message $message
        throw $message
    }

    Write-Message "Starting auto-update workflow ..."

    $ErrorActionPreference = 'Stop'

    $installDir = $PSScriptRoot

    if ((Test-Path HKLM:\Software\Certbot) -And ((Get-ItemProperty -Path HKLM:\Software\Certbot).PSObject.Properties.Name -Contains "CertbotSigningPubKey")) {
        $certbotSigningPubKey = (Get-ItemProperty -Path HKLM:\Software\Certbot).CertbotSigningPubKey
    } else {
        $certbotSigningPubKey = '
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA6MR8W/galdxnpGqBsYbq
OzQb2eyW15YFjDDEMI0ZOzt8f504obNs920lDnpPD2/KqgsfjOgw2K7xWDJIj/18
xUvWPk3LDkrnokNiRkA3KOx3W6fHycKL+zID7zy+xZYBuh2fLyQtWV1VGQ45iNRp
9+Zo7rH86cdfgkdnWTlNSHyTLW9NbXvyv/E12bppPcEvgCTAQXgnDVJ0/sqmeiij
n9tTFh03aM+R2V/21h8aTraAS24qiPCz6gkmYGC8yr6mglcnNoYbsLNYZ69zF1XH
cXPduCPdPdfLlzVlKK1/U7hkA28eG3BIAMh6uJYBRJTpiGgaGdPd7YekUB8S6cy+
CQIDAQAB
-----END PUBLIC KEY-----
'
    }

    if ((Test-Path HKLM:\Software\Certbot) -And ((Get-ItemProperty -Path HKLM:\Software\Certbot).PSObject.Properties.Name -Contains "CertbotUpgradeApiURL")) {
        $certbotUpgradeApiURL = (Get-ItemProperty -Path HKLM:\Software\Certbot).CertbotUpgradeApiURL
    } else {
        $certbotUpgradeApiURL = 'https://api.github.com/repos/certbot/certbot/releases/latest'
    }

    # Get current local certbot version
    try {
        $currentVersion = certbot --version
        $currentVersion = $currentVersion -replace '^certbot (\d+\.\d+\.\d+).*$', '$1'
        $currentVersion = [System.Version]"$currentVersion"
    } catch {
        Write-Message @"
An error occured while fetching the current local certbot version:
$_
Assuming Certbot is not up-to-date.
"@ "Warning"
        $currentVersion = [System.Version]"0.0.0"
    }

    # Get latest remote certbot version
    try {
        $result = Invoke-RestMethod -Uri $certbotUpgradeApiURL -TimeoutSec 60
        $latestVersion = $result.tag_name -replace '^v(\d+\.\d+\.\d+).*$', '$1'
        $latestVersion = [System.Version]"$latestVersion"
    } catch {
        Throw-Error @"
Could not get the latest remote certbot version. Error was:
$_
Aborting auto-upgrade process.
"@
    }

    if ($currentVersion -ge $latestVersion) {
        Write-Message "No upgrade is needed, Certbot is already at the latest version ($currentVersion)."
    } else {
        # Search for the Windows installer asset
        $installerUrl = $null
        foreach ($asset in $result.assets) {
            if ($asset.name -match '^certbot-.*installer-win32\.exe$') {
                $installerUrl = $asset.browser_download_url
            }
        }

        if ($null -eq $installerUrl) {
            Throw-Error "Could not find the URL for the latest Certbot for Windows installer."
        }

        Write-Message "Starting Certbot auto-upgrade from $currentVersion to $latestVersion ..."

        $tmpPath = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid())
        New-Item -ItemType Directory -Path $tmpPath

        $installerPath = Join-Path $tmpPath "certbot-installer-win32.exe"
        try {
            # Download the installer
            Write-Message "Downloading the installer ..."
            $ProgressPreference = "SilentlyContinue"
            Invoke-RestMethod $installerUrl -OutFile $installerPath -TimeoutSec 3600

            # Check installer has a valid signature from the Certbot release team
            $signature = Get-AuthenticodeSignature $installerPath

            if ($signature.Status -ne 'Valid') {
                throw "Downloaded installer has no or invalid Authenticode signature."
            }
            $publicKey = $certbotSigningPubKey -replace '-+.*-+' -replace "`n" -replace "`r"
            $refBinaryPublicKey = [System.Convert]::FromBase64String($publicKey)
            $curBinaryPublicKey = $signature.SignerCertificate.PublicKey.EncodedKeyValue.RawData
            $diff = Compare-Object -ReferenceObject $refBinaryPublicKey -DifferenceObject $curBinaryPublicKey
            if ($diff) {
                throw "Downloaded installer has not been signed by Certbot development team."
            }

            if (Test-Path $installDir\uninstall.exe) {
                # Uninstall old Certbot first
                Write-Message "Running the uninstaller for old version (install dir: $installDir) ..."
                Start-Process -FilePath $installDir\uninstall.exe -ArgumentList "/S" -Wait
            }
            # Install new version of Certbot
            Write-Message "Running the installer for new version (install dir: $installDir) ..."
            Start-Process -FilePath $installerPath -ArgumentList "/S /D=$installDir" -Wait

            Write-Message "Certbot $latestVersion is installed."
        } catch {
            Throw-Error @"
Could not update to the latest remote certbot version. Error was:
$_
Aborting auto-upgrade process.
"@
        } finally {
            Remove-Item $tmpPath -Recurse -ErrorAction 'Ignore'
        }
    }

    Write-Message "Finished auto-update workflow."
}
end {}
