from test_learning import account

def test_private_profile_validation_and_session_restore(client):
    first=account(client,"profile_first","student")
    second=account(client,"profile_second","student")
    payload={"birth_date":"2001-04-12","time_zone":"Asia/Almaty"}
    response=client.patch("/api/profile",headers=first,json=payload)
    assert response.status_code==200
    assert response.json()["time_zone"]=="Asia/Almaty"
    assert client.get("/api/auth/me",headers=first).json()["birth_date"]=="2001-04-12"
    assert client.get("/api/profile",headers=second).json()["birth_date"] is None
    assert client.patch("/api/profile",headers=first,json={**payload,"time_zone":"Bad/Zone"}).status_code==422
    assert client.patch("/api/profile",headers=first,json={**payload,"birth_date":"2999-01-01"}).status_code==422
    assert client.patch("/api/profile",headers=first,json={**payload,"user_id":2}).status_code==422
    assert "Asia/Bishkek" in client.get("/api/profile/time-zones",headers=first).json()
    assert client.patch("/api/profile",headers=first,json={**payload,"birth_date":None}).json()["birth_date"] is None
