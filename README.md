## Overview

This repository demonstrates several distinct techniques:

- How to validate signed GitHub notifications.

  How to use the mechanism described in "[Validating webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)" to verify that a request has been sent by GitHub. This can be used to prevent erroneous notifications or denial-of-service attacks if someone sends arbitrary requests to your notification endpoint.

- How to use the Slack "Block Kit" API to create formatted messages.

  The code in [`slack.py`](slack.py) includes a set of classes that provide a programmatic API for generating Slack messages.

- How to use OpenShift's [build support](https://docs.openshift.com/container-platform/4.14/cicd/builds/understanding-image-builds.html) to automatically build a container image when new code is pushed to a source repository.

- How to [automatically refresh a Deployment](https://docs.openshift.com/container-platform/4.14/openshift_images/triggering-updates-on-imagestream-changes.html) when a new image is built.

## Running locally

For either of the following options, place your configuration settings in a file named `.env`:

```
FLASK_SLACK_WEBHOOK_URL=...
FLASK_VERIFY_WEBHOOK_SIGNATURE=false
```

The value of `FLASK_SLACK_WEBHOOK_URL` should be the webhook url of a [Slack Incoming Webhook].

You will probably want to disable webhook signature verification when running locally to make things easier to test.

[slack incoming webhook]: https://api.slack.com/messaging/webhooks

### Running using flask

Install the requirements into a virtual environment. I like using [pipenv] for this purpose:

```
pipenv install -r requirements.txt
```

[pipenv]: https://pipenv.pypa.io/en/latest/

Then run the app using the `flask` CLI:

```
pipenv run flask --app app:app run -p 8080
```

This will automatically read your configuration from your `.env` file.

You can verify the service is running by connecting to the `/healthz` endpoint:

```
$ curl localhost:8080/healthz
OK
```

You can submit a sample notification from the `samples` directory:

```
$ curl localhost:8080/hook/push -H content-type:application/json -H x-github-event:push \
  -d @samples/push-with-commits.json
{
  "status": "success"
}
```

While this should result in a successful notification, note that the links contained in the notification are bogus and will lead to 404 errors on github.

### Running in a container

Build the container image:

```
podman build -t webhook-receiver .
```

Run the image:

```
podman run -p 8080:8080 --env-file .env webhook-receiver
```

You can apply the same tests as shown in the previous section.

## Running in OpenShift

---

**WARNING**: Before you try running this example locally, you will want to make your own fork of the repository and then modify the manifests in the `manifests/` directory to reference your fork, rather than my repository. Because this project will automatically build and run code from the source repository, you want to be using a repository that is under your control.

---

### Configure the manifests

The manifests included here are design to be used with [kustomize].

[kustomize]: https://kustomize.io

Make a new directory `manifests/overlay/<yourname>` using `manifests/overlay/example` as a template:

```
cp -a manifests/overlay/example manifests/overlay/<yourname>`
```

You will find three files in your new overlay directory:

- `webhook-receiver.env`
- `github-buildconfig.env`
- `kustomzation.yaml`

In `webhook-receiver.env`, replace the values of `FLASK_GITHUB_WEBHOOK_SECRET` and `FLASK_SLACK_WEBHOOK_URL`:

```
FLASK_GITHUB_WEBHOOK_SECRET=<secret>
FLASK_SLACK_WEBHOOK_URL=<webhook url>
```

The value of `FLASK_GITHUB_WEBHOOK_SECRET` is a secret that you create; it will be used by GitHub to sign push notifications send to your web service. `FLASK_SLACK_WEBHOOK_URL` is the url for a [slack incoming webhook].

In `github-buildconfig.env`, replace the value of `WebHookSecretKey`:

```
WebHookSecretKey=<secret>
```

The value of `WebHookSecretKey` is a secret that you create; it will be used in the GitHub notification URL.

In `kustomization.yaml`, replace the repository url (look for `YOUR_USERNAME`) with the URL for your fork of this repository.

### Deploy the manifests

Deploy the manifests using `oc apply` (or `kubectl apply`):

```
oc apply -k manifests/overlay/<yourname>
```

### Configure your source repository

Get the notification URL for your BuildConfig by running:

```
oc describe buildconfig webhook-receiver
```

The result is a long URL that looks something like:

```
https://api.shift.nerc.mghpcc.org:6443/apis/build.openshift.io/v1/namespaces/lars-sandbox/buildconfigs/webhook-receiver/webhooks/<secret>/github
```

Replace `<secret>` with the value of `WebHookSecretKey` from `github-buildconfig.env`, and then use this URL to configure a webhook in the source repository. Do **not** enter any value in the "Secret" field when creating the webhook. This webhook will trigger your BuildConfig whenver you push changes to the source repository.

### Configure a notification repository
