# Product API Enhancement Guide

*Complete guide for extending and customizing the Dataverse Product API Custom Plugin*

## 📋 Table of Contents

1. [Field Management](#field-management)
2. [Relationship Control](#relationship-control)
3. [JSON Structure Customization](#json-structure-customization)
4. [CRUD Operations](#crud-operations)
5. [Separate Endpoints](#separate-endpoints)
6. [Performance Optimization](#performance-optimization)
7. [Advanced Patterns](#advanced-patterns)

---

## 🔧 Field Management

### **Adding New Fields**

```csharp
// File: GetProductDetailsPlugin.cs
// Location: ARTICLE_FIELDS array (lines ~30-110)

private static readonly string[] ARTICLE_FIELDS = {
    // Existing fields...
    "mdm_articleid", "mdm_article_id", "mdm_autoarticleid",
    
    // ADD NEW FIELDS HERE
    "mdm_newfield1", "mdm_newfield2", "mdm_newcustomfield",
    
    // For lookup fields, use base names (no _value suffix)
    "mdm_newlookupfield",  // ✅ Correct for Organization Service
    // "_mdm_newlookupfield_value",  // ❌ Wrong - Web API format
    
    // Continue with existing fields...
};
```

### **Removing Fields (Performance Optimization)**

```csharp
// Comment out or remove fields you don't need
private static readonly string[] ARTICLE_FIELDS = {
    "mdm_articleid", "mdm_article_id", "mdm_autoarticleid",
    
    // REMOVE HEAVY FIELDS FOR PERFORMANCE
    // "mdm_ingredientlist",  // Large text field - removed
    // "mdm_storageinstructions",  // Large text field - removed
    
    // Keep essential fields only
    "mdm_articledescription", "mdm_aimscode", "mdm_itemcode"
};
```

### **Dynamic Field Selection**

```csharp
// Add input parameter for field selection
protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
{
    var fieldSelection = GetInputParameter<string>(context, "FieldSelection"); // "BASIC", "FULL", "CUSTOM"
    
    string[] fieldsToUse = fieldSelection switch
    {
        "BASIC" => BASIC_ARTICLE_FIELDS,
        "FULL" => ARTICLE_FIELDS,
        "CUSTOM" => ParseCustomFields(GetInputParameter<string>(context, "CustomFields")),
        _ => ARTICLE_FIELDS
    };
    
    // Use fieldsToUse in your queries
}

// Define field sets
private static readonly string[] BASIC_ARTICLE_FIELDS = {
    "mdm_articleid", "mdm_article_id", "mdm_articledescription", 
    "mdm_aimscode", "mdm_itemcode", "statecode", "statuscode"
};
```

---

## 🔗 Relationship Control

### **Enable/Disable Specific Relationships**

```csharp
// Add relationship control flags
public class ProductDetailsResult
{
    // Add control properties
    public bool FetchAllergens { get; set; } = true;
    public bool FetchNutrients { get; set; } = true;
    public bool FetchChildArticles { get; set; } = true;
    public bool FetchParentArticles { get; set; } = true;
}

// In GetProductWithDetails method
private ProductDetailsResult GetProductWithDetails(IOrganizationService service, string articleId, ILocalPluginContext context)
{
    // Parse relationship control from input
    var relationshipControl = GetInputParameter<string>(context, "RelationshipControl"); // "ALL", "NONE", "ALLERGENS_ONLY"
    
    var controls = ParseRelationshipControl(relationshipControl);
    
    // Conditional relationship fetching
    if (controls.FetchAllergens)
    {
        context.Trace("Step 2: Fetching Allergen Relationships");
        result.AllergenRelationships = GetAllergenRelationships(service, articleGuid);
    }
    
    if (controls.FetchNutrients)
    {
        context.Trace("Step 3: Fetching Nutrient Relationships");
        result.NutrientRelationships = GetNutrientRelationships(service, articleGuid);
    }
    
    // Skip unwanted relationships for performance
}
```

### **Limit Relationship Fields**

```csharp
// Create specific field arrays for relationships
private static readonly string[] ALLERGEN_SUMMARY_FIELDS = {
    "mdm_articleallergenrelationshipid", "mdm_allergencontains", "mdm_allergenmaybe"
    // Removed heavy fields like descriptions, etc.
};

private static readonly string[] ALLERGEN_DETAILED_FIELDS = {
    "mdm_articleallergenrelationshipid", "mdm_allergencontains", "mdm_allergenmaybe",
    "mdm_description", "mdm_notes", "createdon", "modifiedon"
    // Full field set
};

// Use appropriate field set based on detail level
private EntityCollection GetAllergenRelationships(IOrganizationService service, Guid articleId, string detailLevel = "SUMMARY")
{
    var fieldSet = detailLevel == "DETAILED" ? ALLERGEN_DETAILED_FIELDS : ALLERGEN_SUMMARY_FIELDS;
    
    var query = new QueryExpression("mdm_articleallergenrelationship")
    {
        ColumnSet = new ColumnSet(fieldSet) // Use specific fields instead of ColumnSet(true)
    };
    // ... rest of query logic
}
```

### **Relationship Pagination**

```csharp
// Add pagination for large relationship sets
private EntityCollection GetNutrientRelationships(IOrganizationService service, Guid articleId, int pageSize = 50)
{
    var query = new QueryExpression("mdm_articlenutrientrelationship")
    {
        ColumnSet = new ColumnSet(NUTRIENT_FIELDS),
        PageInfo = new PagingInfo
        {
            Count = pageSize,
            PageNumber = 1
        }
    };
    
    // Add your LinkEntity logic here
    
    return service.RetrieveMultiple(query);
}
```

---

## 📄 JSON Structure Customization

### **Hierarchical JSON Structure**

```csharp
// Enhanced JSON structure with grouping
public string ToJsonString()
{
    var result = new Dictionary<string, object>
    {
        // Main product data
        ["Product"] = new Dictionary<string, object>
        {
            ["BasicInfo"] = ExtractBasicInfo(ProductData),
            ["Classifications"] = ExtractClassifications(ProductData),
            ["PhysicalProperties"] = ExtractPhysicalProperties(ProductData),
            ["SupplierInfo"] = ExtractSupplierInfo(ProductData)
        },
        
        // Relationships grouped
        ["Relationships"] = new Dictionary<string, object>
        {
            ["FoodSafety"] = new Dictionary<string, object>
            {
                ["Allergens"] = EntityCollectionToDictionary(AllergenRelationships),
                ["Nutrients"] = EntityCollectionToDictionary(NutrientRelationships)
            },
            ["ArticleHierarchy"] = new Dictionary<string, object>
            {
                ["Children"] = EntityCollectionToDictionary(ChildArticleRelationships),
                ["Parents"] = EntityCollectionToDictionary(ParentArticleRelationships)
            }
        },
        
        // Metadata
        ["Metadata"] = new Dictionary<string, object>
        {
            ["ExecutionTimeMs"] = ExecutionTimeMs,
            ["Status"] = "Success",
            ["Timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"),
            ["Version"] = PLUGIN_VERSION,
            ["FieldCount"] = ProductData?.Attributes?.Count ?? 0,
            ["RelationshipCounts"] = new Dictionary<string, int>
            {
                ["Allergens"] = AllergenRelationships?.Entities?.Count ?? 0,
                ["Nutrients"] = NutrientRelationships?.Entities?.Count ?? 0,
                ["ChildArticles"] = ChildArticleRelationships?.Entities?.Count ?? 0,
                ["ParentArticles"] = ParentArticleRelationships?.Entities?.Count ?? 0
            }
        }
    };

    var settings = new JsonSerializerSettings { Formatting = Formatting.None };
    return JsonConvert.SerializeObject(result, settings);
}

// Helper methods for data extraction
private Dictionary<string, object> ExtractBasicInfo(Entity entity)
{
    var basicFields = new[] { "mdm_articleid", "mdm_article_id", "mdm_articledescription", "mdm_aimscode" };
    return ExtractSpecificFields(entity, basicFields);
}
```

### **Custom Output Formats**

```csharp
// Add output format parameter
protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
{
    var outputFormat = GetInputParameter<string>(context, "OutputFormat"); // "FULL", "SUMMARY", "FLAT"
    
    string jsonResult = outputFormat switch
    {
        "SUMMARY" => result.ToSummaryJson(),
        "FLAT" => result.ToFlatJson(),
        "EXCEL" => result.ToExcelCompatibleJson(),
        _ => result.ToJsonString() // Default full format
    };
}

// Different JSON formats
public string ToSummaryJson()
{
    var summary = new Dictionary<string, object>
    {
        ["ArticleId"] = ProductData?.GetAttributeValue<Guid>("mdm_articleid"),
        ["Description"] = ProductData?.GetAttributeValue<string>("mdm_articledescription"),
        ["Status"] = ProductData?.GetAttributeValue<OptionSetValue>("statecode")?.Value,
        ["AllergenCount"] = AllergenRelationships?.Entities?.Count ?? 0,
        ["NutrientCount"] = NutrientRelationships?.Entities?.Count ?? 0,
        ["ExecutionTimeMs"] = ExecutionTimeMs
    };
    
    return JsonConvert.SerializeObject(summary, Formatting.None);
}
```

---

## ✏️ CRUD Operations

### **Create Product Operation**

```csharp
// New Custom API: mdm_alshaya_CreateProduct
public class CreateProductPlugin : PluginBase
{
    protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
    {
        var productData = GetInputParameter<string>(localPluginContext.PluginExecutionContext, "ProductData");
        var createRelationships = GetInputParameter<bool>(localPluginContext.PluginExecutionContext, "CreateRelationships");
        
        var service = localPluginContext.OrganizationService;
        
        // Parse JSON product data
        var productEntity = JsonToEntity(productData);
        
        // Validate required fields
        ValidateProductData(productEntity);
        
        // Create main product record
        Guid newProductId = service.Create(productEntity);
        
        // Create relationships if requested
        if (createRelationships)
        {
            CreateProductRelationships(service, newProductId, productData);
        }
        
        // Return created product details
        var result = GetProductWithDetails(service, newProductId.ToString(), localPluginContext);
        
        localPluginContext.PluginExecutionContext.OutputParameters["ProductDetails"] = result.ToJsonString();
        localPluginContext.PluginExecutionContext.OutputParameters["NewProductId"] = newProductId.ToString();
    }
    
    private void ValidateProductData(Entity productEntity)
    {
        // Required field validation
        if (!productEntity.Contains("mdm_article_id"))
            throw new InvalidPluginExecutionException("Article ID is required");
            
        if (!productEntity.Contains("mdm_articledescription"))
            throw new InvalidPluginExecutionException("Article description is required");
            
        // Business rule validation
        var aimscode = productEntity.GetAttributeValue<string>("mdm_aimscode");
        if (!string.IsNullOrEmpty(aimscode) && !ValidateAimsCodeFormat(aimscode))
            throw new InvalidPluginExecutionException($"Invalid AIMS code format: {aimscode}");
    }
}
```

### **Update Product Operation**

```csharp
// New Custom API: mdm_alshaya_UpdateProduct
public class UpdateProductPlugin : PluginBase
{
    protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
    {
        var articleId = GetInputParameter<string>(localPluginContext.PluginExecutionContext, "ArticleId");
        var updateData = GetInputParameter<string>(localPluginContext.PluginExecutionContext, "UpdateData");
        var updateRelationships = GetInputParameter<bool>(localPluginContext.PluginExecutionContext, "UpdateRelationships");
        
        var service = localPluginContext.OrganizationService;
        
        // Get existing product
        var existingProduct = GetArticleByIdentifier(service, articleId, localPluginContext);
        if (existingProduct == null)
            throw new InvalidPluginExecutionException($"Product not found: {articleId}");
        
        // Parse update data
        var updateEntity = JsonToEntity(updateData);
        updateEntity.Id = existingProduct.Id;
        updateEntity.LogicalName = "mdm_article";
        
        // Validate update
        ValidateProductUpdate(existingProduct, updateEntity);
        
        // Update main record
        service.Update(updateEntity);
        
        // Update relationships if requested
        if (updateRelationships)
        {
            UpdateProductRelationships(service, existingProduct.Id, updateData);
        }
        
        // Return updated product
        var result = GetProductWithDetails(service, articleId, localPluginContext);
        
        localPluginContext.PluginExecutionContext.OutputParameters["ProductDetails"] = result.ToJsonString();
        localPluginContext.PluginExecutionContext.OutputParameters["UpdateStatus"] = "Success";
    }
}
```

### **Bulk Operations**

```csharp
// New Custom API: mdm_alshaya_BulkProductOperations
public class BulkProductOperationsPlugin : PluginBase
{
    protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
    {
        var operation = GetInputParameter<string>(localPluginContext.PluginExecutionContext, "Operation"); // "UPDATE", "DEACTIVATE", "EXPORT"
        var productIds = GetInputParameter<string>(localPluginContext.PluginExecutionContext, "ProductIds"); // JSON array
        var batchData = GetInputParameter<string>(localPluginContext.PluginExecutionContext, "BatchData"); // JSON data for updates
        
        var service = localPluginContext.OrganizationService;
        var results = new List<Dictionary<string, object>>();
        
        var ids = JsonConvert.DeserializeObject<string[]>(productIds);
        
        foreach (var id in ids)
        {
            try
            {
                var result = operation switch
                {
                    "UPDATE" => BulkUpdateProduct(service, id, batchData),
                    "DEACTIVATE" => DeactivateProduct(service, id),
                    "EXPORT" => ExportProductData(service, id),
                    _ => throw new InvalidPluginExecutionException($"Unsupported operation: {operation}")
                };
                
                results.Add(new Dictionary<string, object>
                {
                    ["ProductId"] = id,
                    ["Status"] = "Success",
                    ["Result"] = result
                });
            }
            catch (Exception ex)
            {
                results.Add(new Dictionary<string, object>
                {
                    ["ProductId"] = id,
                    ["Status"] = "Error",
                    ["Error"] = ex.Message
                });
            }
        }
        
        localPluginContext.PluginExecutionContext.OutputParameters["BulkResults"] = JsonConvert.SerializeObject(results);
    }
}
```

---

## 🚀 Separate Endpoints

### **Specialized Endpoints**

```csharp
// 1. ALLERGEN-FOCUSED API
// Custom API: mdm_alshaya_GetProductAllergens
public class GetProductAllergensPlugin : PluginBase
{
    protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
    {
        var articleId = GetInputParameter<string>(localPluginContext.PluginExecutionContext, "ArticleId");
        var includeDetails = GetInputParameter<bool>(localPluginContext.PluginExecutionContext, "IncludeDetails");
        
        var service = localPluginContext.OrganizationService;
        
        // Get allergen data only (optimized)
        var allergenData = GetDetailedAllergenRelationships(service, Guid.Parse(articleId), includeDetails);
        
        var result = new Dictionary<string, object>
        {
            ["ArticleId"] = articleId,
            ["AllergenRelationships"] = allergenData,
            ["AllergenSummary"] = GenerateAllergenSummary(allergenData),
            ["ComplianceInfo"] = CheckAllergenCompliance(allergenData)
        };
        
        localPluginContext.PluginExecutionContext.OutputParameters["AllergenData"] = JsonConvert.SerializeObject(result);
    }
}

// 2. NUTRITION-FOCUSED API  
// Custom API: mdm_alshaya_GetProductNutrition
public class GetProductNutritionPlugin : PluginBase
{
    // Similar pattern for nutrition data
}

// 3. HIERARCHY-FOCUSED API
// Custom API: mdm_alshaya_GetProductHierarchy
public class GetProductHierarchyPlugin : PluginBase
{
    // Focus on parent-child relationships with recursive depth
}
```

### **Search and Filter APIs**

```csharp
// Custom API: mdm_alshaya_SearchProducts
public class SearchProductsPlugin : PluginBase
{
    protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
    {
        var searchTerm = GetInputParameter<string>(localPluginContext.PluginExecutionContext, "SearchTerm");
        var filters = GetInputParameter<string>(localPluginContext.PluginExecutionContext, "Filters"); // JSON filters
        var pageSize = GetInputParameter<int>(localPluginContext.PluginExecutionContext, "PageSize");
        var pageNumber = GetInputParameter<int>(localPluginContext.PluginExecutionContext, "PageNumber");
        
        var service = localPluginContext.OrganizationService;
        
        var query = new QueryExpression("mdm_article")
        {
            ColumnSet = new ColumnSet(BASIC_ARTICLE_FIELDS),
            PageInfo = new PagingInfo { Count = pageSize, PageNumber = pageNumber }
        };
        
        // Add search criteria
        if (!string.IsNullOrEmpty(searchTerm))
        {
            var searchFilter = new FilterExpression(LogicalOperator.Or);
            searchFilter.AddCondition("mdm_articledescription", ConditionOperator.Like, $"%{searchTerm}%");
            searchFilter.AddCondition("mdm_aimscode", ConditionOperator.Like, $"%{searchTerm}%");
            searchFilter.AddCondition("mdm_itemcode", ConditionOperator.Like, $"%{searchTerm}%");
            query.Criteria.AddFilter(searchFilter);
        }
        
        // Apply JSON filters
        ApplyJsonFilters(query, filters);
        
        var results = service.RetrieveMultiple(query);
        
        var searchResults = new Dictionary<string, object>
        {
            ["Products"] = results.Entities.Select(EntityToDictionary).ToList(),
            ["TotalCount"] = results.TotalRecordCount,
            ["PageInfo"] = new { PageSize = pageSize, PageNumber = pageNumber },
            ["SearchTerm"] = searchTerm,
            ["ExecutionTimeMs"] = 0 // Calculate actual time
        };
        
        localPluginContext.PluginExecutionContext.OutputParameters["SearchResults"] = JsonConvert.SerializeObject(searchResults);
    }
}
```

---

## ⚡ Performance Optimization

### **Caching Strategy**

```csharp
// Add caching for frequently accessed data
private static readonly Dictionary<string, CacheItem> _cache = new Dictionary<string, CacheItem>();

private EntityCollection GetCachedAllergenRelationships(IOrganizationService service, Guid articleId)
{
    var cacheKey = $"allergens_{articleId}";
    
    if (_cache.TryGetValue(cacheKey, out CacheItem cached) && !cached.IsExpired)
    {
        return cached.Data as EntityCollection;
    }
    
    var fresh = GetAllergenRelationships(service, articleId);
    _cache[cacheKey] = new CacheItem { Data = fresh, ExpiresAt = DateTime.UtcNow.AddMinutes(5) };
    
    return fresh;
}

private class CacheItem
{
    public object Data { get; set; }
    public DateTime ExpiresAt { get; set; }
    public bool IsExpired => DateTime.UtcNow > ExpiresAt;
}
```

### **Parallel Processing**

```csharp
// Fetch relationships in parallel
private ProductDetailsResult GetProductWithDetails(IOrganizationService service, string articleId, ILocalPluginContext context)
{
    // Get main product first
    result.ProductData = GetArticleByIdentifier(service, articleId, context);
    var articleGuid = result.ProductData.Id;
    
    // Fetch relationships in parallel
    var tasks = new List<Task>();
    
    tasks.Add(Task.Run(() => {
        result.AllergenRelationships = GetAllergenRelationships(service, articleGuid);
    }));
    
    tasks.Add(Task.Run(() => {
        result.NutrientRelationships = GetNutrientRelationships(service, articleGuid);
    }));
    
    tasks.Add(Task.Run(() => {
        result.ChildArticleRelationships = GetChildArticleRelationships(service, articleGuid);
    }));
    
    tasks.Add(Task.Run(() => {
        result.ParentArticleRelationships = GetParentArticleRelationships(service, articleGuid);
    }));
    
    Task.WaitAll(tasks.ToArray());
    
    return result;
}
```

---

## 🏗️ Advanced Patterns

### **Plugin Factory Pattern**

```csharp
// Base class for all product operations
public abstract class ProductOperationPluginBase : PluginBase
{
    protected static readonly string[] BASIC_FIELDS = { /* common fields */ };
    protected static readonly string[] DETAILED_FIELDS = { /* all fields */ };
    
    protected abstract void ExecuteProductOperation(ILocalPluginContext context);
    
    protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
    {
        try
        {
            ExecuteProductOperation(localPluginContext);
        }
        catch (Exception ex)
        {
            localPluginContext.Trace($"Error in {GetType().Name}: {ex.Message}");
            throw;
        }
    }
}

// Specific implementations
public class GetProductDetailsPlugin : ProductOperationPluginBase
{
    protected override void ExecuteProductOperation(ILocalPluginContext context)
    {
        // Implementation specific to getting details
    }
}
```

### **Configuration-Driven Fields**

```csharp
// Store field configurations in Dataverse
public class FieldConfigurationManager
{
    public static string[] GetFieldsForOperation(IOrganizationService service, string operationType)
    {
        var query = new QueryExpression("mdm_fieldconfiguration")
        {
            ColumnSet = new ColumnSet("mdm_fieldname"),
            Criteria = new FilterExpression()
        };
        query.Criteria.AddCondition("mdm_operationtype", ConditionOperator.Equal, operationType);
        query.Criteria.AddCondition("mdm_enabled", ConditionOperator.Equal, true);
        
        var results = service.RetrieveMultiple(query);
        return results.Entities.Select(e => e.GetAttributeValue<string>("mdm_fieldname")).ToArray();
    }
}

// Usage in plugin
var fieldsToUse = FieldConfigurationManager.GetFieldsForOperation(service, "GetProductDetails");
```

---

## 📋 Implementation Checklist

### **Before Making Changes:**
- [ ] Backup current plugin version
- [ ] Update version constant
- [ ] Add trace logging for changes

### **Field Changes:**
- [ ] Update field arrays (ARTICLE_FIELDS, ALLERGEN_FIELDS, etc.)
- [ ] Use base field names for lookup fields (no _value suffix)
- [ ] Test with small dataset first
- [ ] Verify JSON structure after changes

### **Relationship Changes:**
- [ ] Use LinkEntity pattern for complex queries
- [ ] Add proper error handling (return empty collections)
- [ ] Test relationship filtering
- [ ] Verify performance impact

### **New Operations:**
- [ ] Create separate Custom API definitions
- [ ] Implement input/output parameter validation
- [ ] Add comprehensive error handling
- [ ] Include execution time tracking
- [ ] Test with various input scenarios

### **Performance:**
- [ ] Monitor execution times
- [ ] Use specific ColumnSet instead of ColumnSet(true)
- [ ] Consider parallel processing for independent operations
- [ ] Implement caching for frequently accessed data

---

**This guide provides patterns for extending the Product API while maintaining the proven architecture that made the Location API successful.**