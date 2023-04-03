import json
import unittest
import requests

# LIKE '%webhook_test%'
EXAMPLE_JSON = json.loads('{"event": "order-sent", "data": {"createTime": "2023-03-10T15:51:57.783-07:00", "orgName": "BYU", "orgId": "5e21e6d86527d4001eb737a8", "siteName": "Wendy\'s", "siteId": "61489c6935473f002dfe9097", "locationId": "5f0cb4bcfe9585003165e48b", "orderChannel": "Kiosk", "diningOption": "To Go (Kiosk)", "source": "Kiosk (G)", "orderId": "640bb48f4f063e001bfb7f5b", "checkIds": [{"vendorName": "Default Vendor", "value": "290590", "name": "posCheckId"}], "isCancelled": false, "orderNumber": "webhook_test", "items": [{"posId": "13065690", "name": "Jr. Cheeseburger", "price": 199, "modGroups": [], "vendorName": "Default Vendor"}, {"posId": "13065712", "name": "10 PC. Crispy Chicken Nuggets", "price": 449, "modGroups": [{"posId": "14088626", "name": "Choose Sauce", "mods": [{"posId": "13075586", "name": "BBQ", "price": 0, "modGroups": []}, {"posId": "13075587", "name": "Honey Mustard", "price": 0, "modGroups": []}]}], "vendorName": "Default Vendor"}, {"posId": "13065690", "name": "Jr. Cheeseburger", "price": 199, "modGroups": [], "vendorName": "Default Vendor"}], "subTotal": 847, "taxTotal": 0, "tipTotal": 0, "discountNames": [], "discountTotal": 0, "total": 847, "refundedAmount": 0, "transactions": [{"cardType": "Atrium Student Card", "transactionType": "sale", "amount": 847, "lastFour": "1900", "gateway": "Atrium", "cardEntryMethod": "Swipe"}], "orderUrl": "https://admin.getbite.com/byu/wendys/kiosk#orders/640bb48f4f063e001bfb7f5b", "isTaxExempt": true, "serviceChargeTotal": 0, "serviceCharges": [], "guest": {"guestId": "15af2a8efd2311e3c9f56617"}}}')
EXAMPLE_JSON_2 = {"event": "order-sent",
                  "data": {
                      "createTime": "2023-03-10T15:51:57.783-07:00",
                      "orgName": "BYU",
                      "orgId": "5e21e6d86527d4001eb737a8",
                      "siteName": "Wendy's",
                      "siteId": "61489c6935473f002dfe9097",
                      "locationId": "5f0cb4bcfe9585003165e48b",
                      "orderChannel": "Kiosk",
                      "diningOption": "Campus Delivery (Contactless)",
                      "source": "Kiosk (G)",
                      "orderId": "640bb48f4f063e001bfb7f5b",
                      "checkIds": [
                          {"vendorName": "Default Vendor", "value": "290590", "name": "posCheckId"}],
                      "isCancelled": False,
                      "orderNumber": "webhook_test",
                      "items": [
                          {"posId": "13065690",
                           "name": "Jr. Cheeseburger",
                           "price": 199,
                           "modGroups": [],
                           "vendorName": "Default Vendor"},
                          {"posId": "13065712",
                           "name": "10 PC. Crispy Chicken Nuggets",
                           "price": 449,
                           "modGroups": [
                               {"posId": "14088626",
                                "name": "Choose Sauce",
                                "mods": [
                                    {"posId": "13075586",
                                     "name": "BBQ",
                                     "price": 0,
                                     "modGroups": []},
                                    {"posId": "13075587",
                                     "name": "Honey Mustard",
                                     "price": 0,
                                     "modGroups": []}
                                ]
                                }
                           ],
                           "vendorName": "Default Vendor"},
                          {"posId": "13065690",
                           "name": "Jr. Cheeseburger",
                           "price": 199,
                           "modGroups": [],
                           "vendorName":
                               "Default Vendor"}
                      ],
                      "subTotal": 847,
                      "taxTotal": 0,
                      "tipTotal": 0,
                      "discountNames": [],
                      "discountTotal": 0,
                      "total": 847,
                      "refundedAmount": 0,
                      "transactions": [
                          {"cardType": "Atrium Student Card",
                           "transactionType": "sale",
                           "amount": 847,
                           "lastFour": "1900",
                           "gateway": "Atrium",
                           "cardEntryMethod": "Swipe"}
                      ],
                      "orderUrl": "https://admin.getbite.com/byu/wendys/kiosk#orders/640bb48f4f063e001bfb7f5b",
                      "futureOrderTime": "2023-03-09T12:00:00.000-07:00",
                      "outpostDeliveryLocation": "USB",
                      "isTaxExempt": True,
                      "serviceChargeTotal": 0,
                      "serviceCharges": [],
                      "guest": {"guestId": "15af2a8efd2311e3c9f56617"}}
                  }

def make_test_data(order_count):
    example_dictionary = {
        "event": "order-sent",
        "data": {
            "createTime": "2023-03-9T00:01:00.000-07:00",
            "orgName": "BYU",
            "orgId": "5e21e6d86527d4001eb737a8",
            "siteName": "Cougar Crust",
            "siteId": "63c049be451025001cd46c35",
            "locationId": "63c049d977d51a001d706757",
            "orderChannel": "Contactless",
            "diningOption": "Campus Delivery (Contactless)",
            "source": "Browser (Desktop)",
            "orderId": f"webhook_test_order_id_{order_count}",
            "checkIds": [
                {
                    "vendorName": "Default Vendor",
                    "value": f"filler_pos_id_{order_count}",
                    "name": "posCheckId"
                }
            ],
            "isCancelled": False,
            "orderNumber": f"test_order_number_{order_count}",
            "items": [
                {
                    "posId": "15363736",
                    "name": "(TEST) Pepperoni Pizza",
                    "price": 0,
                    "modGroups": [
                        {
                            "posId": "15363751",
                            "name": "Size",
                            "mods": [
                                {
                                    "posId": "15363744",
                                    "name": "12\" Pizza",
                                    "price": 1199,
                                    "modGroups": []
                                }
                            ]
                        },
                        {
                            "posId": "15391620",
                            "name": "Remove Ingredients",
                            "mods": [
                                {
                                    "posId": "15372789",
                                    "name": "no Cheese",
                                    "price": 0,
                                    "modGroups": []
                                }
                            ]
                        }
                    ],
                    "vendorName": "Default Vendor"
                }
            ],
            "subTotal": 1199,
            "taxTotal": 99,
            "tipTotal": 0,
            "discountNames": [],
            "discountTotal": 0,
            "total": 1298,
            "refundedAmount": 0,
            "transactions": [
                {
                    "cardType": "Visa",
                    "transactionType": "sale",
                    "amount": 1298,
                    "lastFour": "0000",
                    "gateway": "FreedomPay",
                    "cardEntryMethod": "Manually Entered"
                }
            ],
            "orderUrl": "https://admin.getbite.com/byu/cougar-crust/kiosk#orders/fake_url",
            "futureOrderTime": "2023-03-09T12:00:00.000-07:00",
            "outpostDeliveryLocation": "USB",
            "isTaxExempt": False,
            "serviceChargeTotal": 0,
            "serviceCharges": [],
            "guest": {
                "guestId": "test_guestId",
                "email": "wtaylorh@byu.edu",
                "phoneNumber": "3107709405"
            }
        }
    }
    return example_dictionary


class CCRWebhookTests:

    def new_order_volume_testing(self, num_orders):
        webhook_url = 'https://biteorderfulfillmentapp.azurewebsites.net/api/httpNewGenericOrder?code=YoWlyjRmvDNMvpf9xnHMOUdAo2qg1RfhdsJxglAxB_iGAzFuwPFbsQ=='
        # webhook_headers = {"Content-Type": "application/json; charset=utf-8"}

        for i in range(1, num_orders+1):
            webhook_json = make_test_data(i)
            request_response = requests.post(webhook_url, json=EXAMPLE_JSON_2)
            print(request_response)


if __name__ == '__main__':
    # unittest.main()
    test_class = CCRWebhookTests()
    test_class.new_order_volume_testing(1)

