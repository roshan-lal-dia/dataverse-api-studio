using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Query;
using Newtonsoft.Json;

namespace AlshayaProductAPI
{
    /// <summary>
    /// Custom API Plugin to retrieve comprehensive product/article details including relationships
    /// Converts the Python custom-api-product.py functionality to native Dataverse Custom API
    /// </summary>
    public class GetProductDetailsPlugin : PluginBase
    {
        #region Version Info
        
        /// <summary>
        /// Plugin version for trace logging and debugging - v1.0.1 fixed entity names (mdm_articles -> mdm_article)
        /// </summary>
        private const string PLUGIN_VERSION = "v1.0.4"; // Fixed relationship queries to use LinkEntity navigation pattern (like Location API success)
        
        #endregion
        #region Field Configuration
        
        /// <summary>
        /// Core product/article fields to retrieve - converted from Python FORM_FIELDS array
        /// These are configured in code and can be modified as needed
        /// </summary>
        private static readonly string[] ARTICLE_FIELDS = {
            // Primary identifiers
            "mdm_articleid", "mdm_article_id", "mdm_autoarticleid",
            
            // System fields
            "ownerid", "owningbusinessunit", "createdby", "createdon", 
            "createdonbehalfby", "modifiedby", "modifiedonbehalfby", "modifiedon", "statecode",
            "statuscode", "mdm_transactioncompleteddate",
            
            // Product codes and identifiers
            "mdm_aimscode", "mdm_itemcode", "mdm_legacyitemid", "mdm_variantcode",
            "mdm_productcode", "mdm_nutrientid", "mdm_plucode", "mdm_microsid",
            "mdm_barcode", "mdm_alternatesupplierid",
            
            // Product names and descriptions
            "mdm_articledescription", "mdm_articledescriptionarabic",
            "mdm_articlemarketingname", "mdm_articlemarketingnamearabic",
            "mdm_articlemarketingdescription", "mdm_articlemarketingdescriptionarabic",
            "mdm_recipename", "mdm_foodname", "mdm_productname", "mdm_simphonydescription",
            "mdm_description", "mdm_recipedescription", "mdm_logisticalvariantdescription", 
            "mdm_microsdescription", "mdm_ingredientlist", "mdm_storageinstructions",
            
            // Classification and categorization (lookup fields - Organization Service handles values automatically)
            "mdm_actioncode", "mdm_articlesourcing", "mdm_articlestatus", 
            "mdm_articletype", "mdm_brand", "mdm_brandmultiselect",
            "mdm_abcoption", "mdm_coreefficiency", "mdm_foodcategory",
            "mdm_itemtype", "mdm_assettype", "mdm_assettypes", "mdm_commonflag", 
            "mdm_goldenflag",
            
            // Product hierarchy (lookup fields - Organization Service format)
            "mdm_producthierarchylevel1", "mdm_producthierarchylevel2", 
            "mdm_producthierarchylevel3", "mdm_producthierarchylevel4",
            "mdm_producthierarchylevel5", "mdm_producthierarchylevel6",
            
            // Physical properties and measurements
            "mdm_articlebaseunit", "mdm_articlecaseunit", "mdm_articlestoreunit", 
            "mdm_requisitionunit", "mdm_conversionfactor", "mdm_baseconversionfactor",
            "mdm_pweight", "mdm_averageweight", "mdm_averageweightunit", "mdm_cbm",
            "mdm_casesperpallet", "mdm_productpacksize", "mdm_grossweight",
            "mdm_grossweightunit", "mdm_height", "mdm_minstoragetemperature",
            "mdm_maxstoragetemperature",
            
            // Pricing and financial
            "mdm_purchaseprice", "mdm_purchasepricecurrency", "mdm_purchasepriceunit",
            "mdm_purchasepriceflag", "mdm_foreigncost", "mdm_foreigncurrency", 
            "mdm_productcostprice", "mdm_productcostpriceunit", "mdm_costcontrol",
            
            // Inventory and supply chain
            "mdm_stockmanaged", "mdm_stockmanagedflag", "mdm_inventorymanageflag", 
            "mdm_directtostore", "mdm_minimumorderquantity", "mdm_moq",
            
            // Supplier information
            "mdm_suppliername", "mdm_supplierarticlecode", "mdm_supplieraddress", 
            "mdm_suppliercontactemailid", "mdm_supplierphonenumber", "mdm_suppliersite", 
            "mdm_supplierstatus", "mdm_suppliercategory", "mdm_suppliercurrency",
            "mdm_supplierid", "mdm_supplierdepartment", "mdm_supplierincoterms",
            "mdm_supplierlocation", "mdm_orderableunitid", "mdm_leadtime", 
            "mdm_sustainabilitytag", "mdm_tariffcode", "mdm_hscode",
            
            // Food safety and dietary
            "mdm_halal", "mdm_kosher", "mdm_glutenfree", "mdm_vegan", "mdm_vegetarian",
            "mdm_hazard", "mdm_expirable", "mdm_batchexpirycontrol", "mdm_shelflife",
            "mdm_shelflifeafterdefrosting", "mdm_shelflifeafteropening", "mdm_productshelflife",
            "mdm_productshelflifeunit", "mdm_storagetemperature", 
            "mdm_maycontainallergen", "mdm_foodcontactmaterial",
            
            // Recipe and nutrition
            "mdm_recipeid", "mdm_recipegroup", "mdm_numberofingredients", "mdm_oilfryingusage",
            "mdm_condimentusage", "mdm_consumableusage", "mdm_singleingredientitem",
            "mdm_servingsize", "mdm_servingsizeunit", "mdm_sourceofnutritioninformation",
            "mdm_isnutrientpostflag", "mdm_nutriticserrormessage",
            
            // Flags and operational settings
            "mdm_enabled", "mdm_enable3pl", "mdm_expenceflag", "mdm_expenseitem",
            "mdm_fileupload_flag", "mdm_fooditem", "mdm_pluflag", "mdm_goldenflag",
            "mdm_sellableflag", "mdm_sellablestatus", "mdm_proprietoryitem", "mdm_proprietoryitemflag",
            
            // Digital assets
            "mdm_digitalasset", "mdm_digitalassetlabel", "mdm_digitalassettype",
            
            // Additional properties
            "mdm_color", "mdm_market", "mdm_material", "mdm_manufacturer", "mdm_itemmodifiedby",
            "mdm_itemstatus", "mdm_simphonyid", "mdm_whoperationunit", "mdm_unitofmeasure"
        };

        /// <summary>
        /// Allergen relationship fields to retrieve from related records
        /// </summary>
        private static readonly string[] ALLERGEN_FIELDS = {
            "mdm_allergenid", "mdm_name", "mdm_allergenname", "mdm_description",
            "mdm_allergencode", "statecode", "statuscode", "createdon", "modifiedon"
        };

        /// <summary>
        /// Nutrient relationship fields to retrieve from related records
        /// </summary>
        private static readonly string[] NUTRIENT_FIELDS = {
            "mdm_lookupnutrientid", "mdm_name", "mdm_nutrientname", "mdm_nutrientcode",
            "mdm_unit", "mdm_nutrienttype", "statecode", "statuscode", "createdon", "modifiedon"
        };

        /// <summary>
        /// Article relationship fields for parent/child relationships
        /// </summary>
        private static readonly string[] ARTICLE_RELATIONSHIP_FIELDS = {
            "mdm_articlerelationshipid", "mdm_relationshiptype", "mdm_quantity",
            "mdm_unitofmeasure", "statecode", "statuscode", "createdon", "modifiedon"
        };

        /// <summary>
        /// Relationship navigation properties - from metadata analysis
        /// Based on the custom-api-product.py RELATIONSHIPS configuration
        /// </summary>
        private const string ALLERGEN_RELATIONSHIP = "mdm_articleallergenrelationship_Article_mdm_article";
        private const string NUTRIENT_RELATIONSHIP = "mdm_articlenutrientrelationship_Article_mdm_article";
        private const string CHILD_ARTICLES_RELATIONSHIP = "mdm_articlerelationship_ParentArticle_mdm_article";
        private const string PARENT_ARTICLES_RELATIONSHIP = "mdm_articlerelationship_ChildArticle_mdm_article";
        
        // Many-to-many relationships (if available)
        private const string MANY_TO_MANY_ALLERGENS = "mdm_Article_mdm_LookupAllergen_mdm_LookupAllergen";
        private const string MANY_TO_MANY_NUTRIENTS = "mdm_Article_mdm_LookupNutrient_mdm_LookupNutrient";

        #endregion

        #region Constructor & Base Implementation

        public GetProductDetailsPlugin() : base(typeof(GetProductDetailsPlugin))
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
                if (context.MessageName != "mdm_alshaya_GetProductDetails")
                {
                    localPluginContext.Trace($"Expected message 'mdm_alshaya_GetProductDetails', but got '{context.MessageName}'");
                    return;
                }

                localPluginContext.Trace($"Starting GetProductDetails Custom API execution - Plugin Version: {PLUGIN_VERSION}");

                // Extract input parameters
                string articleId = GetInputParameter<string>(context, "ArticleId");
                if (string.IsNullOrEmpty(articleId))
                {
                    throw new InvalidPluginExecutionException("ArticleId parameter is required");
                }

                localPluginContext.Trace($"Processing article: {articleId}");

                // Execute main logic
                var result = GetProductWithDetails(service, articleId, localPluginContext);

                // Set output parameters - comprehensive response
                string jsonResult = result.ToJsonString();
                localPluginContext.Trace($"Generated JSON result: {(jsonResult != null ? jsonResult.Length : 0)} characters");
                if (jsonResult != null && jsonResult.Length > 0)
                {
                    localPluginContext.Trace($"JSON Preview (first 200 chars): {jsonResult.Substring(0, Math.Min(200, jsonResult.Length))}");
                }
                
                context.OutputParameters["ProductDetails"] = jsonResult;
                context.OutputParameters["ExecutionTime"] = result.ExecutionTimeMs;

                localPluginContext.Trace($"GetProductDetails completed successfully in {result.ExecutionTimeMs}ms");
                localPluginContext.Trace($"Output parameters set - ProductDetails: {jsonResult != null}, ExecutionTime: {result.ExecutionTimeMs}");
            }
            catch (Exception ex)
            {
                localPluginContext.Trace($"Error in GetProductDetails: {ex.Message}");
                throw new InvalidPluginExecutionException($"GetProductDetails failed: {ex.Message}", ex);
            }
        }

        #endregion

        #region Main Logic Methods

        /// <summary>
        /// Main method to retrieve product with all related details
        /// Replaces the Python get_full_article_details() function
        /// </summary>
        private ProductDetailsResult GetProductWithDetails(IOrganizationService service, string articleId, ILocalPluginContext context)
        {
            var startTime = DateTime.UtcNow;
            var result = new ProductDetailsResult();

            try
            {
                // Step 1: Get main article record (supports GUID or alternate keys)
                context.Trace("Step 1: Fetching main article record");
                result.ProductData = GetArticleByIdentifier(service, articleId, context);
                
                if (result.ProductData == null)
                {
                    throw new InvalidPluginExecutionException($"Article not found with identifier: {articleId}");
                }
                
                // Extract the actual GUID for relationship queries
                Guid articleGuid = result.ProductData.Id;
                context.Trace($"Article found with GUID: {articleGuid}");
                context.Trace($"Article has {result.ProductData.Attributes.Count} attributes");

                // Step 2: Get Allergen Relationships
                context.Trace($"Step 2: Fetching Allergen Relationships (Plugin v{PLUGIN_VERSION})");
                result.AllergenRelationships = GetAllergenRelationships(service, articleGuid);
                context.Trace($"Found {result.AllergenRelationships.Entities.Count} allergen relationship records");

                // Step 3: Get Nutrient Relationships
                context.Trace("Step 3: Fetching Nutrient Relationships");
                result.NutrientRelationships = GetNutrientRelationships(service, articleGuid);
                context.Trace($"Found {result.NutrientRelationships.Entities.Count} nutrient relationship records");

                // Step 4: Get Child Article Relationships
                context.Trace("Step 4: Fetching Child Article Relationships");
                result.ChildArticleRelationships = GetChildArticleRelationships(service, articleGuid);
                context.Trace($"Found {result.ChildArticleRelationships.Entities.Count} child article relationship records");

                // Step 5: Get Parent Article Relationships
                context.Trace("Step 5: Fetching Parent Article Relationships");
                result.ParentArticleRelationships = GetParentArticleRelationships(service, articleGuid);
                context.Trace($"Found {result.ParentArticleRelationships.Entities.Count} parent article relationship records");

                var endTime = DateTime.UtcNow;
                result.ExecutionTimeMs = (int)(endTime - startTime).TotalMilliseconds;

                return result;
            }
            catch (Exception ex)
            {
                context.Trace($"Error in GetProductWithDetails: {ex.Message}");
                throw;
            }
        }

        /// <summary>
        /// Parse article identifier - supports GUID or alternate keys
        /// Replaces Python article lookup logic with proper alternate key support
        /// </summary>
        private Entity GetArticleByIdentifier(IOrganizationService service, string articleId, ILocalPluginContext context)
        {
            var columnSet = new ColumnSet(ARTICLE_FIELDS);
            
            // Try to parse as GUID first (most common case)
            if (Guid.TryParse(articleId, out Guid guid))
            {
                context.Trace($"Using GUID lookup: {guid}");
                try
                {
                    var entity = service.Retrieve("mdm_article", guid, columnSet);
                    context.Trace($"Successfully retrieved article via GUID: {entity.Id}");
                    return entity;
                }
                catch (Exception ex)
                {
                    context.Trace($"GUID lookup failed: {ex.Message}");
                    // Continue to alternate key lookup
                }
            }
            
            // Try alternate key lookups based on custom-api-product.py ALTERNATE_KEY_FIELDS
            var alternateKeys = new Dictionary<string, string>
            {
                { "mdm_aimscode", "aimscode" },
                { "mdm_itemcode", "itemcode" },
                { "mdm_barcode", "barcode" },
                { "mdm_articledescription", "articledescription" },
                { "mdm_article_id", "articleid" }
            };

            foreach (var keyPair in alternateKeys)
            {
                try
                {
                    context.Trace($"Attempting alternate key lookup: {keyPair.Key} = {articleId}");
                    
                    var query = new QueryExpression("mdm_article")
                    {
                        ColumnSet = columnSet,
                        Criteria = new FilterExpression()
                    };
                    query.Criteria.AddCondition(keyPair.Key, ConditionOperator.Equal, articleId);
                    
                    var results = service.RetrieveMultiple(query);
                    if (results.Entities.Count > 0)
                    {
                        context.Trace($"Successfully retrieved article via alternate key {keyPair.Key}: {results.Entities[0].Id}");
                        return results.Entities[0];
                    }
                }
                catch (Exception ex)
                {
                    context.Trace($"Alternate key lookup failed for {keyPair.Key}: {ex.Message}");
                    continue; // Try next alternate key
                }
            }
            
            context.Trace($"Article not found with any identifier method: {articleId}");
            return null;
        }

        /// <summary>
        /// Get allergen relationships using navigation property pattern
        /// Based on successful Location API intersection table pattern and Python script
        /// Uses navigation property: mdm_articleallergenrelationship_Article_mdm_article
        /// </summary>
        private EntityCollection GetAllergenRelationships(IOrganizationService service, Guid articleId)
        {
            try
            {
                // Use navigation property pattern like Location API success
                // Query the relationship entity directly using the article as filter
                var query = new QueryExpression("mdm_articleallergenrelationship")
                {
                    ColumnSet = new ColumnSet(true)
                };
                
                // Create a link to the main article to filter relationships
                LinkEntity articleLink = query.AddLink(
                    linkToEntityName: "mdm_article",
                    linkFromAttributeName: "mdm_article", // Lookup field in relationship table
                    linkToAttributeName: "mdm_articleid", // Primary key in article table
                    joinOperator: JoinOperator.Inner);
                
                // Filter for this specific article
                articleLink.LinkCriteria = new FilterExpression();
                articleLink.LinkCriteria.AddCondition("mdm_articleid", ConditionOperator.Equal, articleId);

                var result = service.RetrieveMultiple(query);
                return result;
            }
            catch (Exception)
            {
                // Return empty collection if relationship fetch fails
                return new EntityCollection();
            }
        }

        /// <summary>
        /// Get nutrient relationships using navigation property pattern
        /// Based on successful Location API intersection table pattern and Python script
        /// Uses navigation property: mdm_articlenutrientrelationship_Article_mdm_article
        /// </summary>
        private EntityCollection GetNutrientRelationships(IOrganizationService service, Guid articleId)
        {
            try
            {
                // Use navigation property pattern like Location API success
                var query = new QueryExpression("mdm_articlenutrientrelationship")
                {
                    ColumnSet = new ColumnSet(true)
                };
                
                // Create a link to the main article to filter relationships
                LinkEntity articleLink = query.AddLink(
                    linkToEntityName: "mdm_article",
                    linkFromAttributeName: "mdm_article", // Lookup field in relationship table
                    linkToAttributeName: "mdm_articleid", // Primary key in article table
                    joinOperator: JoinOperator.Inner);
                
                // Filter for this specific article
                articleLink.LinkCriteria = new FilterExpression();
                articleLink.LinkCriteria.AddCondition("mdm_articleid", ConditionOperator.Equal, articleId);

                return service.RetrieveMultiple(query);
            }
            catch (Exception)
            {
                // Return empty collection if relationship fetch fails
                return new EntityCollection();
            }
        }

        /// <summary>
        /// Get child article relationships using navigation property pattern
        /// Based on successful Location API intersection table pattern
        /// </summary>
        private EntityCollection GetChildArticleRelationships(IOrganizationService service, Guid articleId)
        {
            try
            {
                // Use navigation property pattern like Location API success
                var query = new QueryExpression("mdm_articlerelationship")
                {
                    ColumnSet = new ColumnSet(ARTICLE_RELATIONSHIP_FIELDS)
                };
                
                // Create a link to the parent article to filter relationships
                LinkEntity parentArticleLink = query.AddLink(
                    linkToEntityName: "mdm_article",
                    linkFromAttributeName: "mdm_parentarticle", // Lookup field in relationship table
                    linkToAttributeName: "mdm_articleid", // Primary key in article table
                    joinOperator: JoinOperator.Inner);
                
                // Filter for this specific article as parent
                parentArticleLink.LinkCriteria = new FilterExpression();
                parentArticleLink.LinkCriteria.AddCondition("mdm_articleid", ConditionOperator.Equal, articleId);

                return service.RetrieveMultiple(query);
            }
            catch (Exception)
            {
                // Return empty collection if relationship fetch fails
                return new EntityCollection();
            }
        }

        /// <summary>
        /// Get parent article relationships (articles that are parents of this article)
        /// </summary>
        /// <summary>
        /// Get parent article relationships using navigation property pattern
        /// Based on successful Location API intersection table pattern
        /// </summary>
        private EntityCollection GetParentArticleRelationships(IOrganizationService service, Guid articleId)
        {
            try
            {
                // Use navigation property pattern like Location API success
                var query = new QueryExpression("mdm_articlerelationship")
                {
                    ColumnSet = new ColumnSet(ARTICLE_RELATIONSHIP_FIELDS)
                };
                
                // Create a link to the child article to filter relationships
                LinkEntity childArticleLink = query.AddLink(
                    linkToEntityName: "mdm_article",
                    linkFromAttributeName: "mdm_childarticle", // Lookup field in relationship table
                    linkToAttributeName: "mdm_articleid", // Primary key in article table
                    joinOperator: JoinOperator.Inner);
                
                // Filter for this specific article as child
                childArticleLink.LinkCriteria = new FilterExpression();
                childArticleLink.LinkCriteria.AddCondition("mdm_articleid", ConditionOperator.Equal, articleId);

                return service.RetrieveMultiple(query);
            }
            catch (Exception)
            {
                // Return empty collection if relationship fetch fails
                return new EntityCollection();
            }
        }

        #endregion

        #region Helper Methods

        /// <summary>
        /// Safely get input parameter from execution context
        /// </summary>
        private T GetInputParameter<T>(IPluginExecutionContext context, string parameterName)
        {
            if (context.InputParameters.ContainsKey(parameterName))
            {
                return (T)context.InputParameters[parameterName];
            }
            return default(T);
        }

        #endregion

        #region Result Classes

        /// <summary>
        /// Result container for product details response
        /// Matches the structure from custom-api-product.py output
        /// </summary>
        public class ProductDetailsResult
        {
            public Entity ProductData { get; set; }
            public EntityCollection AllergenRelationships { get; set; } = new EntityCollection();
            public EntityCollection NutrientRelationships { get; set; } = new EntityCollection();
            public EntityCollection ChildArticleRelationships { get; set; } = new EntityCollection();
            public EntityCollection ParentArticleRelationships { get; set; } = new EntityCollection();
            public int ExecutionTimeMs { get; set; }

            /// <summary>
            /// Convert result to JSON string for Custom API response
        /// Uses same clean formatting as successful Location API implementation
        /// </summary>
        public string ToJsonString()
        {
            try
            {
                var result = new Dictionary<string, object>
                {
                    ["ProductData"] = EntityToDictionary(ProductData),
                    ["AllergenRelationships"] = EntityCollectionToDictionary(AllergenRelationships),
                    ["NutrientRelationships"] = EntityCollectionToDictionary(NutrientRelationships),
                    ["ChildArticleRelationships"] = EntityCollectionToDictionary(ChildArticleRelationships),
                    ["ParentArticleRelationships"] = EntityCollectionToDictionary(ParentArticleRelationships),
                    ["ExecutionTimeMs"] = ExecutionTimeMs,
                    ["Status"] = "Success",
                    ["Timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
                };

                // Use JsonConvert with clean formatting settings
                var settings = new JsonSerializerSettings
                {
                    Formatting = Formatting.None, // Clean, no extra whitespace
                    NullValueHandling = NullValueHandling.Ignore,
                    DateFormatString = "yyyy-MM-ddTHH:mm:ssZ"
                };
                return JsonConvert.SerializeObject(result, settings);
            }
            catch (Exception ex)
            {
                // Fallback error response with clean formatting
                var errorResult = new Dictionary<string, object>
                {
                    ["Status"] = "Error",
                    ["Message"] = ex.Message,
                    ["ExecutionTimeMs"] = ExecutionTimeMs,
                    ["Timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
                };
                var settings = new JsonSerializerSettings { Formatting = Formatting.None };
                return JsonConvert.SerializeObject(errorResult, settings);
            }
        }

        private Dictionary<string, object> EntityToDictionary(Entity entity)
            {
                if (entity == null) return null;

                var dict = new Dictionary<string, object>();
                dict["Id"] = entity.Id.ToString();
                dict["LogicalName"] = entity.LogicalName;

                foreach (var attr in entity.Attributes)
                {
                    dict[attr.Key] = attr.Value;
                }

                return dict;
            }

            private List<Dictionary<string, object>> EntityCollectionToDictionary(EntityCollection collection)
            {
                if (collection == null) return new List<Dictionary<string, object>>();

                return collection.Entities.Select(EntityToDictionary).ToList();
            }
        }

        #endregion
    }
}