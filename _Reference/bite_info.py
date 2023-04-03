from datetime import date

############# DOMAIN AND URL CONSTANTS #############    
#STAGING_ENVIRONMENT_DOMAIN = "admin-staging"  # TODO: we need to clarify how the environment domain and the sandbox sub-domain differ
#STAGING_SANDBOX_SUB_DOMAIN = "api-staging"
ENVIRONMENT_DOMAIN = "admin"
SANDBOX_SUB_DOMAIN = "api"
    
API_VERSION = "v2"  # this is the API version, and is not the same as the X_MD_API_VERSION
X_MD_API_VERSION = "4"  # str_value must be set to '4' for the Reporting API (see https://documentation.getbite.com/#operation/ReportingOrdersDay)
REPORTING_ENDPOINT_URL = 'https://' + ENVIRONMENT_DOMAIN + '.getbite.com/api/' + API_VERSION + '/reporting/orders/day'  # NOTE: This path is specific to the ReportingOrdersDay api endpoint.
LOCATION_ENDPOINT_URL = 'https://' + ENVIRONMENT_DOMAIN + '.getbite.com/api/' + API_VERSION + '/locations'  # NOTE: This path is specific to the ReportingOrdersDay api endpoint.

# X_BITE_ORG_ID = "byu"  # Must be set to the brand id that you are working with. This str_value will be provided along with the sandbox environment.
# TODO: get X_BITE_ORG_ID from Bite (not urgent)
###################################################  


############# AUTHORIZATION CONSTANTS #############    
#STAGING_API_TOKEN = 'd2440f466f2473b6c10062a3ebf7489c:da69b2b474ca254cc403ecd6eb558be72de70423763bf0089e00a5b645d0e2986a63d410a1c5ebd4c525689ff39bafc711c49963af674e1e011f307e0baec9e8f8'
SANDBOX_API_KEY = '94a4c61677851c77703ee3d58745e412:75683378e557596346801323ed5916000698eac5bf40f0c17c8c3c004e691cae7146ad8fd3f28aedfcea90dfb3b3fb5bc4215fac781fe24d5d47075c4450f659f0' # saved in Azure Key Vault (ordering-apps/cougar-crust-vault) as 'bite-api-key' and Application Settings as 'bite_sandbox_api_key'
AUTHORIZATION_TOKEN = 'Bearer ' + SANDBOX_API_KEY  # [BITE]: Must be set to 'Bearer: <API_TOKEN>'.
###################################################    

############# PAYLOAD CONSTANTS ############# 
CONTENT_TYPE = 'application/json'  # this is (presumably) fixed for this endpoint
TODAY_DATE = str(date.today())  # [BITE]: <string> The date of the orders to retrieve in a YYYY-MM-DD format
# TODO: figure out what we are doing with all of the page and limit values in the API calls
LOCATIONS_PAGE_VALUE = 0
LOCATIONS_LIMIT_VALUE = 50
REPORTING_PAGE_VALUE = 0
REPORTING_LIMIT_VALUE = 50
###################################################

OUTPOST_DINING_OPTION_NAME = "Campus Delivery (Contactless)"
KEYS = {"FulfillmentSites": {"Blue-Ribbon Box": 1,
                            "Chick-Fil-A": 2,
                            "Papa John": 3,
                            "Aloha Plate": 4,
                            "Wendy's": 5,
                            "Milk and Cookies": 6,
                            "Subway": 7,
                            "Choices": 8,
                            "Taco Bell": 9,
                            "BYU-testing": 10,
                            "Creamery Marketplace": 11,
                            "Cloned - Creamery Market": 12,
                            "Cougar Crust": 13},
    "OutpostLocations": {'ASB': 1, 
                        'Creamery' : 2, 
                        'TNRB': 3, 
                        'USB': 4, 
                        'TEST': 5,
                        'Heritage Halls Building 2':6,
                        'Heritage Halls Building 3':7,
                        'Heritage Halls Building 4':8,
                        'Heritage Halls Building 5':9,
                        'Heritage Halls Building 6':10,
                        'Heritage Halls Building 7':11,
                        'Heritage Halls Building 8':12,
                        'Heritage Halls Building 9':13,
                        'Heritage Halls Building 10':14,
                        'Heritage Halls Building 11':15,
                        'Heritage Halls Building 12':16,
                        'Heritage Halls Building 13':17,
                        'Heritage Halls Building 14':18,
                        'Heritage Halls Building 15':19,
                        'Heritage Halls Building 16':20,},
    "DiningOptions": {'Campus Delivery (Contactless)': 1, 
                      'Catering (Contactless)': 2},
    "FulfillmentStatuses":  {'New': 1, 
                             'Prepared': 2, 
                             'Delivered': 3, 
                             'Collected': 4, 
                             'Cancelled': 9},
}