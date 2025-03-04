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
- [x] Make api update database on queries
- [x] Change llm to langgraph with history summarizer
- [x] Add backup llm
- [x] Deploy new version to GCP with cloud-sql-proxy: 28
- [x] Test database operations: 28
- [ ] Exception handling: 28
- [x] add auth: 3
  - [x] add auth table to database
  - [x] generate root user and dreambrdige user
  - [x] dependency injection for stream endpoint
  - [ ] make it so that the table is immutable?
  - [ ] prevent sql injection
- [x] Stop deleting messages in graph state
- [ ] add logging and monitoring: 4
   - [ ] api call level id
   - [ ] track time to first byte
  ------------------------
- [ ] Robust test functionality and performance with script: 5
- [ ] Prompt tune: 5
- [ ] schema check again: 5
- [ ] Edit CORS: 6/whenever client team is available
- [ ] Test integration with frontend: 6/whenever client team is available
- [ ] Performance tune with caching
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
1. Install cloud sql auth proxy in project folder: [https://cloud.google.com/sql/docs/mysql/connect-instance-auth-proxy#mac-m1)
2. Run cloud sql auth proxy `./cloud-sql-proxy -p <port> <INSTANCE_CONNECTION_NAME>`
3. Run the `setup_checkpointer()` function.


## Schema
Session table
|-session_id
|-user_id

Messages table
|-message_id
|-session_id
|-task_id

Tasks table
|-task_id
|-task

Users Table
|-user_id

Auth Table
|-auth_id
|-organization
|-hashed_password

Langgraph checkpointer


## Add Auth
1. Create an Auth table in the database with username and password columns.
2. Use argon-cffi library in python for hashing passwords
3. Authenticate user on each stream llm query
4. Create 2 users: root wizlearnr user and a dreambridge user
5. Credentials for each are stored in GCP secrets manager
