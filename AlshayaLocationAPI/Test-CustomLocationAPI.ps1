# Test-CustomLocationAPI.ps1
# PowerShell script to test the Alshaya GetLocationDetails Custom API

param(
    [Parameter(Mandatory=$true)]
    [string]$OrgUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$LocationId,
    
    [Parameter(Mandatory=$false)]
    [string]$AccessToken
)

# API endpoint construction
$apiEndpoint = "$($OrgUrl.TrimEnd('/'))/api/data/v9.2/alshaya_GetLocationDetails(LocationId='$LocationId')"

Write-Host "🔗 Testing Custom API..." -ForegroundColor Cyan
Write-Host "📍 Endpoint: $apiEndpoint" -ForegroundColor Gray
Write-Host "🔍 Location ID: $LocationId" -ForegroundColor Gray

# Detect identifier type
if ($LocationId -match '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') {
    Write-Host "   Type: GUID (fastest lookup)" -ForegroundColor Green
} else {
    Write-Host "   Type: Alternate Key (will try CCID, AutoLocationID, etc.)" -ForegroundColor Yellow
}

try {
    # Headers
    $headers = @{
        'Accept' = 'application/json'
        'OData-MaxVersion' = '4.0'
        'OData-Version' = '4.0'
    }
    
    # Add authorization if provided
    if ($AccessToken) {
        $headers['Authorization'] = "Bearer $AccessToken"
        Write-Host "🔐 Using provided access token" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No access token provided - may require authentication" -ForegroundColor Yellow
    }
    
    # Make API call
    Write-Host "📡 Sending request..." -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri $apiEndpoint -Method Get -Headers $headers
    
    # Display results
    Write-Host "✅ API call successful!" -ForegroundColor Green
    Write-Host ""
    
    # Location Data Summary
    Write-Host "📊 LOCATION SUMMARY:" -ForegroundColor Cyan
    Write-Host "  Location ID: $($response.LocationData.lmdm_locationid)" -ForegroundColor White
    Write-Host "  Store Name: $($response.LocationData.lmdm_storename)" -ForegroundColor White
    Write-Host "  Country: $($response.LocationData.lmdm_country)" -ForegroundColor White
    Write-Host "  Status: $($response.LocationData.statecode)" -ForegroundColor White
    Write-Host ""
    
    # Key Personnel Summary
    Write-Host "👥 KEY PERSONNEL: $($response.KeyPersonnel.value.Count) records" -ForegroundColor Cyan
    foreach ($person in $response.KeyPersonnel.value | Select-Object -First 3) {
        Write-Host "  • $($person.lmdm_employeename) ($($person.lmdm_employeedesignation))" -ForegroundColor White
    }
    if ($response.KeyPersonnel.value.Count -gt 3) {
        Write-Host "  • ... and $($response.KeyPersonnel.value.Count - 3) more" -ForegroundColor Gray
    }
    Write-Host ""
    
    # Business Hours Summary  
    Write-Host "🕒 BUSINESS HOURS: $($response.BusinessHours.value.Count) records" -ForegroundColor Cyan
    foreach ($hours in $response.BusinessHours.value | Select-Object -First 2) {
        Write-Host "  • Operating Hours: $($hours.lmdm_operatinghours)" -ForegroundColor White
        Write-Host "    Monday: $($hours.lmdm_mondaystarttime) - $($hours.lmdm_mondayendtime)" -ForegroundColor Gray
    }
    Write-Host ""
    
    # Performance
    Write-Host "⚡ PERFORMANCE:" -ForegroundColor Cyan
    Write-Host "  Execution Time: $($response.ExecutionTime)ms" -ForegroundColor White
    Write-Host ""
    
    # Save full response to file
    $outputFile = "location_api_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $response | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputFile -Encoding UTF8
    Write-Host "💾 Full response saved to: $outputFile" -ForegroundColor Green
    
} catch {
    Write-Host "❌ API call failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode
        Write-Host "Status Code: $statusCode" -ForegroundColor Red
        
        # Try to read error details
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorStream)
            $errorBody = $reader.ReadToEnd()
            Write-Host "Error Details: $errorBody" -ForegroundColor Red
        } catch {
            # Ignore error reading details
        }
    }
}

Write-Host ""
Write-Host "📋 Example usage:" -ForegroundColor Gray
Write-Host "  # Using GUID (fastest):" -ForegroundColor Gray
Write-Host "  .\Test-CustomLocationAPI.ps1 -OrgUrl 'https://yourorg.crm.dynamics.com' -LocationId '12345678-1234-1234-1234-123456789012'" -ForegroundColor Gray
Write-Host "  # Using CCID alternate key:" -ForegroundColor Gray  
Write-Host "  .\Test-CustomLocationAPI.ps1 -OrgUrl 'https://yourorg.crm.dynamics.com' -LocationId 'CC12345'" -ForegroundColor Gray
Write-Host "  # Using Auto Location ID:" -ForegroundColor Gray
Write-Host "  .\Test-CustomLocationAPI.ps1 -OrgUrl 'https://yourorg.crm.dynamics.com' -LocationId 'AUTO789'" -ForegroundColor Gray