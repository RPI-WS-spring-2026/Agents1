# Lab 6: JWT Authentication with Express (GitHub Codespaces)

Build a REST API with JWT (JSON Web Token) authentication from scratch. By the end of this lab, you'll have a working authentication system with user registration, login, and protected routes.

**Time:** ~1 hour
**Environment:** GitHub Codespaces (nothing to install locally)

---

## Opening Your Codespace

> **Important:** You must create your Codespace from **your own assignment repository** (the one GitHub Classroom created for you), not the template repo. This ensures your work is saved and pushed to the correct place for grading.

1. Accept the GitHub Classroom assignment using the link provided by your instructor
2. Go to **your** assignment repository (it will be named something like `authenticiation-inclass-yourusername`)
3. Click the green **Code** button, then the **Codespaces** tab
4. Click **Create codespace on main**
5. Wait for the environment to load (this takes 1-2 minutes the first time)

You'll get a full VS Code editor in your browser with Node.js 20 pre-installed and port 3000 ready to go.

**Verify you're in the right repo:** Run this in the Codespace terminal:

```bash
git remote -v
```

You should see your own repository URL (e.g., `github.com/RPI-WS-spring-2026/authenticiation-inclass-yourusername`), **not** the template repo.

> **Tip:** You can also open the Codespace in your local VS Code by clicking the three dots menu next to your Codespace and selecting "Open in Visual Studio Code."

---

## Part 1: Project Setup (~5 min)

Open the **Terminal** in your Codespace (`` Ctrl+` `` or **Terminal > New Terminal**).

**1. Initialize the project:**

```bash
npm init -y
```

**2. Install dependencies:**

```bash
npm install express jsonwebtoken bcryptjs
```

- **express** — Web framework for building the API
- **jsonwebtoken** — Create and verify JWTs
- **bcryptjs** — Hash passwords (pure JS, no native compilation needed)

**3. Create the server file:**

```bash
touch server.js
```

---

## Part 2: Basic Express Server (~10 min)

Click on `server.js` in the Explorer panel to open it, then write code to:

1. Require `express` and create an app on port 3000
2. Add `express.json()` middleware to parse JSON request bodies
3. Create a `GET /api/health` route that returns `{ status: 'ok' }`
4. Create a `GET /api/secret` route that returns `{ message: 'This is a secret message! 🔐' }`
5. Start the server with `app.listen`

> **Helpful docs:**
> - [Express "Hello World"](https://expressjs.com/en/starter/hello-world.html) — creating an app and starting the server
> - [Express routing](https://expressjs.com/en/starter/basic-routing.html) — defining GET/POST routes
> - [express.json() middleware](https://expressjs.com/en/api.html#express.json) — parsing JSON request bodies

**Test it:**

Start the server in your terminal with `--watch` mode so it **automatically reloads** whenever you save changes to `server.js`:

```bash
node --watch server.js
```

When the server starts, Codespaces will show a notification that port 3000 is available. You can ignore it — we'll test with curl.

> **Auto-reload:** From now on, you can leave this terminal running. Every time you save `server.js`, the server will restart automatically — no need to manually stop and restart it. Note: since we use in-memory storage, registered users will be cleared on each reload.

Open a **second terminal** (click the `+` button in the terminal panel) and test:

```bash
curl http://localhost:3000/api/health
```

Expected output:
```json
{"status":"ok"}
```

```bash
curl http://localhost:3000/api/secret
```

Expected output:
```json
{"message":"This is a secret message! 🔐"}
```

Both routes work without any authentication — we'll fix that soon.

> **Codespaces note:** `curl` commands use `localhost` because both terminals run inside the same Codespace. Port forwarding is handled automatically.

---

## Part 3: User Registration (~10 min)

Add registration functionality to `server.js`. The server will auto-reload when you save.

**1. Add bcrypt and an in-memory users store at the top of `server.js`** (after the existing `require` and `app` lines):

```js
const bcrypt = require('bcryptjs');

// In-memory user storage (resets when server restarts)
const users = [];
```

**2. Add the registration route** (before `app.listen`):

```js
// Register a new user
app.post('/api/register', async (req, res) => {
  const { username, password } = req.body;

  // Check if username and password were provided
  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password are required' });
  }

  // Check if user already exists
  if (users.find(u => u.username === username)) {
    return res.status(409).json({ error: 'Username already exists' });
  }

  // Hash the password
  const hashedPassword = await bcrypt.hash(password, 10);

  // Store the user
  users.push({ username, password: hashedPassword });

  res.status(201).json({ message: `User '${username}' registered successfully` });
});
```

**3. Test it:**

Save the file, then register a user:

```bash
curl -X POST http://localhost:3000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'
```

Expected output:
```json
{"message":"User 'alice' registered successfully"}
```

Try registering the same user again — you should get a 409 error:

```bash
curl -X POST http://localhost:3000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'
```

Expected output:
```json
{"error":"Username already exists"}
```

---

## Part 4: User Login + JWT (~10 min)

Now let's add login that returns a JWT.

**1. Add jsonwebtoken and a secret key at the top of `server.js`** (with the other `require` statements):

```js
const jwt = require('jsonwebtoken');

// Secret key for signing JWTs (in production, use an environment variable!)
const JWT_SECRET = 'your-secret-key-change-in-production';
```

**2. Add the login route** (before `app.listen`):

```js
// Login and receive a JWT
app.post('/api/login', async (req, res) => {
  const { username, password } = req.body;

  // Find the user
  const user = users.find(u => u.username === username);
  if (!user) {
    return res.status(401).json({ error: 'Invalid username or password' });
  }

  // Compare passwords
  const validPassword = await bcrypt.compare(password, user.password);
  if (!validPassword) {
    return res.status(401).json({ error: 'Invalid username or password' });
  }

  // Create a JWT
  const token = jwt.sign({ username: user.username }, JWT_SECRET, { expiresIn: '1h' });

  res.json({ token });
});
```

**3. Test it:**

Save the file, then register a user and log in:

```bash
# Register
curl -X POST http://localhost:3000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'

# Login
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'
```

Expected login output (your token will be different):
```json
{"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
```

Copy the token value — you'll need it in the next step.

> **What's in a JWT?** Paste your token at [jwt.io](https://jwt.io) to decode it. You'll see the header, payload (with your username and expiration), and signature.

---

## Part 5: Protect the Route (~10 min)

Now let's create middleware that verifies the JWT and protect the secret route.

**1. Add the authentication middleware** (before your routes):

```js
// Middleware to verify JWT
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // "Bearer TOKEN"

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid or expired token' });
    }
    req.user = user;
    next();
  });
}
```

**2. Update the secret route to use the middleware:**

Replace your existing `/api/secret` route with:

```js
// Protected route - requires valid JWT
app.get('/api/secret', authenticateToken, (req, res) => {
  res.json({
    message: 'This is a secret message! 🔐',
    user: req.user.username
  });
});
```

**3. Test it:**

Save the file, then go through the full flow:

```bash
# Register
curl -X POST http://localhost:3000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'

# Login (copy the token from the response)
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'
```

**Test WITHOUT a token (should fail with 401):**

```bash
curl http://localhost:3000/api/secret
```

Expected output:
```json
{"error":"Access token required"}
```

**Test WITH a valid token (replace `YOUR_TOKEN` with the actual token):**

```bash
curl http://localhost:3000/api/secret \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected output:
```json
{"message":"This is a secret message! 🔐","user":"alice"}
```

**Test with a garbage token (should fail with 403):**

```bash
curl http://localhost:3000/api/secret \
  -H "Authorization: Bearer not.a.real.token"
```

Expected output:
```json
{"error":"Invalid or expired token"}
```

The health endpoint should still work without a token:

```bash
curl http://localhost:3000/api/health
```

---

## Part 6: Refresh Tokens (~15 min)

Right now our login returns a single access token that expires in 1 hour. In production, access tokens are short-lived (15 minutes) and a **refresh token** is used to get new access tokens without making the user log in again.

**1. Add a refresh token store and a separate secret** (at the top of `server.js`, near `JWT_SECRET`):

```js
const REFRESH_SECRET = 'refresh-secret-change-in-production';

// In-memory refresh token storage
const refreshTokens = [];
```

**2. Update the login route to return both tokens:**

Replace the `// Create a JWT` section in your login route with:

```js
  // Create an access token (short-lived)
  const token = jwt.sign({ username: user.username }, JWT_SECRET, { expiresIn: '15m' });

  // Create a refresh token (long-lived)
  const refreshToken = jwt.sign({ username: user.username }, REFRESH_SECRET, { expiresIn: '7d' });
  refreshTokens.push(refreshToken);

  res.json({ token, refreshToken });
```

**3. Add a refresh endpoint** (before `app.listen`):

```js
// Get a new access token using a refresh token
app.post('/api/refresh', (req, res) => {
  const { refreshToken } = req.body;

  if (!refreshToken) {
    return res.status(401).json({ error: 'Refresh token required' });
  }

  // Check if the refresh token is in our store (not revoked)
  if (!refreshTokens.includes(refreshToken)) {
    return res.status(403).json({ error: 'Refresh token revoked or invalid' });
  }

  // Verify the refresh token
  jwt.verify(refreshToken, REFRESH_SECRET, (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid or expired refresh token' });
    }

    // Issue a new access token
    const newToken = jwt.sign({ username: user.username }, JWT_SECRET, { expiresIn: '15m' });
    res.json({ token: newToken });
  });
});
```

**4. (Optional) Add a logout endpoint that revokes the refresh token:**

```js
// Logout - revoke the refresh token
app.post('/api/logout', (req, res) => {
  const { refreshToken } = req.body;
  const index = refreshTokens.indexOf(refreshToken);
  if (index > -1) {
    refreshTokens.splice(index, 1);
  }
  res.json({ message: 'Logged out successfully' });
});
```

**5. Test it:**

Save the file, then test the full refresh flow:

```bash
# Register
curl -X POST http://localhost:3000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'

# Login — now returns both token and refreshToken
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'

# Use the refresh token to get a new access token
curl -X POST http://localhost:3000/api/refresh \
  -H "Content-Type: application/json" \
  -d '{"refreshToken": "YOUR_REFRESH_TOKEN"}'

# Logout (revoke the refresh token)
curl -X POST http://localhost:3000/api/logout \
  -H "Content-Type: application/json" \
  -d '{"refreshToken": "YOUR_REFRESH_TOKEN"}'

# Try refreshing again — should fail with 403
curl -X POST http://localhost:3000/api/refresh \
  -H "Content-Type: application/json" \
  -d '{"refreshToken": "YOUR_REFRESH_TOKEN"}'
```

> **Why two tokens?** Access tokens are short-lived so if stolen, the damage window is small. Refresh tokens are long-lived but can be revoked server-side, giving you a way to "log out" a user even though JWTs are stateless.

---

## Part 7: Stretch Goals & Discussion (~15 min)

### Stretch: Try an Expired Token

Modify the `expiresIn` value in your login route to a very short duration:

```js
const token = jwt.sign({ username: user.username }, JWT_SECRET, { expiresIn: '10s' });
```

Save the file (the server will auto-reload), register, log in, wait 10 seconds, then try to access the secret route. You should get a 403 error with "Invalid or expired token."

**Remember to change it back to `'1h'` when done.**

### Discussion Questions

1. **Where should JWTs be stored on the client?** What are the trade-offs between `localStorage`, `sessionStorage`, and HTTP-only cookies?

2. **Why do we hash passwords?** What would happen if we stored plain-text passwords and the database was breached?

3. **What is the `JWT_SECRET` and why is it important?** What would happen if someone obtained your secret key?

4. **Why use two separate secrets** (`JWT_SECRET` and `REFRESH_SECRET`)? What would happen if they were the same?

5. **What's the difference between a 401 and 403 response?** When did we use each one and why?

6. **What are some limitations of JWTs?** How would you "log out" a user if JWTs are stateless? (Hint: think about token revocation)

---

## Challenge: React Frontend (optional)

Build a simple React frontend that lets users register, log in, and access the protected route — all from the browser instead of curl.

No build tools needed — you'll use React via CDN script tags in a single HTML file.

### Setup

**1. Add static file serving to `server.js`** (after `app.use(express.json())`):

```js
const path = require('path');
app.use(express.static(path.join(__dirname, 'public')));
```

**2. Create the frontend file:**

```bash
mkdir -p public
touch public/index.html
```

### What to Build

Create `public/index.html` with a React app that has three sections:

1. **Register** — a form with username and password fields that calls `POST /api/register`
2. **Login** — a form with username and password fields that calls `POST /api/login` and stores the returned token
3. **Secret** — a button that calls `GET /api/secret` with the token in the `Authorization: Bearer <token>` header and displays the response

### Hints

- Use CDN script tags for React (no build step needed):
  ```html
  <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  ```
- Use `<script type="text/babel">` for your JSX code
- Use `React.useState` to track the token, messages, and form inputs
- Use `fetch()` to call your API endpoints:
  ```js
  const res = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await res.json();
  ```
- To send the token with a request:
  ```js
  const res = await fetch('/api/secret', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  ```
- Disable the "Get Secret" button when there's no token to show the auth flow visually

### Testing

After saving both files, visit `http://localhost:3000` in the Codespace browser (click the forwarded port URL in the **Ports** tab). You should be able to register, log in, and see the secret message — all without curl.

---

## Submitting Your Work

Your Codespace is already connected to your assignment repository. When you commit and push, your code goes directly to **your** repo — there's no need to fork or create a new repository.

Commit and push from the Codespace terminal:

```bash
git add server.js package.json package-lock.json
git commit -m "Complete JWT authentication lab"
git push
```

If you completed the React challenge, include the public folder:

```bash
git add public/
git commit -m "Add React frontend"
git push
```

Or use the **Source Control** panel in VS Code (the branch icon in the left sidebar) to stage, commit, and push.

> **Common mistake:** If `git push` fails with a permissions error, you may have opened a Codespace on the template repo instead of your own assignment repo. Close this Codespace and create a new one from your assignment repository (see [Opening Your Codespace](#opening-your-codespace)).

---

## Automated Grading

When you push your code to GitHub, an automated grading workflow runs 8 tests against your `server.js`:

1. Health check returns 200
2. Register a new user returns 201
3. Duplicate registration returns 409
4. Login with valid credentials returns 200 + token
5. Login with wrong password returns 401
6. Access protected route without token returns 401
7. Access protected route with valid token returns 200
8. Access protected route with garbage token returns 403

**To check your results:** Go to the **Actions** tab in your GitHub repository. A green check means all tests passed; a red X means one or more tests failed. Click into the workflow run to see which tests passed and which failed.

---

## Codespaces Tips

- **Stopping your Codespace:** Your Codespace will auto-stop after 30 minutes of inactivity. You can also stop it manually from [github.com/codespaces](https://github.com/codespaces).
- **Resuming:** Click on your Codespace from the list to pick up where you left off. All files and terminal state are preserved.
- **Port forwarding:** Codespaces automatically forwards port 3000. If you want to test the API from your local browser, click the forwarded port URL in the **Ports** tab at the bottom of the editor.
- **Multiple terminals:** Click `+` in the terminal panel to open additional terminals. You'll need at least two — one running `node --watch server.js` and one for curl commands.


