# Install

You will need to have `poetry` installed.
Then, just execute `poetry install`.

# Run

`poetry run uvicorn demo_server.main:app`

# Example

```
# Use the latest API
~/repos/adaptapi_poc/demo_server » http GET localhost:8000/api/latest/ user="Ron" greeting="Good morning"
HTTP/1.1 200 OK
content-length: 30
content-type: application/json
date: Sat, 19 Aug 2023 11:22:15 GMT
server: uvicorn

{
    "message": "Good morning Ron"
}

# Use v1 API (default greeting, output is string and not dict)
~/repos/adaptapi_poc/demo_server » http GET localhost:8000/api/v1/ user="Ron"                      
HTTP/1.1 200 OK
content-length: 11
content-type: application/json
date: Sat, 19 Aug 2023 11:22:53 GMT
server: uvicorn

"Hello Ron"
```
