Minimum Requirements:
- OpenAPI compatible api calling for llm
- Async fastAPI server deployed to GCP
- Test performance

## TODO:
- [x] Set up CD on GCP for cloud run
- [x] Add unauthenticated CORS for iteration
- [x] Add steps for CD
- [x] Build llm wrapper with fastAPI
- [x] deploy database for conversation history: 21
  - [x] user data
  - [x] userid in conversation table
  - [x] extra informaiton
  - [x] validate schema by checking with Madhavi
- [x] Setup checkpointer for agent memory
- [ ] Make api update database on queries
- [ ] Change llm to langgraph with history summarizer
- [ ] Test database operations
- [ ] Exception handling and second option for llm api: 24
- [ ] add auth: 24
  - [ ] add auth to database
- [ ] add logging and monitoring: 25
   - [ ] api call level id
   - [ ] track time to first byte
  ------------------------
- [ ] Test performance with script: 25
- [ ] Prompt tune: 26
- [ ] schema check again: 26
- [ ] Performance tune with caching
- [ ] Add CORS: 27
- [ ] Test integration with frontend
- [ ] CI
- [ ] private IP for cloud sql


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


## Connect to Postgres Database in Cloud Run
Link: [https://cloud.google.com/sql/docs/mysql/connect-run#console](https://cloud.google.com/sql/docs/mysql/connect-run#console)
1. Create a Cloud SQL instance of Postgresql
2. In the IAM section, for the service account of the project, add Cloud SQL Client role.
3. (Optional) Go to the Cloud SQL instance you've created, and click on edit and update to Postgres 17.
4. Go to cloud run instance -> edit and deploy new version -> Containers -> Settings -> Cloud SQL connections -> Add connection -> Deploy

## Add tables to Database
1. Create a connection pool to database
2. Store chat messages and session and user


Docs link: [https://colab.research.google.com/github/GoogleCloudPlatform/cloud-sql-python-connector/blob/main/samples/notebooks/postgres_python_connector.ipynb#scrollTo=9NYmcepFOM12](https://colab.research.google.com/github/GoogleCloudPlatform/cloud-sql-python-connector/blob/main/samples/notebooks/postgres_python_connector.ipynb#scrollTo=9NYmcepFOM12)
1. Create a user for the instance: go to Users tab in database instance on cloud console or

```bash
gcloud sql users create chef \
  --instance={instance_name} \
  --password="food"
```

2. Create a database on the instance `gcloud sql databases create backend --instance={instance-name}` to create a database called backend.
3. Add username, password, database to `.env` file. Look at .env.example file for exact variable names.
4. Add these variables to Secret Manager on cloud, give the service account for cloud run the permissions of Secret Manager Secret Accessor and add those secrets to Cloud Run instance.

## Setup checkpointer on Database
1. Install cloud sql auth proxy in project folder: [https://cloud.google.com/sql/docs/mysql/connect-instance-auth-proxy#mac-m1](https://cloud.google.com/sql/docs/mysql/connect-instance-auth-proxy#mac-m1)
2. Run cloud sql auth proxy `./cloud-sql-proxy <INSTANCE_CONNECTION_NAME>`
3. Run the `setup_checkpointer()` function.

## Update tables on API calls
1. Add persistance to chat

## Test that tables are getting properly updated




## Schema
Session table
|-sessionid
|-userid
|-heading?

Messages table
|-messageid
|-sessionid
|-taskid

Tasks table
|-taskid
|-task

Users Table
|-userid

Langgraph checkpointer
|-sessionid
|-messages
