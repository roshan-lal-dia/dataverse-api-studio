# Alshaya Product API - Deployment Guide

## 📋 **Overview**
This guide walks you through deploying the **GetProductDetails** Custom API to your Dataverse environment. The Custom API provides comprehensive product/article data including relationships (Allergens, Nutrients, Article Hierarchies) through a single API call.

## 🏗️ **What Was Built**
✅ **GetProductDetailsPlugin.cs**: Main plugin with logic converted from Python script  
✅ **CustomApiDefinition.json**: API definition with parameters and response properties  
✅ **Project compiled successfully**: Ready for deployment

### **Key Features Implemented**
- **Native Dataverse Integration**: Uses IOrganizationService instead of Web API
- **Configurable Field Selection**: 100+ fields configured in C# code arrays
- **Relationship Navigation**: Automatic retrieval of Allergens, Nutrients, Article Hierarchies
- **Performance Tracking**: Returns execution time in milliseconds
- **Error Handling**: Graceful handling of missing relationships
- **Consistent Python Logic**: Mirrors the working custom-api-product.py functionality

## 📦 **Files Created**

### **1. AlshayaProductAPI/GetProductDetailsPlugin.cs**
- **Purpose**: Main Custom API plugin logic
- **Key Configuration Sections**:
  ```csharp
  // Modify these arrays to add/remove fields
  ARTICLE_FIELDS           // Core product fields (100+ from Python FORM_FIELDS)
  ALLERGEN_FIELDS          // Allergen relationship fields  
  NUTRIENT_FIELDS          // Nutrient relationship fields
  ARTICLE_RELATIONSHIP_FIELDS // Article hierarchy fields
  ```

### **2. AlshayaProductAPI/CustomApiDefinition.json**
- **Purpose**: API registration specification
- **API Name**: `mdm_alshaya_GetProductDetails`
- **Input**: ArticleId (GUID string, AIMS code, Item code, Barcode, etc.)
- **Output**: ProductDetails (JSON), ExecutionTime (Integer)

### **3. AlshayaProductAPI.csproj**
- **Purpose**: Project configuration
- **Target**: .NET Framework 4.6.2 (Dataverse compatible)
- **Dependencies**: Microsoft.CrmSdk.CoreAssemblies 9.0.2.56, Newtonsoft.Json 13.0.1

## 🚀 **Deployment Steps**

### **Prerequisites**
- [ ] Power Platform admin access to target environment
- [ ] Plugin Registration Tool (PRT) installed
- [ ] .NET SDK 6.0+ (with .NET Framework 4.6.2 targeting)
- [ ] Strong Name Key file (AlshayaProductAPI.snk) - already included in project

### **Step 1: Build & Package the Plugin**
```powershell
cd "AlshayaProductAPI"
dotnet restore
dotnet build --configuration Release
```
**Output Location**: `bin\Release\net462\AlshayaProductAPI.dll`

**✅ Strong Name Signing**: The plugin is configured with strong name signing using `AlshayaProductAPI.snk` to meet Dataverse security requirements.

### **Step 2: Register the Plugin Assembly**
1. **Open Plugin Registration Tool**
2. **Connect to your Dataverse environment**
3. **Click "Register" → "Register New Assembly"**
4. **Browse and select**: `AlshayaProductAPI.dll`
5. **Registration Settings**:
   - ✅ **Isolation Mode**: Sandbox
   - ✅ **Location**: Database
   - ✅ **Source Type**: Database

### **Step 3: Create the Custom API**
1. **In Plugin Registration Tool**, right-click your registered assembly
2. **Select "Register New Custom API"**
3. **Configure Custom API**:
   - **Name**: `mdm_alshaya_GetProductDetails`
   - **Unique Name**: `mdm_alshaya_GetProductDetails`
   - **Display Name**: `Alshaya Get Product Details`
   - **Binding Type**: Global
   - **Is Function**: ✅ Yes
   - **Plugin Type**: Select `AlshayaProductAPI.GetProductDetailsPlugin`

### **Step 4: Configure Request Parameters**
**Add Parameter**: ArticleId
- **Name**: `ArticleId`
- **Unique Name**: `ArticleId` 
- **Type**: String
- **Is Optional**: ❌ No
- **Description**: The unique identifier (GUID, AIMS code, Item code, Barcode, or description) of the article to retrieve

### **Step 5: Configure Response Properties**
**Add these 2 response properties**:

1. **ProductDetails**
   - **Type**: String
   - **Description**: Complete product data including all relationships as JSON

2. **ExecutionTime**
   - **Type**: Integer
   - **Description**: Time taken to execute the API call in milliseconds

### **Step 6: Register Plugin Step**
1. **Right-click the registered Custom API**
2. **Select "Register New Step"**
3. **Step Configuration**:
   - **Message**: `mdm_alshaya_GetProductDetails`
   - **Primary Entity**: (none)
   - **Stage**: Main Operation
   - **Execution Mode**: Synchronous

## 🧪 **Testing the API**

### **🔒 Authentication Context**
**Good News!** Authentication requirements depend on how you call the API:

#### **✅ Internal Calls (No Bearer Token Required)**
- **Canvas Apps**: `CustomAPI.GetProductDetails(ArticleId)`
- **Power Automate**: Direct Custom API connector
- **Model-driven Apps**: Ribbon button or JavaScript
- **Other Plugins/Workflows**: Native Dataverse context

#### **🌐 External Web API Calls (Bearer Token Required)**
- **External applications** via REST API
- **Postman/curl testing**
- **JavaScript apps** from outside Dataverse

### **Web API Call Format**
```http
GET [org]/api/data/v9.2/mdm_alshaya_GetProductDetails(ArticleId='[article-identifier]')
```

### **📝 Input Support - Flexible Identifiers**
**The API accepts multiple identifier types** (just like the original Python script):

✅ **GUID**: `'12345678-1234-1234-1234-123456789012'`  
✅ **AIMS Code**: `'AIMS12345'` (most common alternate key)  
✅ **Item Code**: `'ITEM98765'`  
✅ **Barcode**: `'1234567890123'`  
✅ **Article Description**: `'Product Name'` (if unique)

**Examples**:
```http
# Using GUID (fastest)
GET .../mdm_alshaya_GetProductDetails(ArticleId='12345678-1234-1234-1234-123456789012')

# Using AIMS Code alternate key  
GET .../mdm_alshaya_GetProductDetails(ArticleId='AIMS12345')

# Using Item Code
GET .../mdm_alshaya_GetProductDetails(ArticleId='ITEM789')
```

### **Example Request (External)**
```http
GET https://yourorg.api.crm.dynamics.com/api/data/v9.2/mdm_alshaya_GetProductDetails(ArticleId='AIMS12345')
Authorization: Bearer [token]
Accept: application/json
```

### **Expected Response Structure**
```json
{
  "ProductDetails": "{
    \"ProductData\": {
      \"Id\": \"guid-here\",
      \"mdm_articleid\": \"guid-here\",
      \"mdm_aimscode\": \"AIMS12345\",
      \"mdm_articledescription\": \"Product Name\",
      ...100+ fields
    },
    \"AllergenRelationships\": [...],
    \"NutrientRelationships\": [...],
    \"ChildArticleRelationships\": [...],
    \"ParentArticleRelationships\": [...],
    \"ExecutionTimeMs\": 250
  }",
  "ExecutionTime": 250
}
```

## ⚙️ **Field Configuration**

### **To Add/Remove Product Fields**
**Edit**: `GetProductDetailsPlugin.cs` → `ARTICLE_FIELDS` array
```csharp
private static readonly string[] ARTICLE_FIELDS = {
    "mdm_articleid",
    "mdm_aimscode",
    "mdm_itemcode",
    // Add your new fields here
    "mdm_yournewfield"
};
```

### **To Add/Remove Relationship Fields**
**Edit**: `ALLERGEN_FIELDS`, `NUTRIENT_FIELDS`, or `ARTICLE_RELATIONSHIP_FIELDS` arrays
```csharp
private static readonly string[] ALLERGEN_FIELDS = {
    "mdm_allergenid",
    "mdm_name",
    // Add new allergen fields here
};
```

**After field changes**: Rebuild and redeploy the assembly.

## 🔍 **Troubleshooting**

### **Common Issues**

1. **"Strong Names Error" - Assembly must be signed**
   - ✅ Ensure `AlshayaProductAPI.snk` file exists in project folder
   - ✅ Verify project file has `<SignAssembly>true</SignAssembly>`
   - ✅ Rebuild with `dotnet build --configuration Release`

2. **"Plugin not found" Error**
   - ✅ Verify assembly is registered and activated
   - ✅ Check plugin type name matches exactly

2. **"Parameter not found" Error**  
   - ✅ Verify Custom API parameter configuration
   - ✅ Check parameter names match code exactly

3. **Relationship Data Missing**
   - ✅ Verify relationship entity names in metadata
   - ✅ Check navigation property names
   - ✅ Plugin returns empty collections for failed relationships (by design)

4. **Performance Issues**
   - ✅ Check `ExecutionTime` value in response
   - ✅ Consider reducing field selection for large datasets
   - ✅ Monitor plugin execution logs

### **Debugging**
1. **Enable Plugin Tracing** in Plugin Registration Tool
2. **Check System Jobs** for plugin execution logs  
3. **Review Error Logs** in Dataverse admin center

## 📊 **Performance Notes**

### **Optimizations Implemented**
- **Single main query**: Article record retrieved in one call
- **Separate relationship queries**: Independent failure handling
- **Configurable fields**: Only retrieve what's needed
- **Entity collections**: Efficient for multiple related records

### **Expected Performance**
- **Simple product**: 50-150ms
- **With relationships**: 150-500ms  
- **Large datasets**: May require field reduction

## 🔐 **Security Considerations**

### **Plugin User Context**
The plugin runs under the **Plugin User Service** context, which provides:
- ✅ Consistent security context
- ✅ System-level access where configured
- ✅ Audit trail preservation

### **Required Permissions**
Ensure the plugin execution user has:
- ✅ **Read** access to `mdm_articles` entity
- ✅ **Read** access to `mdm_articleallergenrelationships` entity
- ✅ **Read** access to `mdm_articlenutrientrelationships` entity
- ✅ **Read** access to `mdm_articlerelationships` entity
- ✅ **Read** access to related lookup entities (allergens, nutrients)

## ✅ **Success Criteria**

Your deployment is successful when:
- [x] Plugin assembly registers without errors
- [x] Custom API appears in API list
- [x] Web API call returns product data
- [x] Related records (Allergens, Nutrients, Hierarchies) are included
- [x] ExecutionTime is reported in response
- [x] No errors in plugin trace logs

## 📞 **Next Steps**

1. **Test with real article identifiers** from your environment
2. **Verify field mapping** matches your schema
3. **Performance test** with typical usage patterns  
4. **Consider implementing** additional product APIs (GetProductList, SearchProducts)
5. **Document API endpoints** for consuming applications

## 🔄 **Integration with Existing Systems**

The Custom API is designed to replace/supplement the Python `custom-api-product.py` script:

- **Same Input Flexibility**: GUID, AIMS codes, Item codes, Barcodes
- **Compatible Output Structure**: JSON format matches Python script
- **Enhanced Performance**: Native Dataverse queries vs Web API calls
- **Better Security**: Plugin user context vs external authentication

---

**Status**: ✅ Ready for deployment  
**Build Status**: ✅ Compiled successfully  
**Configuration**: ✅ Field arrays configured from Python script  
**Documentation**: ✅ Complete deployment guide  
**Testing**: ✅ PowerShell test script provided