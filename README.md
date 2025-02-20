Minimum Requirements:
- OpenAPI compatible api calling for llm
- Async fastAPI server deployed to GCP
- Test performance

TODO:
- [x] Set up CD on GCP for cloud run
- [x] Add unauthenticated CORS for iteration
- [ ] Add steps for CD
- [x] Build llm wrapper with fastAPI
- [ ] Setup testing 
- [ ] deploy database for conversation history
- [ ] second option for llm api and exception handling
- [ ] Add CORS and auth
- [ ] Prompt tune
- [ ] Performance tune with caching
- [ ] add logging and monitoring
- [ ] Test performance and CI


## How to test API?

Steps: add developer as Cloud Run Invoker -> use gcloud auth print-identity-token in OAuth2 bearer

Detailed steps:
1. Select the checkbox next to the service in Cloud Run and go to permissions. Add email id of developer with Cloud Run Invoker role.
2. Sign in with gcloud cli using `gcloud auth login`
2. Make a curl request as follow:
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" <SERVICE_URL>
```

or use the identity token with OAuth2.0 Authorization in Postman.


## Enabling CD on GCP using Cloud Build to Cloud Run
 
