param(
    [string]$command
)

$creds = az webapp deployment list-publishing-profiles --name trifecta-agent --resource-group TrifectaRG --query "[?publishMethod=='ZipDeploy']" -o json | ConvertFrom-Json
if (-not $creds) {
    Write-Error "Could not retrieve credentials."
    exit 1
}
$username = $creds[0].userName
$password = $creds[0].userPWD
$base64Auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${username}:${password}"))
$apiUrl = "https://trifecta-agent.scm.azurewebsites.net/api/command"
$body = @{ command = $command; dir = "/home/site/wwwroot" } | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $apiUrl -Headers @{Authorization=("Basic {0}" -f $base64Auth)} -Method Post -Body $body -ContentType "application/json"
    Write-Output "--- OUTPUT ---"
    Write-Output $response.Output
    Write-Output "--- ERROR ---"
    Write-Output $response.Error
} catch {
    Write-Error $_.Exception.Message
}
