self.addEventListener("push",event=>{let data={};try{data=event.data.json();}catch{}event.waitUntil(self.registration.showNotification(data.title||"TaalimSpace",{body:data.body||"Новое уведомление",tag:data.tag,data:{url:"/notifications"}}));});
self.addEventListener("notificationclick",event=>{event.notification.close();event.waitUntil(clients.openWindow("/notifications"));});
