# App Layout

## Azure Trigger
### function.json
- **filename:** 'httpNewCougarCrustOrder/function.json'
- **inputs:** HTTP Request coming from the Bite Webhook. This webhook is fired each time that  Bite processes a new order from a site that we have told them to send us webhooks for.
- **operations**
    - Initiates a run of the app. This is the "Azure" portion of the app.
- **results:** Calls 'httpNewCougarCrustOrder/\_init_.py', passing the HTTP request as a parameter to the main() function in the \_init_.py file.
- **depends on**
    - calls 'httpNewCougarCrustOrder/\_init_.py'

### \_init_.py
- **filename:** 'httpNewCougarCrustOrder/\_init_.py'
- **inputs:** The HTTP Request recieved from the Bite Webhook.
- **operations**
    - Attempts to sanitize the JSON of the HTTP request and then passes the body of the request to the 'CougCrustOrdersFromHttp.new_order()' function.
- **results:** Returns a HTTP Response that includes how many new orders were inserted and how many duplicate orders it attempted to insert.
- **depends on**
    - calls 'httpNewCougarCrustOrder/CougCrustOrdersFromHttp.py'


## HTTP CCR App
### CougCrustOrdersFromHttp
- **filename:** 'httpNewCougarCrustOrder/CougCrustOrdersFromHttp.py'
- **inputs:** The sanitized JSON request body from the Bite Webhook HTTP request. 
- **operations**
    - checks to make sure that the correct version of Python is being used
    - Retrieves a list of POS id numbers associated with pizzas from the database by calling the 'ccr_db_object.get_pizza_pos_ids()' function
- **depends on**
    - calls 'ccr_db_object.get_pizza_pos_ids()' function without parameters
    
## Timer CCR App
