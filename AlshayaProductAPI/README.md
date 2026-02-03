# Alshaya Product API - Custom API Plugin

## Overview

This project implements a Custom API plugin for retrieving comprehensive product/article details from Microsoft Dataverse. It's built following the same patterns as the successful `AlshayaLocationAPI` but adapted for product/article entities.

## Features

✅ **Comprehensive Product Data**: Retrieves 100+ product/article fields  
✅ **Flexible Identifiers**: Supports GUID, AIMS code, Item code, Barcode, or Article description  
✅ **Rich Relationships**: Allergen relationships, Nutrient relationships, Article hierarchies  
✅ **Performance Optimized**: Single API call returns all related data  
✅ **JSON Response**: Structured, hierarchical data format  
✅ **Error Handling**: Graceful fallbacks for missing relationships  

## Architecture

```
Custom API: mdm_alshaya_GetProductDetails
├── Input: ArticleId (string) - Flexible identifier
└── Output: 
    ├── ProductDetails (JSON) - Complete product data + relationships
    └── ExecutionTime (Integer) - Performance metrics
```

## Supported Relationships

1. **Allergen Relationships**: Product allergen associations
2. **Nutrient Relationships**: Nutritional information and values  
3. **Child Article Relationships**: Sub-products, components, ingredients
4. **Parent Article Relationships**: Parent products, recipes, bundles

## Field Categories

The plugin retrieves fields across these categories:

- **Identifiers**: Article ID, AIMS code, Item code, Barcode, Auto Article ID
- **Descriptions**: Names and descriptions (English/Arabic)  
- **Classification**: Status, type, action codes, brand, hierarchy levels
- **Physical Properties**: Weight, dimensions, packaging, storage requirements
- **Supply Chain**: Supplier info, sourcing, lead times, MOQ
- **Pricing**: Purchase prices, cost control, currency handling
- **Food Safety**: Halal, Kosher, allergen info, expiry, storage temp
- **Nutrition**: Recipe data, serving size, nutrient source
- **Operational**: Flags for inventory, selling, compliance

## Project Structure

```
AlshayaProductAPI/
├── AlshayaProductAPI.csproj     # .NET Framework 4.6.2 project
├── GetProductDetailsPlugin.cs   # Main plugin implementation  
├── PluginBase.cs               # Plugin infrastructure
├── CustomApiDefinition.json    # API metadata reference
├── Test-CustomProductAPI.ps1   # Testing script
└── README.md                   # This file
```

## Quick Start

### 1. Build the Plugin

```powershell
cd AlshayaProductAPI
dotnet restore
dotnet build --configuration Release
```

**✅ Strong Name Signing**: The plugin is automatically signed using `AlshayaProductAPI.snk` to meet Dataverse security requirements.

### 2. Deploy to Dataverse

1. **Register Assembly**: Use Plugin Registration Tool to upload the built DLL
2. **Create Custom API**: Configure in Power Platform admin center or via API
3. **Associate Plugin**: Link the plugin type to the Custom API message
4. **Test**: Use the provided PowerShell script

### 3. API Usage

**HTTP GET Request:**
```http
GET [org]/api/data/v9.2/mdm_alshaya_GetProductDetails(ArticleId='AIMS12345')
Authorization: Bearer [token]
```

**Response Structure:**
```json
{
  "ProductDetails": "{...}", // JSON string with complete product data
  "ExecutionTime": 250       // Milliseconds
}
```

## Input Flexibility

The API accepts various identifier formats:

- **GUID**: `12345678-1234-1234-1234-123456789012`
- **AIMS Code**: `AIMS12345` (most common)  
- **Item Code**: `ITEM98765`
- **Barcode**: `1234567890123`
- **Article Description**: `Product Name`

## Testing

Use the provided PowerShell script:

```powershell
.\Test-CustomProductAPI.ps1
```

Or test with Python:

```python
import requests
url = f"{org_url}/api/data/v9.2/mdm_alshaya_GetProductDetails(ArticleId='AIMS12345')"
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(url, headers=headers)
data = response.json()
product_details = json.loads(data["ProductDetails"])
```

## Configuration

### Field Customization

Modify field arrays in `GetProductDetailsPlugin.cs`:

```csharp
private static readonly string[] ARTICLE_FIELDS = {
    // Add/remove fields as needed
    "mdm_articleid", "mdm_article_id", ...
};
```

### Relationship Configuration

Update relationship navigation properties:

```csharp
private const string ALLERGEN_RELATIONSHIP = "mdm_articleallergenrelationship_Article_mdm_article";
// Update based on your metadata analysis
```

## Performance Notes

- **Expected Response Time**: 150-500ms depending on relationships
- **Field Selection**: 100+ fields configured by default
- **Relationship Handling**: Independent queries with graceful failure
- **Caching**: Leverages Dataverse platform caching

## Development Notes

Based on the successful `AlshayaLocationAPI` implementation patterns:

- ✅ **PluginBase Architecture**: Robust error handling and tracing
- ✅ **Metadata-Driven Configuration**: Field arrays defined in code
- ✅ **Flexible Lookup Strategy**: GUID + multiple alternate keys
- ✅ **JSON Serialization**: Structured response formatting
- ✅ **.NET CLI Workflow**: No Visual Studio dependency

## Extending the Plugin

### Add New Relationships

1. **Analyze Metadata**: Use entity metadata exporter to find navigation properties
2. **Add Field Arrays**: Define fields to retrieve from related entities
3. **Implement Query Method**: Follow existing patterns
4. **Update Result Class**: Add property to `ProductDetailsResult`

### Add New Alternate Keys

Update the `alternateKeys` dictionary in `GetArticleByIdentifier()`:

```csharp
var alternateKeys = new Dictionary<string, string>
{
    { "your_new_field", "key_name" }
};
```

## Troubleshooting

### Common Issues

1. **"Article not found"**: Verify identifier format and entity permissions
2. **"Relationship data missing"**: Check navigation property names in metadata  
3. **Performance issues**: Consider reducing field selection for large datasets
4. **JSON serialization errors**: Verify all retrieved fields are serializable

### Debug Process

1. **Enable Plugin Tracing** in Plugin Registration Tool
2. **Check Execution Logs** in System Jobs
3. **Test Individual Components** using the Python reference script
4. **Verify Metadata** with entity metadata exporter

## Version History

- **v1.0.0**: Initial implementation based on `custom-api-product.py`
  - Complete field mapping from Python script
  - All relationship types implemented
  - Flexible identifier support
  - JSON response formatting

## Dependencies

- **.NET Framework 4.6.2**: Required for Dataverse plugins  
- **Microsoft.CrmSdk.CoreAssemblies 9.0.2**: Dataverse SDK
- **Newtonsoft.Json 13.0.1**: JSON serialization

## Next Steps

1. **Test with Real Data**: Use actual article identifiers from your environment
2. **Performance Optimization**: Monitor execution times and optimize queries
3. **Additional APIs**: Consider implementing `GetProductList`, `SearchProducts`
4. **Integration**: Connect with existing applications using the custom-api-product.py patterns

---

**Status**: ✅ Ready for deployment  
**Build Status**: ✅ Compiles successfully  
**Pattern Compliance**: ✅ Follows AlshayaLocationAPI patterns  
**Documentation**: ✅ Complete deployment and usage guide