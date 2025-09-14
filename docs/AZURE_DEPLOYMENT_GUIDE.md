# Career Compass Azure Deployment Configuration

## Prerequisites
- Azure CLI installed and logged in
- Access to Azure subscription
- Django project ready for deployment

## Step 1: Finding Available Regions for Your Subscription

Azure subscriptions (especially free, student, or trial accounts) often have region restrictions. The error you encountered indicates your subscription can't deploy to certain regions.

### Method 1: Use our helper script

```bash
# Make the script executable
chmod +x scripts/find_allowed_regions.sh

# Run the script to find allowed regions
./scripts/find_allowed_regions.sh
```

### Method 2: Manual checking

```bash
# Login to Azure
az login

# List available regions for your subscription
az account list-locations -o table

# Check App Service availability
az provider show --namespace Microsoft.Web --query "resourceTypes[?resourceType=='sites'].locations" -o json
```

Common regions that might work for limited subscriptions:
- eastus
- westus
- northeurope
- southeastasia
- australiaeast

## Step 2: Create Azure resources in an allowed region

Replace `East US` with one of the allowed regions from your subscription that you found in Step 1:

```bash
# Set variables
RESOURCE_GROUP="career-compass-group"  # Changed from career-compass
LOCATION="East US"  # Replace with an allowed region from Step 1
APP_NAME="career-compass"
APP_SERVICE_PLAN="ASP-careercompass"

# Create resource group
az group create --name $RESOURCE_GROUP --location "$LOCATION"

# Create app service plan
az appservice plan create --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --sku B1 \
    --location "$LOCATION" \
    --is-linux

# Create web app
az webapp create --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --runtime "PYTHON:3.13"
```

### Troubleshooting Regional Restrictions

If you continue to get errors about regional restrictions:

1. Try multiple different regions until you find one that works
2. Use the Azure Portal to create resources and let it suggest available regions
3. Contact Azure support to request access to specific regions
4. Consider upgrading from a free/student account to a pay-as-you-go subscription

## Step 3: Configure app settings

```bash
# Set Django-related environment variables
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP \
    --settings \
    DJANGO_SECRET_KEY="your-secure-secret-key" \
    DJANGO_DEBUG="False" \
    DJANGO_ALLOWED_HOSTS="$APP_NAME.azurewebsites.net,localhost,127.0.0.1" \
    DJANGO_SETTINGS_MODULE="core.settings"
```

### Setting up Python in Azure App Service

Azure App Service needs specific configurations for Python applications:

```bash
# Configure Python version
az webapp config set --name $APP_NAME --resource-group $RESOURCE_GROUP \
    --linux-fx-version "PYTHON|3.13"

# Enable startup command
az webapp config set --name $APP_NAME --resource-group $RESOURCE_GROUP \
    --startup-file "gunicorn --bind=0.0.0.0 --workers=4 core.wsgi:application"
```

Make sure gunicorn is in your requirements.txt file.

## Step 4: Deploy using GitHub Actions

1. Create Azure publish profile
```bash
az webapp deployment list-publishing-profiles \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --xml > publish_profile.xml
```

2. Add the content of publish_profile.xml as a GitHub Secret named `AZURE_WEBAPP_PUBLISH_PROFILE`

3. Add the GitHub workflow file for Azure deployment (.github/workflows/azure-deploy.yml)

## Step 5: Manual deployment (alternative)

```bash
# Package your application
mkdir -p deploy
cp -r applications accounts catalog core manage.py requirements.txt deploy/
cd deploy && zip -r ../career-campass-deploy.zip .

# Deploy the package
az webapp deployment source config-zip \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --src career-campass-deploy.zip
```

## Step 6: Verify deployment

```bash
# Get the URL of your web app
echo "Your app is deployed at: https://$APP_NAME.azurewebsites.net"
```

## Common Issues and Solutions

1. Region restrictions
   - Use `az account list-locations -o table` to see allowed regions
   - Deploy to one of the allowed regions from the list

2. Authentication issues
   - Ensure your Azure CLI is properly authenticated: `az login`
   - For CI/CD, use proper service principal credentials

3. Deployment failures
   - Check application logs: `az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP`
   - SSH into the app service: `az webapp ssh --name $APP_NAME --resource-group $RESOURCE_GROUP`
