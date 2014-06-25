ws = new WebSocket("ws://localhost:8888/websocket/stream/test-job-six/")

ws.onmessage = (e) -> 
    console.log(e)
