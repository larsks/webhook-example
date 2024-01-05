## Overview

This repository demonstrates several distinct techniques:

- How to validate signed GitHub notifications.

  How to use the mechanism described in "[Validating webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)" to verify that a request has been sent by GitHub. This can be used to prevent erroneous notifications or denial-of-service attacks if someone sends arbitrary requests to your notification endpoint.

- How to use the Slack "Block Kit" API to create formatted messages.

  The code in [`slack.py`](slack.py) includes a set of classes that provide a programmatic API for generating Slack messages.

- How to use OpenShift's [build support](https://docs.openshift.com/container-platform/4.14/cicd/builds/understanding-image-builds.html) to automatically build a container image when new code is pushed to a source repository.

- How to [automatically refresh a Deployment](https://docs.openshift.com/container-platform/4.14/openshift_images/triggering-updates-on-imagestream-changes.html) when a new image is built.
