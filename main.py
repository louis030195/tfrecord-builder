
import base64
import json
import logging
import os
import urllib.request # No conflict import ?
import requests
from flask import current_app, Flask, render_template, request

# Imports the Google Cloud client libraries
from google.cloud import storage
from google.cloud import datastore
from google.cloud import pubsub_v1

# Utils
from build_image_data import _process_image_files


app = Flask(__name__)

# Configure the following environment variables via app.yaml
# This is used in the push request handler to verify that the request came from
# pubsub and originated from a trusted source.
app.config['PUBSUB_VERIFICATION_TOKEN'] = \
    os.environ['PUBSUB_VERIFICATION_TOKEN']
app.config['PUBSUB_TOPIC'] = os.environ['PUBSUB_TOPIC']
app.config['PROJECT'] = os.environ['PROJECT_ID']


# Global list to storage messages received by this instance.
MESSAGES = []


# [START gae_flex_pubsub_index]
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html', messages=MESSAGES)

    data = request.form.get('payload', 'Example payload').encode('utf-8')

    # Consider initialzing the publisher client outside this function
    # for low latency publish.
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(
        current_app.config['PROJECT'],
        current_app.config['PUBSUB_TOPIC'])

    publisher.publish(topic_path, data=data)

    return 'OK', 200
# [END gae_flex_pubsub_index]


# [START gae_flex_pubsub_push]
@app.route('/pubsub/push', methods=['POST'])
def pubsub_push():
    if (request.args.get('token', '') !=
            current_app.config['PUBSUB_VERIFICATION_TOKEN']):
        return 'Invalid request', 400

    envelope = json.loads(request.data.decode('utf-8'))
    payload = base64.b64decode(envelope['message']['data']).decode('utf-8')

    if len(payload) < 5:
        return 'Incorrect URL', 500

    # If it's a video
    if payload[-4:] == '.mp4' or payload[-4:] == '.avi':
        # Call Frame Extractor
        url = 'https://frame-extractor-dot-{}.appspot.com/pubsub/push?token={}'.format(os.environ['PROJECT_ID'], os.environ['PUBSUB_VERIFICATION_TOKEN'])

        # Request with payload (video url)
        response = requests.post(
            url,
            data=json.dumps({
                "message": {
                    "data": base64.b64encode(
                        u'{}'.format(payload).encode('utf-8')
                    ).decode('utf-8')
                }
            })
        )
        return response.text, 200 # 'Video not implemented', 500

    # If it's not a video and not an image
    if payload[-4:] != '.jpg' and payload[-4:] != '.png' and payload[-5:] != '.jpeg':
        return 'Unhandled file type {}'.format(payload), 500

    treshold = os.environ['TRESHOLD']
    client = datastore.Client()
    # Then get by key for this entity
    query_frame = client.query(kind='Frame')
    query_frame.add_filter('predictions', '=', None)
    frames_to_process = list(query_frame.fetch())

    # If there are too few frames to process, return
    if len(frames_to_process) < treshold:
        return 'Not enough frames to build a tfrecord', 200

    print("Starting a job", len(frames_to_process), "images to process")

    # Instantiates a storage client
    storage_client = storage.Client()

    # The name for the bucket
    bucket_name = os.environ['BUCKET_NAME']

    # Get the bucket
    bucket = storage_client.get_bucket(bucket_name)

    # Get the list of tfrecords
    blobs = bucket.list_blobs(prefix='/batches')

    # Just extract the file names
    blobs = [int(blob.split('/')[-1].split('.')[0]) for blob in blobs]

    # Get last id + 1
    autoincrement = max(blobs if blobs else [0]) + 1

    imageUrls = []
    for f in frames_to_process:
        path = os.path.join('/tmp', f['imageUrl'].split('/')[-1])

        # Download the image locally
        urllib.request.urlretrieve(f['imageUrl'], path)

        # Store the absolute path in a list
        imageUrls.append(path)

    # Write a tfrecord with last id + 1 (autoincrement ...)
    # No need labels
    try:
        _process_image_files(autoincrement, imageUrls, [''] * len(imageUrls), [0] * len(imageUrls), 5)
    except:
        return 'Failed to build tfrecord', 500

    MESSAGES.append(payload)

    # Returning any 2xx status indicates successful receipt of the message.
    return 'TFRecord n°{} written'.format(autoincrement), 200
# [END gae_flex_pubsub_push]


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
