# Portfolio

Extended Portfolio & Personal Blog

This repository contains the source for my portfolio as a personal blog & journal.

And yes - it is public. This is not a normal portfolio, or even at its best, just a blog.

This is a full-scale DevOps Playground, a mini infrastructure project.

## Implementation

### Web Server

The project utilizes FastAPI as its primary web server. FastAPI is a modern Python framework for building APIs.

The web server has been used for:

**Handle Requests**
- Enables the application to accept incoming HTTP requests from clients
- Primary client platform is browsers
- If the project becomes a huge success (I hope it will), the application can be extended to handle traffic from mobile apps, USSD gateways, and other servers

**Routing**
- Determines which piece of code should handle the request based on the URL path and HTTP method (GET, POST, PUT, DELETE, etc.)

**Executing Business Logic**
- Database queries
- Data processing
- Authentication and authorization checks
- File handling
- Integration with other APIs

**Generating Responses**
- Formats and returns HTTP responses to the client
- Dominant format used is JSON, HTML templates, files, and plain text (parsed MARKDOWN strings)

**Middleware & Hooks**
- Logging requests/responses
- Error handling
- Authentication/authorization
- Rate limiting
- Compression and caching

### Database Server
This application uses Postgres as its primary database server. The blog posts are stored as TEXT (In markdown format) in `blogs` column.

You might come across JSONB a lot. I mean, really alot. Most of the content here are unstructured. Might as well migrate to Mongo DB later.
