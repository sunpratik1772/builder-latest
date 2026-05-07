# Emergent Google Auth — Testing Playbook (saved per integration playbook)

## Step 1: Create Test User & Session
```
mongosh --eval "
use('test_database');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'test.user.' + Date.now() + '@example.com',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  created_at: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Test Backend
```
TOKEN=<from step 1>
curl -X GET https://copilot-align.preview.emergentagent.com/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```
Expect: 200 with {user_id, email, name, picture}

## Step 3: Browser
Set cookie `session_token=$TOKEN` on the preview domain and load the app.
Expect: lands directly on Studio (no /login redirect). Avatar shows initials top-right.

## Cleanup
```
mongosh --eval "
use('test_database');
db.users.deleteMany({email: /test\.user\./});
db.user_sessions.deleteMany({session_token: /test_session/});
"
```
