# Building Authentication the Right Way: Lessons from My Blogging App

When I started building this blogging application, authentication felt like one of those features that is *deceptively simple*. Log in a user, set a session, done — right?

Not quite.

As the project grew beyond a toy app, authentication quickly became a design problem touching **security, scalability, testing, and developer experience**. This post documents how I approached authentication, the alternatives I evaluated, the mistakes I avoided, and the final solution I implemented.

---

## Why Authentication Deserved Special Attention

This project is a server-rendered FastAPI application using Jinja2 templates. Users can:

- View public blog posts anonymously
- Log in to create posts and comments
- Maintain a session-like experience without server-side sessions

That last requirement was the turning point.

I wanted:
- Stateless infrastructure
- Clean separation between authentication and business logic
- A design that could later support APIs or SPAs
- Something that reflects **real-world, production patterns**

---

## The First Question: Sessions or Tokens?

Traditionally, server-rendered apps rely on **session-based authentication**:

- Session ID stored in a cookie
- Session data stored on the server (often Redis)
- Simple mental model, easy logout

I’ve used this approach before, and it works well.

However, sessions introduce:
- Stateful infrastructure
- Scaling considerations (sticky sessions or shared stores)
- Tight coupling between authentication and backend storage

Since FastAPI is API-first by nature, I explored **token-based authentication** as an alternative.

---

## Evaluating Authentication Options

Here were the main approaches I considered:

### 1. Bearer JWTs (Authorization headers)
Common for SPAs and mobile apps, but awkward for server-rendered templates:
- Browsers don’t automatically attach headers
- Requires JavaScript glue everywhere
- CSRF protection becomes tricky

Rejected for this app.

---

### 2. Traditional Sessions
Simple and proven, but:
- Requires server-side state
- Less flexible for future API expansion

Viable, but not ideal for my long-term goals.

---

### 3. JWTs in HTTP-only Cookies (Chosen)
This approach combines the best of both worlds:
- Stateless authentication
- Browser-native cookie handling
- Works naturally with server-rendered templates
- Easily extendable to APIs later

This became the final design.

---

## The Final Architecture

### Core Ideas
- **JWT access tokens** stored in HTTP-only cookies
- **Short-lived access tokens** (15 minutes)
- **Long-lived refresh tokens** (7 days)
- **CSRF protection** via double-submit cookie pattern
- Authentication handled via FastAPI dependencies

The browser automatically sends cookies with every request, so authentication feels like classic sessions — but without server-side storage.

---

## JWT Design Decisions

Each token includes:
- `sub`: user ID
- `type`: access or refresh
- `exp`: expiration timestamp

I deliberately kept payloads minimal to reduce risk if tokens are compromised.

---

## CSRF Protection

Because cookies are automatically attached by browsers, CSRF protection is mandatory.

I implemented the **double-submit cookie pattern**:
- A random CSRF token is stored in a readable cookie
- The same token must be sent in a header or form field
- Tokens are compared using constant-time comparison

This protects all state-changing endpoints without server-side storage.

---

## Optional Authentication for Public Pages

One design goal was allowing:
- Anonymous users to read blogs
- Authenticated users to post or comment

Instead of forcing authentication everywhere, I created two dependencies:

- `get_current_user` → strict (raises 401)
- `get_optional_user` → permissive (returns `None` if unauthenticated)

This keeps public routes clean while enforcing security where it matters.

---

## The Final Working Implementation

Below is the final, tested authentication core used in the project:

```python
# (code omitted here for brevity in the blog view)
# Full implementation includes:
# - JWT creation & verification
# - HTTP-only cookie handling
# - CSRF protection
# - Optional vs strict auth dependencies
# - Refresh token flow
````

This implementation was tested using:

* REST clients (verifying cookie behavior)
* Browser-based flows
* Manual token expiry testing
* Protected route enforcement

---

## Testing Philosophy

Authentication code is risky to change and easy to break silently.

My testing focus was:

* Verifying cookies are set correctly on login
* Ensuring protected routes reject unauthenticated users
* Confirming public routes remain accessible
* Manually testing token expiry and refresh behavior
* Verifying CSRF failures are correctly rejected

Rather than over-mocking, I tested **real request flows**, since authentication bugs often appear at integration boundaries.

---

## What I Learned

1. Authentication is architecture, not just code
2. Stateless systems require more upfront thinking
3. Cookies are not the enemy — misusing them is
4. FastAPI’s dependency system is perfect for auth
5. Security decisions should be explicit and documented

Most importantly: **simple solutions age better than clever ones**.

---

## Future Improvements

This system is intentionally minimal but extensible. Planned upgrades include:

* Switching from HS256 to RS256
* Refresh token rotation and revocation
* OAuth / OpenID Connect integration
* Role-based access control
* Automated security-focused tests

---

## Closing Thoughts

This authentication system isn’t the most complex one possible — and that’s intentional.

It’s:

* Secure
* Scalable
* Testable
* Understandable six months later

this reflects how I approach real-world engineering:
**understand the problem, evaluate tradeoffs, and choose clarity over cleverness.**

---

If you’re building something similar, my biggest advice is this:

> Treat authentication as a system design problem first — the code will follow.

