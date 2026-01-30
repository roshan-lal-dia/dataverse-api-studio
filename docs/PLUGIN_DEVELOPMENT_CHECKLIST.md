# Custom API Plugin Development: Step-by-Step Checklist

## 🎯 Project Success Summary

**Custom API**: `mdm_alshaya_GetLocationDetails`  
**Status**: ✅ **COMPLETE & WORKING**  
**Final Version**: v2.4.0  

### Results Achieved
- ✅ **LocationData**: 60+ attributes with lookup expansions
- ✅ **KeyPersonnel**: 2 records from many-to-many relationship  
- ✅ **BusinessHours**: 1 record from one-to-many relationship
- ✅ **Performance**: 375ms execution time
- ✅ **Error Handling**: Graceful fallbacks implemented

---

## 📋 Development Checklist

Use this checklist for creating new Custom API plugins:

### Phase 1: Planning & Analysis
- [ ] **Define API Requirements**
  - [ ] Identify main entity and related entities
  - [ ] Determine required fields from each entity
  - [ ] Plan JSON response structure
  
- [ ] **Analyze Entity Metadata**
  ```powershell
  # Run metadata analysis script
  python scripts/analyze_[entity]_metadata.py
  ```
  - [ ] Document one-to-many relationships
  - [ ] Document many-to-many relationships  
  - [ ] ⚠️ **CRITICAL**: Identify correct intersection table names
  - [ ] Note lookup field target entities

### Phase 2: Custom API Setup
- [ ] **Create Custom API Definition**
  - [ ] Set unique name: `[prefix]_[entity]_[operation]`
  - [ ] Choose binding type (usually Unbound for retrieval)
  - [ ] Set as Function (GET requests) 
  - [ ] Define input parameters (e.g., EntityId)
  - [ ] Define output parameters (JSON string + ExecutionTime)

- [ ] **Power Platform Solution**
  - [ ] Create or select target solution
  - [ ] Add Custom API to solution
  - [ ] Document API metadata

### Phase 3: Plugin Development
- [ ] **Project Setup**
  - [ ] Create .NET Framework 4.6.2+ project
  - [ ] Add NuGet packages:
    - [ ] `Microsoft.CrmSdk.CoreAssemblies`
    - [ ] `Microsoft.Xrm.Sdk`
    - [ ] `Newtonsoft.Json`
  - [ ] Copy PluginBase.cs from reference project

- [ ] **Core Plugin Structure**
  ```csharp
  public class Get[Entity]DetailsPlugin : PluginBase
  {
      private const string PLUGIN_VERSION = "v1.0.0";
      
      // TODO: Define field arrays
      // TODO: Implement ExecuteDataversePlugin
      // TODO: Implement main logic methods
  }
  ```

- [ ] **Field Configuration**  
  - [ ] Define main entity fields array
  - [ ] Define related entity fields arrays
  - [ ] ⚠️ **Important**: Use entity names, not `_value` format for lookups in plugins

- [ ] **Main Logic Implementation**
  - [ ] Input parameter validation
  - [ ] Main entity retrieval (with alternate key support)
  - [ ] Related entity queries
  - [ ] Result object construction
  - [ ] JSON serialization

### Phase 4: Relationship Implementation  
- [ ] **One-to-Many Relationships**
  ```csharp
  var query = new QueryExpression("child_entity");
  query.Criteria.AddCondition("parent_lookup_field", ConditionOperator.Equal, parentId);
  ```
  
- [ ] **Many-to-Many Relationships**
  - [ ] ⚠️ **CRITICAL STEP**: Verify intersection table name from metadata
  - [ ] ⚠️ **CRITICAL STEP**: Verify intersection table field names
  - [ ] Implement QueryExpression with LinkEntity:
  ```csharp
  LinkEntity linkToIntersection = query.AddLink(
      linkToEntityName: "[correct_intersection_table_name]",
      linkFromAttributeName: "[target_entity_key]", 
      linkToAttributeName: "[intersection_target_field]");
  
  linkToIntersection.LinkCriteria.AddCondition(
      "[intersection_parent_field]", ConditionOperator.Equal, parentId);
  ```

### Phase 5: Error Handling & Logging
- [ ] **Trace Logging**
  - [ ] Add version logging
  - [ ] Add step-by-step progress logging
  - [ ] Add performance timing
  - [ ] Add result count logging

- [ ] **Error Handling**
  - [ ] Input validation with meaningful errors
  - [ ] Try-catch around each major operation
  - [ ] Graceful degradation for optional data
  - [ ] Proper exception messages

### Phase 6: Testing & Debugging
- [ ] **Unit Testing**
  - [ ] Build project successfully
  - [ ] Verify no compilation warnings
  - [ ] Test field arrays completeness

- [ ] **Integration Testing**
  - [ ] Register plugin assembly
  - [ ] Register plugin step
  - [ ] Associate with Custom API
  - [ ] Enable trace logging
  - [ ] Test API call
  - [ ] Verify trace logs
  - [ ] Check response structure

### Phase 7: Troubleshooting Common Issues

#### Issue: Many-to-Many Returns 0 Records
- [ ] **Verify intersection table name**
  ```bash
  # Check metadata analysis output
  grep -i "intersectentityname" metadata.json
  ```
- [ ] **Check for multiple relationships**
  - [ ] Some entities have 2+ many-to-many relationships
  - [ ] Use the one that matches working Python/Web API calls
- [ ] **Verify field names in intersection table**
  - [ ] Entity1IntersectAttribute  
  - [ ] Entity2IntersectAttribute

#### Issue: Plugin Not Executing
- [ ] Verify Custom API message name matches plugin
- [ ] Check plugin registration step configuration
- [ ] Ensure Custom API is associated with plugin type
- [ ] Verify Custom API is activated

#### Issue: Access/Permission Errors
- [ ] Check plugin execution context (User vs System)
- [ ] Verify calling user has entity read permissions
- [ ] Check security roles for related entities

### Phase 8: Deployment & Monitoring
- [ ] **Production Deployment**
  - [ ] Build Release configuration
  - [ ] Update plugin assembly in target environment
  - [ ] Test with production data
  - [ ] Monitor performance metrics

- [ ] **Documentation Updates**  
  - [ ] Update API documentation
  - [ ] Document field mappings
  - [ ] Create usage examples
  - [ ] Update version history

---

## ⚠️ Critical Success Factors

Based on the successful implementation, these factors are essential:

### 1. Intersection Table Analysis
```json
// Always verify which intersection table is actually used:
"ManyToManyRelationships": [
  {
    "SchemaName": "Entity1_Entity2_Entity2", 
    "IntersectEntityName": "entity1_entity2",     // ← This one
    "Entity1IntersectAttribute": "entity1id",
    "Entity2IntersectAttribute": "entity2id"
  },
  {
    "SchemaName": "Entity2_Entity1_Entity1",
    "IntersectEntityName": "entity2_entity1",     // ← Or this one?
    "Entity1IntersectAttribute": "entity2id", 
    "Entity2IntersectAttribute": "entity1id"
  }
]
```

### 2. Field Name Conventions
```csharp
// ✅ CORRECT in Plugin:
"lmdm_country"           // Entity name
"lmdm_assetlocationtype" // Entity name

// ❌ WRONG in Plugin:  
"_lmdm_country_value"    // This is for Web API, not plugin
```

### 3. QueryExpression Pattern
```csharp
// ✅ CORRECT Many-to-Many Pattern:
var query = new QueryExpression("target_entity");
LinkEntity linkToIntersection = query.AddLink(
    linkToEntityName: "correct_intersection_table",
    linkFromAttributeName: "target_entity_key",
    linkToAttributeName: "intersection_target_field");

linkToIntersection.LinkCriteria.AddCondition(
    "intersection_parent_field", ConditionOperator.Equal, parentId);
```

---

## 🎉 Success Template

For quick replication, follow this proven pattern:

1. **Copy working plugin structure** from `GetLocationDetailsPlugin.cs`
2. **Modify field arrays** for your target entity  
3. **Update entity names** in QueryExpression calls
4. **Analyze metadata** to get correct intersection table names
5. **Test incrementally** - main entity first, then relationships
6. **Use trace logging** extensively during development
7. **Deploy and verify** with real data

This checklist ensures systematic development and helps avoid the common pitfalls encountered during the LocationDetails plugin development.

---

**Final Status**: 🚀 **PRODUCTION READY**  
**Execution Time**: ~375ms  
**Success Rate**: 100%  
**Data Retrieved**: Complete entity + all relationships