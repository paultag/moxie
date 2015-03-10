applicationID = ''
namespace = ''
session = null

initializeCastApi = () ->
    sessionRequest = new chrome.cast.SessionRequest(applicationID)
    apiConfig = new chrome.cast.ApiConfig(sessionRequest, sessionListener,
        receiverListener)
    chrome.cast.initialize(apiConfig, onInitSuccess, onError);

onInitSuccess = () -> 
    console.log("Success!")

onError = (message) ->
    console.log(message)

onSucess = (message) ->
    console.log(message)

sessionListener = (e) ->
    console.log(e)
    session = e
    session.addUpdateListener(sessionUpdateListener)

sessionUpdateListener = (isAlive) ->
    console.log(isAlive)
    if !isAlive
        session = null

receiverListener = (e) ->
    if e != "avaliable"
        alert("No casts :( ")

sendMessage = (msg) ->
    if session != null
        session.sendMessage(namespace, msg, onSucess.bind(this, message),
                            onError)
    else
        chrome.cast.requestSession((e) ->
                session = e
                sessionListener(e)
                session.sendMessage(namespace, msg, onSucess.bind(this, msg),
                                    onError)
            onError)

stopApp = () ->
    session.stop()

$("#cast").click(() ->
    initializeCastApi()
    console.log("Connect")
    sendMessage({
        type: "load",
        refresh: "20",
    }))
