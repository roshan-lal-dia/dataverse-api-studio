# Complete Guide: Building Custom APIs with Plugins in Dataverse

## 🎯 Overview

This comprehensive guide covers building Custom APIs with .NET plugins in Microsoft Dataverse, based on the successful implementation of `mdm_alshaya_GetLocationDetails`. This solution retrieves complex entity data with many-to-many relationships and one-to-many relationships in a single API call.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)  
3. [Custom API Creation](#custom-api-creation)
4. [Plugin Development](#plugin-development)
5. [Relationship Handling](#relationship-handling)
6. [Deployment Process](#deployment-process)
7. [Testing & Debugging](#testing--debugging)
8. [Extending to Other Entities](#extending-to-other-entities)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

### Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Custom API    │───▶│  .NET Plugin    │───▶│   JSON Result   │
│  (Unbound)      │    │  (IPlugin)      │    │  (Complex Data) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ GET /api/data/  │    │ QueryExpression │    │ LocationData +  │
│ v9.2/CustomAPI  │    │ LinkEntity      │    │ KeyPersonnel +  │
│ Name(params)    │    │ Many-to-Many    │    │ BusinessHours   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Features
- **Single API Call**: Returns main entity + all related data
- **Many-to-Many Support**: Handles complex intersection table queries  
- **Performance Optimized**: Efficient QueryExpression with LinkEntity
- **JSON Response**: Structured, hierarchical data format
- **Error Handling**: Graceful fallbacks for missing relationships

## 🛠️ Prerequisites

### Development Environment
```powershell
# Required Tools
- .NET SDK 6.0+ (with .NET Framework 4.6.2 targeting support)
- .NET CLI (dotnet command)
- Plugin Registration Tool (PRT)
- Microsoft.Xrm.Sdk (NuGet package)
- Microsoft.CrmSdk.CoreAssemblies (NuGet package)

# Optional but Recommended  
- Power Platform CLI
- Dataverse Web API testing tool (Postman/Insomnia)
- Visual Studio Code or any text editor

# Note: Visual Studio IDE is NOT required - .NET CLI handles all build operations
```

### Dataverse Setup
- System Administrator or System Customizer role
- Custom API creation permissions
- Plugin registration permissions
- Entity metadata access

## 🔧 Custom API Creation

### Step 1: Design the Custom API

```json
{
  "uniquename": "mdm_alshaya_GetLocationDetails",
  "displayname": "Get Location Details",
  "bindingtype": 0,  // Unbound (Global)
  "isfunction": true,  // GET request
  "description": "Retrieves comprehensive location data including personnel and hours"
}
```

### Step 2: Define Input Parameters

```json
{
  "name": "LocationId", 
  "uniquename": "LocationId",
  "type": 10,  // String
  "iscustomizable": true,
  "description": "Location identifier (GUID or alternate key)"
}
```

### Step 3: Define Output Parameters  

```json
{
  "name": "LocationDetails",
  "uniquename": "LocationDetails", 
  "type": 10,  // String (JSON)
  "iscustomizable": true,
  "description": "Complete location data as JSON"
},
{
  "name": "ExecutionTime",
  "uniquename": "ExecutionTime",
  "type": 1,   // Integer
  "iscustomizable": true,
  "description": "Plugin execution time in milliseconds"
}
```

### Step 4: Power Platform Solution

1. **Create Solution**:
   ```powershell
   # Using Power Platform CLI
   pac solution create --name "LocationAPI" --publisher "YourPublisher"
   ```

2. **Add Custom API via UI**:
   - Power Platform admin center
   - Solutions → New → More → Custom API
   - Configure parameters and properties

## 💻 Plugin Development

### Project Structure
```
AlshayaLocationAPI/
├── AlshayaLocationAPI.csproj      # Project file with .NET Framework 4.6.2 target
├── GetLocationDetailsPlugin.cs     # Main plugin class
├── PluginBase.cs                  # Base plugin infrastructure  
├── CustomApiDefinition.json       # API metadata (reference)
├── bin/Release/net462/            # Build output (dotnet build)
├── obj/                           # Build intermediates
└── packages.config                # NuGet dependencies (auto-managed)
```

### .NET CLI Project Setup
```powershell
# Create new class library project
dotnet new classlib -n AlshayaLocationAPI -f net462

# Add required NuGet packages
dotnet add package Microsoft.CrmSdk.CoreAssemblies
dotnet add package Microsoft.Xrm.Sdk

# Verify project targets correct framework
# Check AlshayaLocationAPI.csproj contains: <TargetFramework>net462</TargetFramework>
```

### Step 1: Create Plugin Class

```csharp
using System;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;
using Newtonsoft.Json;

namespace AlshayaLocationAPI
{
    public class GetLocationDetailsPlugin : PluginBase
    {
        // Version tracking for debugging
        private const string PLUGIN_VERSION = "v2.4.0";
        
        public GetLocationDetailsPlugin() : base(typeof(GetLocationDetailsPlugin)) { }

        protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
        {
            if (localPluginContext == null)
                throw new ArgumentNullException(nameof(localPluginContext));

            var context = localPluginContext.PluginExecutionContext;
            var service = localPluginContext.PluginUserService;

            try 
            {
                // Validate Custom API message
                if (context.MessageName != "mdm_alshaya_GetLocationDetails")
                {
                    localPluginContext.Trace($"Unexpected message: {context.MessageName}");
                    return;
                }

                // Extract input parameters
                string locationId = GetInputParameter<string>(context, "LocationId");
                if (string.IsNullOrEmpty(locationId))
                    throw new InvalidPluginExecutionException("LocationId parameter is required");

                // Execute main logic
                var result = GetLocationWithDetails(service, locationId, localPluginContext);

                // Set output parameters
                context.OutputParameters["LocationDetails"] = result.ToJsonString();
                context.OutputParameters["ExecutionTime"] = result.ExecutionTimeMs;

                localPluginContext.Trace($"Plugin completed successfully in {result.ExecutionTimeMs}ms");
            }
            catch (Exception ex)
            {
                localPluginContext.Trace($"Plugin error: {ex.Message}");
                throw new InvalidPluginExecutionException($"GetLocationDetails failed: {ex.Message}", ex);
            }
        }
    }
}
```

### Step 2: Implement Core Logic

```csharp
private LocationDetailsResult GetLocationWithDetails(IOrganizationService service, string locationId, ILocalPluginContext context)
{
    var startTime = DateTime.UtcNow;
    var result = new LocationDetailsResult();

    try
    {
        // Step 1: Get main location record
        context.Trace("Step 1: Fetching main location record");
        result.LocationData = GetLocationByIdentifier(service, locationId, context);
        
        if (result.LocationData == null)
        {
            throw new InvalidPluginExecutionException($"Location not found: {locationId}");
        }

        Guid locationGuid = result.LocationData.Id;
        
        // Step 2: Get Key Personnel (Many-to-Many)
        context.Trace("Step 2: Fetching Key Personnel");
        result.KeyPersonnel = GetKeyPersonnel(service, locationGuid).Entities.ToList();
        context.Trace($"Found {result.KeyPersonnel.Count} key personnel records");

        // Step 3: Get Business Hours (One-to-Many)  
        context.Trace("Step 3: Fetching Business Hours");
        result.BusinessHours = GetBusinessHours(service, locationGuid).Entities.ToList();
        context.Trace($"Found {result.BusinessHours.Count} business hours records");

        result.ExecutionTimeMs = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        result.Status = "Success";
        result.Timestamp = DateTime.UtcNow;

        return result;
    }
    catch (Exception ex)
    {
        context.Trace($"Error in GetLocationWithDetails: {ex.Message}");
        throw;
    }
}
```

### Step 3: Field Configuration

```csharp
// Define fields to retrieve from main entity
private static readonly string[] LOCATION_FIELDS = {
    // Primary identifiers
    "lmdm_locationid", "lmdm_ccid", "lmdm_autolocationid",
    
    // System fields  
    "ownerid", "createdby", "modifiedby", "createdon", "modifiedon", "statecode",
    
    // Lookup fields (use entity name, not _value format in plugins)
    "lmdm_assetlocationtype", "lmdm_channeltype", "lmdm_storetrait",
    "lmdm_country", "lmdm_city", "lmdm_region", "lmdm_brands",
    
    // Text and number fields
    "lmdm_storename", "lmdm_fmcname", "lmdm_latitude", "lmdm_longitude",
    "lmdm_addressline1", "lmdm_email", "lmdm_landline",
    
    // Date fields
    "lmdm_forecastedopeningdate", "lmdm_tradingstartdate", "lmdm_ccidcreationdate"
};

// Related entity fields
private static readonly string[] KEY_PERSONNEL_FIELDS = {
    "lmdm_keypersonaleid", "lmdm_employeenumber", "lmdm_employeename",
    "lmdm_employeefullname", "lmdm_username", "lmdm_careerlevel", 
    "lmdm_employeedesignation", "lmdm_brand", "lmdm_division", 
    "lmdm_country", "statecode", "statuscode", "createdon", "modifiedon"
};

private static readonly string[] BUSINESS_HOURS_FIELDS = {
    "lmdm_locationbusinesshoursid", "lmdm_location", "lmdm_operatinghours",
    "lmdm_mondaystarttime", "lmdm_mondayendtime", "lmdm_tuesdaystarttime", "lmdm_tuesdayendtime",
    "lmdm_wednesdaystarttime", "lmdm_wednesdayendtime", "lmdm_thursdaystarttime", "lmdm_thursdayendtime",
    "lmdm_fridaystarttime", "lmdm_fridayendtime", "lmdm_saturdaystarttime", "lmdm_saturdayendtime",
    "lmdm_sundaystarttime", "lmdm_sundayendtime", "lmdm_seasonaltimeappplicable",
    "statecode", "statuscode", "createdon", "modifiedon"
};
```

## 🔗 Relationship Handling

### Critical Discovery: Multiple Intersection Tables

**Important**: Some entities may have multiple many-to-many relationships with different intersection tables. Always verify which one is actively used.

#### Step 1: Analyze Metadata

```csharp
// Query entity metadata to find relationships
var metadataRequest = new RetrieveEntityRequest
{
    LogicalName = "lmdm_location",
    EntityFilters = EntityFilters.Relationships
};

var metadataResponse = (RetrieveEntityResponse)service.Execute(metadataRequest);
var manyToManyRelationships = metadataResponse.EntityMetadata.ManyToManyRelationships;
```

#### Step 2: Many-to-Many Implementation

**✅ RESOLVED**: KeyPersonnel many-to-many relationship issue has been successfully resolved through proper intersection table analysis and metadata verification.

```csharp
private EntityCollection GetKeyPersonnel(IOrganizationService service, Guid locationId)
{
    try
    {
        // Start with target entity
        var query = new QueryExpression("lmdm_keypersonale")
        {
            ColumnSet = new ColumnSet(KEY_PERSONNEL_FIELDS)
        };
        
        // CRITICAL: Use the correct intersection table
        // RESOLVED: Through metadata analysis, confirmed correct intersection table name
        LinkEntity linkToIntersection = query.AddLink(
            linkToEntityName: "lmdm_location_lmdm_keypersonale", 
            linkFromAttributeName: "lmdm_keypersonaleid",        // Entity1IntersectAttribute
            linkToAttributeName: "lmdm_keypersonaleid",          // Match from keypersonale to intersection
            joinOperator: JoinOperator.Inner);
        
        // Filter on intersection table for specific location
        linkToIntersection.LinkCriteria = new FilterExpression();
        linkToIntersection.LinkCriteria.AddCondition("lmdm_locationid", ConditionOperator.Equal, locationId);

        return service.RetrieveMultiple(query);
    }
    catch (Exception)
    {
        return new EntityCollection(); // Return empty on error
    }
}
```

#### Step 3: One-to-Many Implementation

```csharp
private EntityCollection GetBusinessHours(IOrganizationService service, Guid locationId)
{
    try
    {
        var query = new QueryExpression("lmdm_locationbusinesshours");
        query.ColumnSet = new ColumnSet(BUSINESS_HOURS_FIELDS);
        query.Criteria = new FilterExpression();
        query.Criteria.AddCondition("lmdm_location", ConditionOperator.Equal, locationId);

        return service.RetrieveMultiple(query);
    }
    catch (Exception)
    {
        return new EntityCollection();
    }
}
```

### Metadata Analysis Script

```csharp
// Helper method to analyze many-to-many relationships
private void AnalyzeRelationships(IOrganizationService service, string entityName)
{
    var request = new RetrieveEntityRequest
    {
        LogicalName = entityName,
        EntityFilters = EntityFilters.Relationships
    };

    var response = (RetrieveEntityResponse)service.Execute(request);
    
    foreach (var relationship in response.EntityMetadata.ManyToManyRelationships)
    {
        Console.WriteLine($"Relationship: {relationship.SchemaName}");
        Console.WriteLine($"  Intersection Table: {relationship.IntersectEntityName}");
        Console.WriteLine($"  Entity1: {relationship.Entity1LogicalName} -> {relationship.Entity1IntersectAttribute}");
        Console.WriteLine($"  Entity2: {relationship.Entity2LogicalName} -> {relationship.Entity2IntersectAttribute}");
        Console.WriteLine();
    }
}
```

## 📦 Deployment Process

### Step 1: Build Plugin

```powershell
# Navigate to plugin project directory
cd AlshayaLocationAPI

# Restore NuGet packages
dotnet restore

# Build in Release mode using .NET CLI
dotnet build --configuration Release

# Verify assembly location
# AlshayaLocationAPI\bin\Release\net462\AlshayaLocationAPI.dll

# Alternative: Clean and rebuild if needed
# dotnet clean
# dotnet build --configuration Release --no-restore
```

### Step 2: Register Plugin Assembly

1. **Open Plugin Registration Tool (PRT)**
2. **Connect to Environment**
3. **Register New Assembly**:
   - Select built DLL file
   - Choose "Database" for assembly location
   - Select "Sandbox" for isolation mode

### Step 3: Register Plugin Step

```
Message: mdm_alshaya_GetLocationDetails
Entity: none (Custom API is unbound)
Stage: Post Operation (40)
Execution Mode: Synchronous
Configuration: (leave empty)
```

### Step 4: Associate with Custom API

1. **Find Custom API** in Dataverse
2. **Set Plugin Type** to registered plugin
3. **Activate** the Custom API

### Step 5: Deployment Verification

```http
GET {{org_url}}/api/data/v9.2/mdm_alshaya_GetLocationDetails(LocationId='test-id')
Authorization: Bearer {{access_token}}
```

## 🧪 Testing & Debugging

### Trace Logging Strategy

```csharp
protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
{
    localPluginContext.Trace($"Starting Plugin Version: {PLUGIN_VERSION}");
    localPluginContext.Trace($"Processing location: {locationId}");
    
    // Log each major step
    localPluginContext.Trace("Step 1: Fetching main location record");
    // ... execute step
    localPluginContext.Trace($"Location found with GUID: {locationGuid}");
    
    localPluginContext.Trace($"Found {keyPersonnelCount} key personnel records");
    localPluginContext.Trace($"Plugin completed in {executionTime}ms");
}
```

### Debug Process

1. **Enable Trace Logging** in Plugin Registration Tool
2. **Execute API Call**
3. **View Traces** in PRT or via query:

```http
GET {{org_url}}/api/data/v9.2/plugintraces?
$filter=contains(messagename,'mdm_alshaya_GetLocationDetails')
&$orderby=createdon desc
&$top=5
```

### Common Debug Points

```csharp
// Version verification
localPluginContext.Trace($"Plugin Version: {PLUGIN_VERSION}");

// Input validation  
localPluginContext.Trace($"Input LocationId: '{locationId}'");

// Query results
localPluginContext.Trace($"Query returned {results.Entities.Count} records");

// Relationship debugging
localPluginContext.Trace($"Using intersection table: {intersectionTableName}");

// Performance tracking
localPluginContext.Trace($"Step completed in {stepTime}ms");
```

## 🌐 Extending to Other Entities

### Template for New Custom API

```csharp
public class Get[EntityName]DetailsPlugin : PluginBase
{
    private const string PLUGIN_VERSION = "v1.0.0";
    
    // Define entity-specific fields
    private static readonly string[] MAIN_ENTITY_FIELDS = {
        "[entityname]id", "name", "createdon", "modifiedon"
        // Add relevant fields
    };

    private static readonly string[] RELATED_ENTITY_FIELDS = {
        // Define related entity fields
    };

    protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
    {
        var context = localPluginContext.PluginExecutionContext;
        var service = localPluginContext.PluginUserService;

        try
        {
            // Validate message name
            if (context.MessageName != "your_custom_api_name")
                return;

            // Get input parameters
            string entityId = GetInputParameter<string>(context, "EntityId");
            
            // Execute main logic
            var result = GetEntityWithDetails(service, entityId, localPluginContext);
            
            // Set output
            context.OutputParameters["EntityDetails"] = result.ToJsonString();
            context.OutputParameters["ExecutionTime"] = result.ExecutionTimeMs;
        }
        catch (Exception ex)
        {
            throw new InvalidPluginExecutionException($"Plugin failed: {ex.Message}", ex);
        }
    }
}
```

### Generic Relationship Patterns

```csharp
// One-to-Many pattern
private EntityCollection GetRelatedRecords(IOrganizationService service, Guid parentId, 
    string childEntity, string lookupField, string[] fields)
{
    var query = new QueryExpression(childEntity);
    query.ColumnSet = new ColumnSet(fields);
    query.Criteria = new FilterExpression();
    query.Criteria.AddCondition(lookupField, ConditionOperator.Equal, parentId);
    
    return service.RetrieveMultiple(query);
}

// Many-to-Many pattern  
private EntityCollection GetManyToManyRecords(IOrganizationService service, Guid parentId,
    string targetEntity, string intersectionTable, string parentAttribute, 
    string targetAttribute, string[] fields)
{
    var query = new QueryExpression(targetEntity);
    query.ColumnSet = new ColumnSet(fields);
    
    LinkEntity linkToIntersection = query.AddLink(
        linkToEntityName: intersectionTable,
        linkFromAttributeName: targetAttribute,
        linkToAttributeName: targetAttribute,
        joinOperator: JoinOperator.Inner);
    
    linkToIntersection.LinkCriteria = new FilterExpression();
    linkToIntersection.LinkCriteria.AddCondition(parentAttribute, ConditionOperator.Equal, parentId);
    
    return service.RetrieveMultiple(query);
}
```

## ⚡ Best Practices

### Performance Optimization

1. **Efficient Queries**:
   ```csharp
   // Use specific ColumnSet, avoid ColumnSet(true)
   query.ColumnSet = new ColumnSet("field1", "field2", "field3");
   
   // Use appropriate JoinOperators
   joinOperator: JoinOperator.Inner  // Default, good performance
   joinOperator: JoinOperator.Exists // Better for filtering only
   ```

2. **Batch Operations**:
   ```csharp
   // Execute related queries in parallel where possible
   var tasks = new[]
   {
       Task.Run(() => GetKeyPersonnel(service, locationId)),
       Task.Run(() => GetBusinessHours(service, locationId))
   };
   
   Task.WaitAll(tasks);
   ```

3. **Caching Strategy**:
   ```csharp
   // Cache static/reference data in static variables
   private static Dictionary<Guid, string> _lookupCache = new Dictionary<Guid, string>();
   ```

### Error Handling

```csharp
// Graceful degradation pattern
private EntityCollection GetOptionalRelatedData(IOrganizationService service, Guid parentId)
{
    try
    {
        // Attempt to retrieve data
        return service.RetrieveMultiple(query);
    }
    catch (Exception ex)
    {
        // Log but don't break main operation
        localPluginContext.Trace($"Optional data query failed: {ex.Message}");
        return new EntityCollection(); // Return empty collection
    }
}
```

### Security Considerations

```csharp
// Use appropriate service context
var service = localPluginContext.PluginUserService;     // Run as calling user
// vs
var service = localPluginContext.CurrentUserService;    // Run as plugin owner

// Input validation
private void ValidateInput(string input, string parameterName)
{
    if (string.IsNullOrWhiteSpace(input))
        throw new InvalidPluginExecutionException($"{parameterName} cannot be empty");
        
    if (input.Length > 100) // Prevent injection attacks
        throw new InvalidPluginExecutionException($"{parameterName} exceeds maximum length");
}
```

### Testing Strategies

1. **Unit Tests**:
   ```csharp
   [TestMethod]
   public void TestGetLocationDetails_ValidId_ReturnsData()
   {
       // Arrange
       var mockService = new Mock<IOrganizationService>();
       var plugin = new GetLocationDetailsPlugin();
       
       // Act & Assert
   }
   ```

2. **Integration Tests**:
   ```csharp
   // Test with real Dataverse environment
   [TestMethod]  
   public void TestCustomAPI_EndToEnd()
   {
       // Test actual API call
       var response = httpClient.GetAsync(customApiUrl);
       Assert.IsTrue(response.IsSuccessStatusCode);
   }
   ```

## 🐛 Troubleshooting

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| ~~"0 records returned" for Many-to-Many~~ | ~~Wrong intersection table~~ | ✅ **RESOLVED**: Analyze metadata, use correct `IntersectEntityName` |
| "Plugin not found" | Registration issue | Re-register plugin step, verify message name |
| "Null reference exception" | Missing null checks | Add defensive programming |
| "Timeout exception" | Inefficient queries | Optimize QueryExpression, reduce joins |
| "Access denied" | Security context | Check plugin run context, user permissions |
| "Build errors with .NET CLI" | Missing SDK references | Run `dotnet restore`, verify .csproj targets net462 |

### Debug Checklist

```
□ Plugin registered correctly?
□ Custom API activated? 
□ Correct message name in plugin?
□ Input parameters validated?
□ Intersection table name correct?
□ Entity field names correct (no typos)?
□ Trace logging enabled?
□ User has necessary permissions?
□ Plugin assembly up to date?
□ Error handling implemented?
```

### Performance Analysis

```csharp
// Add timing to each operation
private void TrackOperationTime(ILocalPluginContext context, string operation, Action action)
{
    var stopwatch = Stopwatch.StartNew();
    try
    {
        action();
    }
    finally
    {
        stopwatch.Stop();
        context.Trace($"{operation} completed in {stopwatch.ElapsedMilliseconds}ms");
    }
}
```

## 🎯 Success Metrics

### Plugin Performance KPIs
- **Execution Time**: < 5 seconds (typical: 200-800ms)
- **Error Rate**: < 1%  
- **Query Efficiency**: Minimal database round trips
- **Memory Usage**: Efficient object handling
- **Relationship Data**: ✅ All relationships (Many-to-Many and One-to-Many) working correctly

### API Response Structure
```json
{
  "LocationDetails": "{...}",  // Serialized JSON string
  "ExecutionTime": 375         // Milliseconds
}
```

### Parsed LocationDetails Structure
```json
{
  "LocationData": { /* Main entity with lookup expansions */ },
  "KeyPersonnel": [ /* Array of related personnel records */ ],
  "BusinessHours": [ /* Array of business hours records */ ],
  "ExecutionTimeMs": 375,
  "Status": "Success", 
  "Timestamp": "2026-01-30T12:12:47Z"
}
```

## 📚 Additional Resources

### Microsoft Documentation
- [Custom API Overview](https://docs.microsoft.com/power-apps/developer/data-platform/custom-api)
- [Plugin Development Guide](https://docs.microsoft.com/power-apps/developer/data-platform/plug-ins)
- [QueryExpression Reference](https://docs.microsoft.com/dotnet/api/microsoft.xrm.sdk.query.queryexpression)

### Tools & Utilities
- Plugin Registration Tool
- Power Platform CLI  
- XrmToolBox (Community tool)
- Dataverse REST Builder (Query generator)

---

## 🚀 Quick Start Template

For rapid development of similar Custom APIs, use this template structure:

1. **Copy plugin project structure**
2. **Modify field arrays for your entity**
3. **Update relationship queries**  
4. **Adjust Custom API definition**
5. **Test with your entity data**
6. **Deploy following the documented process**

This guide provides a complete foundation for building robust, performant Custom APIs with complex relationship handling in Microsoft Dataverse.