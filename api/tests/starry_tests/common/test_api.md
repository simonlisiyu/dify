
# workflow run
## streaming
curl -X POST 'http://192.168.1.152/v1/workflows/run' \
--header 'Authorization: Bearer app-FiUnCpxHj2Fz6ABuYuOtcIZd' \
--header 'Content-Type: application/json' \
--data-raw '{
"inputs": {
"query": "hello"
},
"response_mode": "streaming",
"user": "abc-123"
}'

## blocking
curl -X POST 'http://192.168.1.152/v1/workflows/run' \
--header 'Authorization: Bearer app-FiUnCpxHj2Fz6ABuYuOtcIZd' \
--header 'Content-Type: application/json' \
--data-raw '{
"inputs": {
"query": "hello"
},
"response_mode": "blocking",
"user": "abc-123"
}'