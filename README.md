Minimum Requirements:
- OpenAPI compatible api calling for llm
- Async fastAPI server deployed to GCP
- Test performance

TODO:
- [x] Set up CD on GCP for cloud run
- [x] Add unauthenticated CORS for iteration
- [x] Add steps for CD
- [x] Build llm wrapper with fastAPI
- [ ] deploy database for conversation history: 21
  - [ ] user data
  - [ ] userid in conversation table
  - [ ] extra informaiton
  - [ ] validate schema by checking with Madhavi
- [ ] Setup testing for database: 21
- [ ] exception handling and second option for llm api: 24
- [ ] add auth: 24
  - [ ] add auth to database
- [ ] add logging and monitoring: 25
   - [ ] track time to first byte
- [ ] Test performance with script: 25
- [ ] Prompt tune: 26
- [ ] schema check again: 26
- [ ] Performance tune with caching
- [ ] Add CORS: 27 
- [ ] Test integration with frontend
- [ ] CI


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
In a new project on an account with basically all permissions, setting up CD from a github repo to Cloud Run:
1. Use Cloud build: create a new cloud build deployment, connect the github repo and maybe also need to select the region here.
2. Add Cloud Run Admin, Cloud Run Service Agent, Cloud Run Builder, Artifact Registry Administrater, Artifact Registry Service Agent, Kubernetes Engine Admin, Logs Writer, Service Account User roles atleast to the compute service acocunt for this project (some of these roles might not be required or be at higher level of access than required). 
3. Create the `cloudbuild.yaml` in your repo.
4. Push to github and it should deploy on Cloud Run.
5. Somewhere in this process there will be an option to send reports back to github, which you should accept so that the result of the build shows in the repo.

Documentation link: https://cloud.google.com/build/docs/deploying-builds/deploy-cloud-run
Note the extra option in our `cloudbuild.yaml` for logging which is required unless you have some logging already set up.


## Connect to Postgres Database
Link: [https://cloud.google.com/sql/docs/mysql/connect-run#console](https://cloud.google.com/sql/docs/mysql/connect-run#console)
1. Create a Cloud SQL instance of Postgresql
2. In the IAM section, for the service account of the project, add Cloud SQL Client role.
3. (Optional) Go to the Cloud SQL instance you've created, and click on edit and update to Postgres 17.
4. Go to cloud run instance -> edit and deploy new version -> Containers -> Settings -> Cloud SQL connections -> Add connection -> Deploy
