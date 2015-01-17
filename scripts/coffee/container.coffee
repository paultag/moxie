
url = () -> 
    loc = window.location

    if loc.protocol == "https:"
        new_uri = "wss:"
    else
        new_uri = "ws:"

    new_uri += "//" + loc.host
    return new_uri



$(document).ready () ->
    root = url()

    ws = new WebSocket(root + "/websocket/stream/" + job + "/")
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
