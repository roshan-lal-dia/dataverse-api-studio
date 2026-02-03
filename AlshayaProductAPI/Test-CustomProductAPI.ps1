# Test script for Alshaya Product API Custom API
# Tests the mdm_alshaya_GetProductDetails Custom API

Write-Host "=== Alshaya Product API Test Script ===" -ForegroundColor Green
Write-Host "Testing Custom API: mdm_alshaya_GetProductDetails" -ForegroundColor Yellow
Write-Host ""

# Configuration
$ORG_URL = "https://org8c516d18.crm4.dynamics.com"  # Update with your environment
$CUSTOM_API_NAME = "mdm_alshaya_GetProductDetails"

# Test cases - Update with real article identifiers from your environment
$TEST_CASES = @(
    @{
        Name = "Test with GUID"
        ArticleId = "12345678-1234-1234-1234-123456789012"  # Replace with real GUID
        Description = "Test using article GUID identifier"
    },
    @{
        Name = "Test with AIMS Code"
        ArticleId = "AIMS12345"  # Replace with real AIMS code
        Description = "Test using AIMS code alternate key"
    },
    @{
        Name = "Test with Item Code"
        ArticleId = "ITEM98765"  # Replace with real item code
        Description = "Test using item code alternate key"
    },
    @{
        Name = "Test with Barcode"
        ArticleId = "1234567890123"  # Replace with real barcode
        Description = "Test using barcode alternate key"
    }
)

Write-Host "Available Test Cases:" -ForegroundColor Cyan
for ($i = 0; $i -lt $TEST_CASES.Count; $i++) {
    Write-Host "[$($i + 1)] $($TEST_CASES[$i].Name) - $($TEST_CASES[$i].Description)" -ForegroundColor White
}
Write-Host "[A] Run All Tests" -ForegroundColor Yellow
Write-Host ""

$choice = Read-Host "Select test case (1-$($TEST_CASES.Count) or A for all)"

function Test-ProductAPI {
    param(
        [string]$ArticleId,
        [string]$TestName
    )
    
    Write-Host "--- Testing: $TestName ---" -ForegroundColor Yellow
    Write-Host "Article ID: $ArticleId" -ForegroundColor White
    
    # Construct API URL
    $apiUrl = "$ORG_URL/api/data/v9.2/$CUSTOM_API_NAME(ArticleId='$ArticleId')"
    Write-Host "API URL: $apiUrl" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "Expected Response Properties:" -ForegroundColor Cyan
    Write-Host "- ProductDetails (JSON): Main article data + relationships" -ForegroundColor White
    Write-Host "- ExecutionTime (Integer): Execution time in milliseconds" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Expected Relationships:" -ForegroundColor Cyan
    Write-Host "- AllergenRelationships: Allergen associations" -ForegroundColor White
    Write-Host "- NutrientRelationships: Nutrient information" -ForegroundColor White
    Write-Host "- ChildArticleRelationships: Sub-products/components" -ForegroundColor White
    Write-Host "- ParentArticleRelationships: Parent products/recipes" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Sample PowerShell call:" -ForegroundColor Green
    Write-Host @"
# With authentication token
`$headers = @{
    'Authorization' = 'Bearer YOUR_ACCESS_TOKEN'
    'Accept' = 'application/json'
}
`$response = Invoke-RestMethod -Uri '$apiUrl' -Method GET -Headers `$headers
`$productData = `$response.ProductDetails | ConvertFrom-Json
Write-Host "Execution Time: `$(`$response.ExecutionTime)ms"
"@ -ForegroundColor DarkGreen
    
    Write-Host ""
    Write-Host "Sample Python call:" -ForegroundColor Green
    Write-Host @"
import requests
url = '$apiUrl'
headers = {'Authorization': 'Bearer YOUR_ACCESS_TOKEN'}
response = requests.get(url, headers=headers)
data = response.json()
print(f"Execution Time: {data['ExecutionTime']}ms")
product_details = json.loads(data['ProductDetails'])
"@ -ForegroundColor DarkGreen
    
    Write-Host ""
    Write-Host "--- Test Complete ---" -ForegroundColor Yellow
    Write-Host ""
}

# Execute tests based on user choice
if ($choice -eq "A" -or $choice -eq "a") {
    Write-Host "Running All Tests..." -ForegroundColor Green
    Write-Host "=" * 60
    
    foreach ($testCase in $TEST_CASES) {
        Test-ProductAPI -ArticleId $testCase.ArticleId -TestName $testCase.Name
        Write-Host "=" * 60
    }
    
    Write-Host "All tests completed!" -ForegroundColor Green
} elseif ($choice -match '^\d+$' -and [int]$choice -ge 1 -and [int]$choice -le $TEST_CASES.Count) {
    $selectedTest = $TEST_CASES[[int]$choice - 1]
    Test-ProductAPI -ArticleId $selectedTest.ArticleId -TestName $selectedTest.Name
} else {
    Write-Host "Invalid selection. Please run the script again." -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Deployment Notes ===" -ForegroundColor Green
Write-Host "1. Build the plugin: cd AlshayaProductAPI && dotnet build" -ForegroundColor White
Write-Host "2. Register assembly in Plugin Registration Tool" -ForegroundColor White
Write-Host "3. Create Custom API with parameters and response properties" -ForegroundColor White
Write-Host "4. Associate plugin with Custom API message" -ForegroundColor White
Write-Host "5. Test with real article identifiers from your environment" -ForegroundColor White
Write-Host ""
Write-Host "Plugin Version: v1.0.0" -ForegroundColor Cyan
Write-Host "Entity Set: mdm_articles" -ForegroundColor Cyan
Write-Host "Primary Key: mdm_articleid" -ForegroundColor Cyan
Write-Host ""