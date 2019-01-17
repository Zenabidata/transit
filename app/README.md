# How to set up

## To link with API

This web application will make a web request every 15 seconds. It will be expecting a JSON object similar to this one:
```
{"Train Stop Name": [
        {
        "Uptown":
            [
                {
                    "line": "C",
                    "name": "168 St",
                    "time": 1547683200
                }
            ]    
        },
        {
            "Lefttown":
                [
                    {
                        "line": "S",
                        "name": "Dab on Em St",
                        "time": 1547682600
                    },
                    {
                        "line": "C",
                        "name": "168 St",
                        "time": 1547683200
                    }
                ]    
        },
        {
            "Downtown":
                [
                    {
                        "line": "S",
                        "name": "Dab on Em St",
                        "time": 1547682600
                    },
                    {
                        "line": "C",
                        "name": "168 St",
                        "time": 1547683200
                    }
                ]    
        }
    ]
}
```

Once the API is set up and ready to accept requests, get the URL for the GET request and put in the URL parameter of the AJAX call (Line 10 of ```plugin.js```, if you have no idea what I just said.) Then it is set up!

---
If there are still issues with getting this running, check the logs! If this is complaining about a CORS issue, then it is a problem with the server, and not this application. 😉