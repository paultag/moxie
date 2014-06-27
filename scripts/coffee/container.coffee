$(document).ready () ->
    ws = new WebSocket("ws://localhost:8888/websocket/stream/" + job + "/")
    ws.onopen = (e) -> 
        term = new Terminal({
            cols: 80,
            rows: 24,
            useStyle: false,
        })

        content = $("#main-content")
        term.open(content.get(0))

        ws.onmessage = (data) ->
            term.write(data.data)

        ws.onclose = (e) ->
            term.destroy()
