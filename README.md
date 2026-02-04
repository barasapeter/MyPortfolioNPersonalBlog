# Portfolio
Extended Portfolio &amp; Personal Blog

This Repository contains the source for my portfolio as a personal blog & journal.

and yes - it is public. this is not a normal portfolio, or even at its best, just a blog.

this is a full scale DevOps Playground, a mini infrastructure project.

## Implementation
- Web server: The project utilizes FastAPI as its primary web server. 
FastAPI is a modern Python framework for building APIs. 

The web server has been used for:
- Handle Requests:
    It enables the application to accept incoming HTTP requests from clients. The primary client platform is Browsers. If the project becomes a huge success (I hope it will), the
    application can be extended to handle traffic from mobile apps, USSD gateways and other servers.

- Routing:
    The web server determines which piece of code should handle the request based on the URL path and HTTP method (GET, POST, PUT, DELETE, etc.)

- executing business logic:
    the server is responsible for Database queries, data processing, authentication and authorization checks, file handling and integration with other APIs.

- Generating Responses:
    FastAPI has been used to format and return HTTP responses to the client.
    The dominant format used is JSON, HTML templates, files and even plain text (.md files with MDX)

- Middleware & Hooks:
    Logging requests/responses, Error handling, Authentication/authorization, Rate limiting ,Compression and caching
