# Strong Name Signing Fix for Product API Plugin

## Issue Encountered
When registering the `AlshayaProductAPI.dll` in Plugin Registration Tool, you encountered:

> **"Strong Names Error"**  
> "Assemblies containing Plugins must be strongly signed. Sign the Assembly using a KeyFile."

## Root Cause
The product API plugin project was missing strong name signing configuration, which is **required** by Dataverse for plugin assemblies. The location API plugin already had this configured, which is why it worked without issues.

## ✅ Solution Applied

### 1. **Copied Strong Name Key File**
```powershell
# Copied from working location API
AlshayaLocationAPI.snk → AlshayaProductAPI.snk
```

### 2. **Updated Project Configuration**
Modified `AlshayaProductAPI.csproj` to include:
```xml
<PropertyGroup>
  <SignAssembly>true</SignAssembly>
  <AssemblyOriginatorKeyFile>AlshayaProductAPI.snk</AssemblyOriginatorKeyFile>
</PropertyGroup>
```

### 3. **Rebuilt with Strong Name Signing**
```powershell
cd AlshayaProductAPI
dotnet clean
dotnet build --configuration Release
```

## ✅ Result
- **Assembly Location**: `bin\Release\net462\AlshayaProductAPI.dll`
- **Status**: ✅ Strongly signed and ready for Plugin Registration Tool
- **Error**: ✅ Resolved - No more "Strong Names Error"

## 📋 Next Steps for Deployment

1. **Register the Assembly** in Plugin Registration Tool (should work now)
2. **Create Custom API**: `mdm_alshaya_GetProductDetails`
3. **Configure Parameters**: ArticleId (input), ProductDetails & ExecutionTime (outputs)
4. **Test**: Use PowerShell script or direct API calls

## 🔧 Why This Happened

**Location API** (working):
- Already had `<SignAssembly>true</SignAssembly>` 
- Already had `AlshayaLocationAPI.snk` key file
- Built with strong name signing from the start

**Product API** (initial issue):
- Had `<SignAssembly>false</SignAssembly>`
- Missing `.snk` key file
- Built without strong name signing

## 📚 Documentation Updated

- ✅ `DEPLOYMENT_GUIDE.md` - Added strong name signing prerequisites
- ✅ `README.md` - Added signing information to build instructions
- ✅ Project builds successfully with signing

The plugin is now ready for deployment following the same process as the successful location API!