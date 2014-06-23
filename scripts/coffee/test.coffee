

console.log("NOTIFICATION")
Notification.requestPermission((status) ->
  console.log(status)
  n = new Notification("title", {body: "notification body"})
)
