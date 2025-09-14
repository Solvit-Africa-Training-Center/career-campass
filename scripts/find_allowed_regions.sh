#!/bin/bash

# Script to find available regions for your Azure subscription
# This script helps identify which regions you're allowed to deploy resources to

echo "Checking available regions for your subscription..."

# List all Azure locations
echo "All Azure regions:"
az account list-locations -o table

# Get subscription details
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "\nChecking policy restrictions for subscription: $SUBSCRIPTION_ID"

# Check resource provider availability
echo -e "\nChecking App Service availability in regions:"
az provider show --namespace Microsoft.Web --query "resourceTypes[?resourceType=='sites'].locations" -o json

# Try to create test resource groups in different regions to find allowed ones
echo -e "\nTesting resource group creation in common regions to find allowed ones:"

# List of regions to try
declare -a regions=("eastus" "eastus2" "westus" "westus2" "northeurope" "westeurope" 
                    "southeastasia" "eastasia" "australiaeast" "australiasoutheast"
                    "brazilsouth" "canadacentral" "canadaeast" "uksouth" "ukwest"
                    "francecentral" "southafricanorth" "uaenorth" "switzerlandnorth"
                    "germanywestcentral" "norwayeast" "japaneast" "koreacentral" "southcentralus")

# Timestamp for unique resource group names
TIMESTAMP=$(date +%s)

for region in "${regions[@]}"; do
    TEST_RG="cc-test-$region-$TIMESTAMP"
    echo -n "Testing $region: "
    result=$(az group create --name "$TEST_RG" --location "$region" 2>&1 || echo "Failed")
    
    if [[ $result == *"Failed"* ]] || [[ $result == *"DisallowedByAzure"* ]]; then
        echo "❌ Not allowed"
    else
        echo "✅ ALLOWED - You can deploy to this region!"
        # Delete the test resource group
        az group delete --name "$TEST_RG" --yes --no-wait
    fi
done

echo -e "\nTest complete. Use the regions marked as ALLOWED for your Career Compass deployment."
echo "Add the allowed region to your .github/workflows/azure-deploy.yml file."
