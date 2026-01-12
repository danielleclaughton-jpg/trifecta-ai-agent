# =============================================================================
# Trifecta AI Agent - Local Testing Script
# =============================================================================

$apiUrl = "http://localhost:5000"
$testResults = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method = "GET",
        [string]$Endpoint,
        [object]$Body = $null
    )
    
    Write-Host "`n[$Name]" -ForegroundColor Yellow
    Write-Host "  Testing: $Method $Endpoint" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = "$apiUrl$Endpoint"
            Method = $Method
            ContentType = "application/json"
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        Write-Host "  ✓ SUCCESS" -ForegroundColor Green
        
        # Pretty print response
        $response | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Cyan
        
        return @{ Success = $true; Response = $response }
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMessage = $_.Exception.Message
        
        if ($statusCode -eq 503 -or $statusCode -eq 500) {
            Write-Host "  ⚠ WARNING: $statusCode - $errorMessage" -ForegroundColor Yellow
            Write-Host "    (This may be expected if API keys are not configured)" -ForegroundColor Gray
        }
        else {
            Write-Host "  ✗ FAILED: $statusCode - $errorMessage" -ForegroundColor Red
        }
        
        return @{ Success = $false; Error = $errorMessage; StatusCode = $statusCode }
    }
}

# =============================================================================
# Run Tests
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Trifecta AI Agent - Local API Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nMake sure the Flask server is running:" -ForegroundColor Yellow
Write-Host "  python app.py" -ForegroundColor White
Write-Host "`nPress any key to start testing..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Test 1: Root endpoint
$testResults += Test-Endpoint -Name "Root Endpoint" -Endpoint "/"

# Test 2: Health check
$testResults += Test-Endpoint -Name "Health Check" -Endpoint "/health"

# Test 3: List skills
$testResults += Test-Endpoint -Name "List Skills" -Endpoint "/api/skills"

# Test 4: Get specific skill
$testResults += Test-Endpoint -Name "Get Skill" -Endpoint "/api/skills/trifecta-document-generator"

# Test 5: Chat endpoint (requires ANTHROPIC_API_KEY)
$chatBody = @{
    message = "What services does Trifecta offer?"
}
$testResults += Test-Endpoint -Name "Chat Endpoint" -Method "POST" -Endpoint "/api/chat" -Body $chatBody

# Test 6: Graph clients (requires MS credentials)
$testResults += Test-Endpoint -Name "Graph Clients" -Endpoint "/api/graph/clients"

# Test 7: Dialpad calls (requires DIALPAD_API_KEY)
$testResults += Test-Endpoint -Name "Dialpad Calls" -Endpoint "/api/dialpad/calls?limit=5"

# =============================================================================
# Summary
# =============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$successCount = ($testResults | Where-Object { $_.Success }).Count
$totalCount = $testResults.Count

Write-Host "`nTotal Tests: $totalCount" -ForegroundColor White
Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed/Warnings: $($totalCount - $successCount)" -ForegroundColor $(if ($successCount -eq $totalCount) { "Green" } else { "Yellow" })

Write-Host "`nNote: Some endpoints may fail if API keys are not configured in .env" -ForegroundColor Gray
Write-Host "This is expected for local testing without full credentials." -ForegroundColor Gray
