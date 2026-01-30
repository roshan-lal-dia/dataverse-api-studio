# Plugin Template Generator

## 🎯 Purpose
Generate plugin code templates for new Custom APIs based on entity analysis.

## 📁 Generated Files Structure

```
templates/plugin-templates/
├── BasePluginTemplate.cs          # Core plugin structure
├── EntityAnalysisTemplate.cs      # Metadata analysis helper  
├── ManyToManyTemplate.cs          # Many-to-many relationship handler
├── OneToManyTemplate.cs           # One-to-many relationship handler
└── CustomAPITemplate.cs          # Complete Custom API plugin
```

## 🔧 Usage

### Step 1: Entity Analysis
```bash
python scripts/analyze_[entity]_metadata.py > templates/[entity]_analysis.txt
```

### Step 2: Generate Plugin Template
```bash
python scripts/generate_plugin_template.py --entity [entity_name] --relationships [one-to-many,many-to-many]
```

### Step 3: Customize Generated Code
1. Update field arrays with your specific fields
2. Modify relationship queries based on metadata analysis
3. Update Custom API message name
4. Add business logic validation

---

## 📝 Base Plugin Template

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;
using Newtonsoft.Json;

namespace [YourNamespace]
{
    /// <summary>
    /// Custom API Plugin for retrieving [Entity] details with related data
    /// Generated from template - customize for your specific needs
    /// </summary>
    public class Get[Entity]DetailsPlugin : PluginBase
    {
        #region Version Info
        private const string PLUGIN_VERSION = "v1.0.0";
        #endregion

        #region Field Configuration
        
        // TODO: Update with your entity fields
        private static readonly string[] MAIN_ENTITY_FIELDS = {
            "[entity_prefix]id",        // Primary key
            "name",                     // Primary name
            "createdon", "modifiedon",  // Audit fields
            "statecode", "statuscode",  // Status fields
            
            // TODO: Add your specific fields
            // "field1", "field2", "field3"
        };

        // TODO: Add related entity field arrays
        private static readonly string[] RELATED_ENTITY_FIELDS = {
            // Define fields for related entities
        };

        #endregion

        #region Constructor
        public Get[Entity]DetailsPlugin() : base(typeof(Get[Entity]DetailsPlugin)) { }
        #endregion

        #region Main Execution
        protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
        {
            if (localPluginContext == null)
                throw new ArgumentNullException(nameof(localPluginContext));

            var context = localPluginContext.PluginExecutionContext;
            var service = localPluginContext.PluginUserService;

            try
            {
                // Validate Custom API message name - UPDATE THIS
                if (context.MessageName != "your_custom_api_name")
                {
                    localPluginContext.Trace($"Expected message 'your_custom_api_name', got '{context.MessageName}'");
                    return;
                }

                localPluginContext.Trace($"Starting plugin execution - Version: {PLUGIN_VERSION}");

                // Extract input parameters
                string entityId = GetInputParameter<string>(context, "EntityId");
                if (string.IsNullOrEmpty(entityId))
                    throw new InvalidPluginExecutionException("EntityId parameter is required");

                localPluginContext.Trace($"Processing entity: {entityId}");

                // Execute main logic
                var result = GetEntityWithDetails(service, entityId, localPluginContext);

                // Set output parameters
                string jsonResult = result.ToJsonString();
                context.OutputParameters["EntityDetails"] = jsonResult;
                context.OutputParameters["ExecutionTime"] = result.ExecutionTimeMs;

                localPluginContext.Trace($"Plugin completed successfully in {result.ExecutionTimeMs}ms");
            }
            catch (Exception ex)
            {
                localPluginContext.Trace($"Error in plugin: {ex.Message}");
                throw new InvalidPluginExecutionException($"Plugin failed: {ex.Message}", ex);
            }
        }
        #endregion

        #region Main Logic
        private EntityDetailsResult GetEntityWithDetails(IOrganizationService service, string entityId, ILocalPluginContext context)
        {
            var startTime = DateTime.UtcNow;
            var result = new EntityDetailsResult();

            try
            {
                // Step 1: Get main entity record
                context.Trace("Step 1: Fetching main entity record");
                result.MainEntityData = GetMainEntity(service, entityId, context);
                
                if (result.MainEntityData == null)
                    throw new InvalidPluginExecutionException($"Entity not found: {entityId}");

                Guid entityGuid = result.MainEntityData.Id;
                context.Trace($"Entity found with GUID: {entityGuid}");

                // Step 2: Get related data (customize based on your needs)
                context.Trace("Step 2: Fetching related data");
                
                // TODO: Implement your relationship queries
                // result.RelatedData1 = GetOneToManyRelated(service, entityGuid).Entities.ToList();
                // result.RelatedData2 = GetManyToManyRelated(service, entityGuid).Entities.ToList();

                result.ExecutionTimeMs = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
                result.Status = "Success";
                result.Timestamp = DateTime.UtcNow;

                return result;
            }
            catch (Exception ex)
            {
                context.Trace($"Error in GetEntityWithDetails: {ex.Message}");
                throw;
            }
        }
        #endregion

        #region Data Retrieval Methods

        private Entity GetMainEntity(IOrganizationService service, string entityId, ILocalPluginContext context)
        {
            try
            {
                // Try GUID first
                if (Guid.TryParse(entityId, out Guid guid))
                {
                    context.Trace("Attempting GUID lookup");
                    return service.Retrieve("[entity_logical_name]", guid, new ColumnSet(MAIN_ENTITY_FIELDS));
                }

                // TODO: Implement alternate key lookup if needed
                // return GetByAlternateKey(service, entityId, context);
                
                throw new InvalidPluginExecutionException($"Invalid entity identifier: {entityId}");
            }
            catch (Exception ex)
            {
                context.Trace($"Error retrieving main entity: {ex.Message}");
                throw;
            }
        }

        // TODO: Implement relationship methods
        private EntityCollection GetOneToManyRelated(IOrganizationService service, Guid entityId)
        {
            try
            {
                var query = new QueryExpression("[related_entity_name]");
                query.ColumnSet = new ColumnSet(RELATED_ENTITY_FIELDS);
                query.Criteria = new FilterExpression();
                query.Criteria.AddCondition("[parent_lookup_field]", ConditionOperator.Equal, entityId);

                return service.RetrieveMultiple(query);
            }
            catch (Exception)
            {
                return new EntityCollection();
            }
        }

        private EntityCollection GetManyToManyRelated(IOrganizationService service, Guid entityId)
        {
            try
            {
                var query = new QueryExpression("[target_entity_name]");
                query.ColumnSet = new ColumnSet(RELATED_ENTITY_FIELDS);
                
                // TODO: Update intersection table name from metadata analysis
                LinkEntity linkToIntersection = query.AddLink(
                    linkToEntityName: "[intersection_table_name]",
                    linkFromAttributeName: "[target_entity_key]",
                    linkToAttributeName: "[intersection_target_field]",
                    joinOperator: JoinOperator.Inner);
                
                linkToIntersection.LinkCriteria = new FilterExpression();
                linkToIntersection.LinkCriteria.AddCondition("[intersection_parent_field]", ConditionOperator.Equal, entityId);

                return service.RetrieveMultiple(query);
            }
            catch (Exception)
            {
                return new EntityCollection();
            }
        }

        #endregion

        #region Helper Methods

        private T GetInputParameter<T>(IPluginExecutionContext context, string parameterName)
        {
            if (context.InputParameters.ContainsKey(parameterName))
                return (T)context.InputParameters[parameterName];
            
            return default(T);
        }

        #endregion
    }

    #region Result Classes

    public class EntityDetailsResult
    {
        public Entity MainEntityData { get; set; }
        public List<Entity> RelatedData1 { get; set; } = new List<Entity>();
        public List<Entity> RelatedData2 { get; set; } = new List<Entity>();
        public int ExecutionTimeMs { get; set; }
        public string Status { get; set; }
        public DateTime Timestamp { get; set; }

        public string ToJsonString()
        {
            try
            {
                var result = new
                {
                    MainEntityData = EntityToObject(MainEntityData),
                    RelatedData1 = RelatedData1.Select(EntityToObject).ToList(),
                    RelatedData2 = RelatedData2.Select(EntityToObject).ToList(),
                    ExecutionTimeMs,
                    Status,
                    Timestamp
                };

                return JsonConvert.SerializeObject(result);
            }
            catch (Exception ex)
            {
                return JsonConvert.SerializeObject(new { Error = $"Serialization failed: {ex.Message}" });
            }
        }

        private object EntityToObject(Entity entity)
        {
            if (entity == null) return null;

            var obj = new Dictionary<string, object>
            {
                ["Id"] = entity.Id,
                ["LogicalName"] = entity.LogicalName
            };

            foreach (var attr in entity.Attributes)
            {
                if (attr.Value is EntityReference entityRef)
                {
                    obj[attr.Key] = new
                    {
                        Id = entityRef.Id,
                        Name = entityRef.Name,
                        LogicalName = entityRef.LogicalName
                    };
                }
                else
                {
                    obj[attr.Key] = attr.Value;
                }
            }

            return obj;
        }
    }

    #endregion
}
```

---

## 🎛️ Configuration Guide

### 1. Update Entity Information
```csharp
// Replace placeholders with your values:
"[entity_logical_name]" → "your_entity_name"
"[entity_prefix]" → "your_prefix_"
"your_custom_api_name" → "prefix_entity_GetDetails"
```

### 2. Configure Fields
```csharp
private static readonly string[] MAIN_ENTITY_FIELDS = {
    "entityid",              // Primary key
    "name",                  // Primary name attribute
    "createdon", "modifiedon", // Audit fields
    
    // Add your specific fields from metadata analysis:
    "field1", "field2", "field3",
    
    // Lookup fields (use entity name, not _value format):
    "lookup_field1", "lookup_field2"
};
```

### 3. Update Relationship Queries
```csharp
// From metadata analysis, update:
linkToEntityName: "actual_intersection_table_name",
linkFromAttributeName: "actual_target_key",
linkToAttributeName: "actual_intersection_field"
```

### 4. Custom API Configuration
```json
{
  "uniquename": "prefix_entity_GetDetails",
  "displayname": "Get [Entity] Details", 
  "bindingtype": 0,
  "isfunction": true,
  "parameters": [
    {
      "name": "EntityId",
      "type": 10,
      "description": "Entity identifier"
    }
  ]
}
```

---

## 🧪 Testing Template

```csharp
// Add to your test project
[TestClass]
public class Get[Entity]DetailsPluginTests
{
    [TestMethod]
    public void TestGetEntityDetails_ValidId_ReturnsData()
    {
        // Arrange
        var mockService = new Mock<IOrganizationService>();
        var plugin = new Get[Entity]DetailsPlugin();
        
        // Mock main entity
        var testEntity = new Entity("[entity_name]", Guid.NewGuid());
        testEntity["name"] = "Test Entity";
        
        mockService.Setup(s => s.Retrieve(It.IsAny<string>(), It.IsAny<Guid>(), It.IsAny<ColumnSet>()))
                   .Returns(testEntity);

        // Act & Assert
        // Implement your test logic
    }
}
```

---

## 📋 Deployment Checklist

- [ ] Update all placeholder values
- [ ] Configure field arrays from metadata
- [ ] Test main entity retrieval
- [ ] Test each relationship query
- [ ] Add proper error handling
- [ ] Enable trace logging
- [ ] Build and register plugin
- [ ] Create Custom API definition  
- [ ] Associate plugin with Custom API
- [ ] Test end-to-end API call
- [ ] Monitor performance and logs

---

## 🚀 Quick Start

1. **Copy template** to new project
2. **Run metadata analysis** for your entity
3. **Update placeholders** with actual values
4. **Test incrementally** (main entity → relationships)
5. **Deploy and verify** with real data

This template provides a solid foundation while incorporating lessons learned from the successful LocationDetails implementation.