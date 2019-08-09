# Python Google Cloud Pub/Sub for Google App Engine Flexible Environment
[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/louis030195/tfrecord-builder)

## Setup

Before you can run or deploy the sample, you will need to do the following:

1. Enable the Cloud Pub/Sub API in the [Google Developers Console](https://console.developers.google.com/project/_/apiui/apiview/pubsub/overview).

2. Create a topic and subscription.

        $ gcloud pubsub topics create topic_tfrecord
        $ gcloud pubsub subscriptions create sub_tfrecord \
            --topic topic_tfrecord \
            --push-endpoint \
                https://[your-app-id].appspot.com/pubsub/push?token=[your-token] \
            --ack-deadline 30

3. Update the environment variables in ``app.yaml``.

## Running locally

Install dependencies, preferably with a virtualenv:

    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt

Then set environment variables before starting your application:

    export GOOGLE_APPLICATION_CREDENTIALS=[path-to-json-cred]
    export PUBSUB_VERIFICATION_TOKEN=[your-verification-token]
    export PUBSUB_TOPIC=[your-topic]
    export BUCKET_NAME=[your-bucket]
    export PROJECT_ID=[your-project-id]
    python main.py

### Simulating push notifications
Assuming you have Frame entities in Datastore with imageUrl property pointing to their storage (on GCS ?)

    export PUBSUB_VERIFICATION_TOKEN=[your-verification-token]
    python test/call.py

## Running on App Engine

    gcloud app deploy

