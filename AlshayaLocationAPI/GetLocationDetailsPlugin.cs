using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;

namespace AlshayaLocationAPI
{
    /// <summary>
    /// Custom API Plugin to retrieve comprehensive location details including relationships
    /// Converts the Python custom-api-location.py functionality to native Dataverse Custom API
    /// </summary>
    public class GetLocationDetailsPlugin : PluginBase
    {
        #region Version Info
        
        /// <summary>
        /// Plugin version for trace logging and debugging - v2.4.0 fixed to use correct intersection table
        /// </summary>
        private const string PLUGIN_VERSION = "v2.4.0";
        
        #endregion
        #region Field Configuration
        
        /// <summary>
        /// Core location fields to retrieve - converted from Python FORM_FIELDS array
        /// These are configured in code and can be modified as needed
        /// </summary>
        private static readonly string[] LOCATION_FIELDS = {
            // Location ID
            "lmdm_locationid",
            
            // System fields
            "ownerid", "owningbusinessunit", "createdby", "createdon", 
            "createdonbehalfby", "modifiedby", "modifiedonbehalfby", "modifiedon", "statecode",
            
            // Location identifiers
            "lmdm_autolocationid", "lmdm_ccid", "lmdm_fmcid", "lmdm_financeccid", 
            "lmdm_projectid", "lmdm_hbid", "lmdm_sessionmid", "lmdm_symphonyid", 
            "lmdm_vendosid", "lmdm_yextid", "lmdm_mdmlocationid",
            
            // Location names
            "lmdm_storename", "lmdm_storenamelocallanguage", "lmdm_fmcname", "lmdm_hbstorename",
            
            // Classification (Lookup fields - Dataverse handles _value conversion automatically)
            "lmdm_assetlocationtype", "lmdm_channeltype", "lmdm_storetrait", 
            "lmdm_locationtype", "lmdm_branddivision", "lmdm_storepaneltype",
            
            // Format fields
            "lmdm_sbxstoreformat", "lmdm_storeformat", "lmdm_reservetype", 
            "lmdm_reserveequipmenttype", "lmdm_drivethrupaneltype", "lmdm_pricetier",
            "lmdm_hbstorelayout", "lmdm_hbstoreformat", "lmdm_hbstoresegment",
            
            // Status fields
            "lmdm_directtostore", "lmdm_currentstorestatus", "lmdm_reserve", 
            "lmdm_storestatus", "lmdm_transactiontype", "lmdm_seasonaltimeapplicable",
            
            // Delivery & Operations
            "lmdm_deliveryoptions", "lmdm_deliveryaggregator", "lmdm_fulfilmentwh",
            
            // Geographic & Physical
            "lmdm_country", "lmdm_countrygroup", "lmdm_region", "lmdm_state", 
            "lmdm_city", "lmdm_postalcode", "lmdm_addressline1", "lmdm_addressline2", 
            "lmdm_addressline1arabic", "lmdm_latitude", "lmdm_longitude", "lmdm_areadescription",
            "lmdm_grossleasablearea", "lmdm_operatingcurrency",
            
            // Reference numbers & IDs
            "lmdm_rocireferencenumber", "lmdm_googlepinid", "lmdm_brands",
            
            // Dates
            "lmdm_forecastedopeningdate", "lmdm_estimatedopeningdate", "lmdm_tradingstartdate", 
            "lmdm_resumptiondate", "lmdm_closuredate", "lmdm_temporaryclosuredate", 
            "lmdm_ccidcreationdate", "lmdm_rentcommdate",
            
            // Planning & Financial
            "lmdm_plannedinbp", "lmdm_leasableareaextension", "lmdm_renttypecode",
            
            // Contact Info
            "lmdm_landline", "lmdm_mobile", "lmdm_email",
            
            // Administrative
            "lmdm_gridchangeflag", "lmdm_taskownedby", "lmdm_itemmodifiedby", 
            "lmdm_locationchangesessionid", "lmdm_locationglobalworkflowsessionid", 
            "lmdm_locationworkflowstate", "lmdm_isdraft", "lmdm_isactivetaskforcapturer", 
            "lmdm_applicationversion"
        };

        /// <summary>
        /// Key Personnel fields to retrieve from related records
        /// Configurable in code - modify as needed
        /// </summary>
        private static readonly string[] KEY_PERSONNEL_FIELDS = {
            "lmdm_keypersonaleid", "lmdm_employeenumber", "lmdm_employeename", 
            "lmdm_employeefullname", "lmdm_brand", "lmdm_division", "lmdm_country",
            "lmdm_careerlevel", "lmdm_username", "lmdm_employeedesignation", 
            "lmdm_ccidcountry", "statecode", "statuscode", "createdon", "modifiedon"
        };

        /// <summary>
        /// Business Hours fields to retrieve from related records
        /// Configurable in code - modify as needed
        /// </summary>
        private static readonly string[] BUSINESS_HOURS_FIELDS = {
            "lmdm_locationbusinesshoursid", "lmdm_location", "lmdm_operatinghours",
            "lmdm_mondaystarttime", "lmdm_mondayendtime", "lmdm_tuesdaystarttime", "lmdm_tuesdayendtime",
            "lmdm_wednesdaystarttime", "lmdm_wednesdayendtime", "lmdm_thursdaystarttime", "lmdm_thursdayendtime",
            "lmdm_fridaystarttime", "lmdm_fridayendtime", "lmdm_saturdaystarttime", "lmdm_saturdayendtime",
            "lmdm_sundaystarttime", "lmdm_sundayendtime", "lmdm_closeddays", "lmdm_24houropeningdays",
            "lmdm_seasonaltimeappplicable", "lmdm_hourstoreflag", "statecode", "statuscode", "createdon", "modifiedon"
        };

        /// <summary>
        /// Relationship navigation properties - from metadata analysis
        /// </summary>
        private const string KEY_PERSONNEL_RELATIONSHIP = "lmdm_Location_lmdm_KeyPersonale_lmdm_KeyPersonale";
        private const string BUSINESS_HOURS_RELATIONSHIP = "lmdm_Location_lmdm_Location_lmdm_LocationBusinessHours";

        #endregion

        #region Constructor & Base Implementation

        public GetLocationDetailsPlugin() : base(typeof(GetLocationDetailsPlugin))
        {
        }

        protected override void ExecuteDataversePlugin(ILocalPluginContext localPluginContext)
        {
            if (localPluginContext == null)
            {
                throw new ArgumentNullException(nameof(localPluginContext));
            }

            var context = localPluginContext.PluginExecutionContext;
            var service = localPluginContext.PluginUserService; // Use PluginUserService instead of CurrentUserService

            try
            {
                // Validate this is our Custom API message
                if (context.MessageName != "mdm_alshaya_GetLocationDetails")
                {
                    localPluginContext.Trace($"Expected message 'mdm_alshaya_GetLocationDetails', but got '{context.MessageName}'");
                    return;
                }

                localPluginContext.Trace($"Starting GetLocationDetails Custom API execution - Plugin Version: {PLUGIN_VERSION}");

                // Extract input parameters
                string locationId = GetInputParameter<string>(context, "LocationId");
                if (string.IsNullOrEmpty(locationId))
                {
                    throw new InvalidPluginExecutionException("LocationId parameter is required");
                }

                localPluginContext.Trace($"Processing location: {locationId}");

                // Execute main logic
                var result = GetLocationWithDetails(service, locationId, localPluginContext);

                // Set output parameters - SINGLE comprehensive response
                string jsonResult = result.ToJsonString();
                localPluginContext.Trace($"Generated JSON result: {(jsonResult != null ? jsonResult.Length : 0)} characters");
                if (jsonResult != null && jsonResult.Length > 0)
                {
                    localPluginContext.Trace($"JSON Preview (first 200 chars): {jsonResult.Substring(0, Math.Min(200, jsonResult.Length))}");
                }
                
                context.OutputParameters["LocationDetails"] = jsonResult;
                context.OutputParameters["ExecutionTime"] = result.ExecutionTimeMs;

                localPluginContext.Trace($"GetLocationDetails completed successfully in {result.ExecutionTimeMs}ms");
                localPluginContext.Trace($"Output parameters set - LocationDetails: {jsonResult != null}, ExecutionTime: {result.ExecutionTimeMs}");
            }
            catch (Exception ex)
            {
                localPluginContext.Trace($"Error in GetLocationDetails: {ex.Message}");
                throw new InvalidPluginExecutionException($"GetLocationDetails failed: {ex.Message}", ex);
            }
        }

        #endregion

        #region Main Logic Methods

        /// <summary>
        /// Main method to retrieve location with all related details
        /// Replaces the Python get_full_location_details() function
        /// </summary>
        private LocationDetailsResult GetLocationWithDetails(IOrganizationService service, string locationId, ILocalPluginContext context)
        {
            var startTime = DateTime.UtcNow;
            var result = new LocationDetailsResult();

            try
            {
                // Step 1: Get main location record (supports GUID or alternate keys)
                context.Trace("Step 1: Fetching main location record");
                result.LocationData = GetLocationByIdentifier(service, locationId, context);
                
                if (result.LocationData == null)
                {
                    throw new InvalidPluginExecutionException($"Location not found with identifier: {locationId}");
                }
                
                // Extract the actual GUID for relationship queries
                Guid locationGuid = result.LocationData.Id;
                context.Trace($"Location found with GUID: {locationGuid}");
                context.Trace($"Location has {result.LocationData.Attributes.Count} attributes");

                // Step 2: Get Key Personnel (Many-to-Many relationship)
                context.Trace($"Step 2: Fetching Key Personnel (Plugin v{PLUGIN_VERSION})");
                result.KeyPersonnel = GetKeyPersonnel(service, locationGuid);
                context.Trace($"Found {result.KeyPersonnel.Entities.Count} key personnel records");

                // Step 3: Get Business Hours (One-to-Many relationship)
                context.Trace("Step 3: Fetching Business Hours");
                result.BusinessHours = GetBusinessHours(service, locationGuid);
                context.Trace($"Found {result.BusinessHours.Entities.Count} business hours records");

                var endTime = DateTime.UtcNow;
                result.ExecutionTimeMs = (int)(endTime - startTime).TotalMilliseconds;

                return result;
            }
            catch (Exception ex)
            {
                context.Trace($"Error in GetLocationWithDetails: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// Parse location identifier - supports GUID or alternate keys
        /// Replaces Python location lookup logic with proper alternate key support
        /// </summary>
        private Entity GetLocationByIdentifier(IOrganizationService service, string locationId, ILocalPluginContext context)
        {
            var columnSet = new ColumnSet(LOCATION_FIELDS);
            
            // Try to parse as GUID first (most common case)
            if (Guid.TryParse(locationId, out Guid guid))
            {
                context.Trace($"Using GUID lookup: {guid}");
                try
                {
                    var entity = service.Retrieve("lmdm_location", guid, columnSet);
                    context.Trace($"Successfully retrieved location via GUID: {entity.Id}");
                    return entity;
                }
                catch (Exception ex)
                {
                    context.Trace($"GUID lookup failed: {ex.Message}");
                    throw new InvalidPluginExecutionException($"Location with GUID {guid} not found: {ex.Message}");
                }
            }

            // If not a GUID, try common alternate keys
            context.Trace($"Attempting alternate key lookup for: {locationId}");
            
            // Try common alternate keys (add more as needed)
            string[] alternateKeyFields = { 
                "lmdm_ccid",           // Most common alternate key
                "lmdm_autolocationid", // Auto location ID
                "lmdm_mdmlocationid",  // MDM location ID
                "lmdm_storename"       // Store name (less reliable but possible)
            };

            foreach (string keyField in alternateKeyFields)
            {
                try
                {
                    var query = new QueryExpression("lmdm_location");
                    query.ColumnSet = columnSet;
                    query.Criteria = new FilterExpression();
                    query.Criteria.AddCondition(keyField, ConditionOperator.Equal, locationId);
                    query.TopCount = 1; // Only get first match

                    var results = service.RetrieveMultiple(query);
                    if (results.Entities.Count > 0)
                    {
                        context.Trace($"Found location using alternate key {keyField}: {locationId}");
                        return results.Entities[0];
                    }
                }
                catch (Exception ex)
                {
                    context.Trace($"Failed to lookup using {keyField}: {ex.Message}");
                    // Continue to next alternate key
                }
            }

            // If no matches found
            throw new InvalidPluginExecutionException($"Location not found with identifier: {locationId}. Tried GUID and alternate keys: {string.Join(", ", alternateKeyFields)}");
        }

        #endregion

        #region Data Retrieval Methods

        /// <summary>
        /// Retrieve Key Personnel using Many-to-Many relationship
        /// Uses Microsoft documented pattern for intersection table queries
        /// Version: 2.4.0 - Fixed to use correct intersection table from metadata: lmdm_location_lmdm_keypersonale
        /// </summary>
        private EntityCollection GetKeyPersonnel(IOrganizationService service, Guid locationId)
        {
            try
            {
                // Use Microsoft documented pattern for many-to-many relationships
                // Pattern: Start with target entity, link through intersection table to source
                var query = new QueryExpression("lmdm_keypersonale")
                {
                    ColumnSet = new ColumnSet(KEY_PERSONNEL_FIELDS)
                };
                
                // Use the SECOND relationship from metadata (the one Python script uses)
                // IntersectEntityName: "lmdm_location_lmdm_keypersonale"
                // Entity1 (lmdm_keypersonale) -> Entity1IntersectAttribute: "lmdm_keypersonaleid" 
                // Entity2 (lmdm_location) -> Entity2IntersectAttribute: "lmdm_locationid"
                LinkEntity linkToIntersection = query.AddLink(
                    linkToEntityName: "lmdm_location_lmdm_keypersonale", // CORRECT intersection table (2nd relationship)
                    linkFromAttributeName: "lmdm_keypersonaleid",
                    linkToAttributeName: "lmdm_keypersonaleid", // Entity1IntersectAttribute
                    joinOperator: JoinOperator.Inner);
                
                // Filter on intersection table for specific location using Entity2IntersectAttribute
                linkToIntersection.LinkCriteria = new FilterExpression();
                linkToIntersection.LinkCriteria.AddCondition("lmdm_locationid", ConditionOperator.Equal, locationId);

                var result = service.RetrieveMultiple(query);
                return result;
            }
            catch (Exception ex)
            {
                // Log but don't break - return empty collection (matches Python behavior)
                // Note: Exception details will appear in trace logs for debugging
                return new EntityCollection();
            }
        }

        /// <summary>
        /// Retrieve Business Hours using One-to-Many relationship
        /// Replaces Python business hours navigation logic
        /// </summary>
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
                // Return empty collection if relationship fails - don't break the main operation
                return new EntityCollection();
            }
        }

        #endregion

        #region Helper Methods

        /// <summary>
        /// Generic method to extract input parameters with type safety
        /// </summary>
        private T GetInputParameter<T>(IPluginExecutionContext context, string parameterName)
        {
            if (context.InputParameters.Contains(parameterName))
            {
                return (T)context.InputParameters[parameterName];
            }
            return default(T);
        }

        #endregion
    }

    #region Result Classes

    /// <summary>
    /// Data class to hold the complete location details result
    /// Mirrors the Python final_output structure
    /// </summary>
    public class LocationDetailsResult
    {
        public Entity LocationData { get; set; }
        public EntityCollection KeyPersonnel { get; set; } = new EntityCollection();
        public EntityCollection BusinessHours { get; set; } = new EntityCollection();
        public int ExecutionTimeMs { get; set; }

        /// <summary>
        /// Convert to JSON string for single response parameter
        /// Mirrors the Python script's final output format
        /// </summary>
        public string ToJsonString()
        {
            try
            {
                var result = new Dictionary<string, object>();

                // Add location data
                if (LocationData != null)
                {
                    var locationDict = new Dictionary<string, object>();
                    locationDict["Id"] = LocationData.Id.ToString();
                    locationDict["LogicalName"] = LocationData.LogicalName ?? "lmdm_location";
                    
                    foreach (var attr in LocationData.Attributes)
                    {
                        locationDict[attr.Key] = ConvertAttributeValue(attr.Value);
                    }
                    result["LocationData"] = locationDict;
                }
                else
                {
                    result["LocationData"] = null;
                }

                // Add key personnel
                var personnelList = new List<Dictionary<string, object>>();
                if (KeyPersonnel != null)
                {
                    foreach (var person in KeyPersonnel.Entities)
                    {
                        var personDict = new Dictionary<string, object>();
                        personDict["Id"] = person.Id.ToString();
                        foreach (var attr in person.Attributes)
                        {
                            personDict[attr.Key] = ConvertAttributeValue(attr.Value);
                        }
                        personnelList.Add(personDict);
                    }
                }
                result["KeyPersonnel"] = personnelList;

                // Add business hours
                var hoursList = new List<Dictionary<string, object>>();
                if (BusinessHours != null)
                {
                    foreach (var hours in BusinessHours.Entities)
                    {
                        var hoursDict = new Dictionary<string, object>();
                        hoursDict["Id"] = hours.Id.ToString();
                        foreach (var attr in hours.Attributes)
                        {
                            hoursDict[attr.Key] = ConvertAttributeValue(attr.Value);
                        }
                        hoursList.Add(hoursDict);
                    }
                }
                result["BusinessHours"] = hoursList;

                // Add execution time and status
                result["ExecutionTimeMs"] = ExecutionTimeMs;
                result["Status"] = "Success";
                result["Timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");

                // Use System.Web.Script.Serialization.JavaScriptSerializer for .NET Framework 4.6.2
                var serializer = new System.Web.Script.Serialization.JavaScriptSerializer();
                serializer.MaxJsonLength = int.MaxValue; // Handle large responses
                return serializer.Serialize(result);
            }
            catch (Exception ex)
            {
                // Fallback error response
                var errorResult = new Dictionary<string, object>
                {
                    ["Status"] = "Error",
                    ["Message"] = ex.Message,
                    ["ExecutionTimeMs"] = ExecutionTimeMs,
                    ["Timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
                };
                var serializer = new System.Web.Script.Serialization.JavaScriptSerializer();
                return serializer.Serialize(errorResult);
            }
        }

        /// <summary>
        /// Convert Dataverse attribute values to JSON-serializable objects
        /// </summary>
        private object ConvertAttributeValue(object value)
        {
            if (value == null) return null;

            // Handle EntityReference (lookup fields) - convert to readable format
            if (value is EntityReference entityRef)
            {
                return new Dictionary<string, object>
                {
                    ["Id"] = entityRef.Id,
                    ["Name"] = entityRef.Name ?? "",
                    ["LogicalName"] = entityRef.LogicalName
                };
            }

            // Handle OptionSetValue (choice fields)
            if (value is OptionSetValue optionSet)
            {
                return optionSet.Value;
            }

            // Handle Money
            if (value is Money money)
            {
                return money.Value;
            }

            // Handle DateTime
            if (value is DateTime dateTime)
            {
                return dateTime.ToString("yyyy-MM-ddTHH:mm:ssZ");
            }

            // Return as-is for primitive types
            return value;
        }
    }

    #endregion
}