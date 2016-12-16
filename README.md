Prototyping CI service
======================

The aim of this project is to find a way to add a new service to Continous Integration platforms such as travis-ci without building a full-fledged CI platform with things like github authentification, webhooks etc.

Just for example, this service will count the occurrence of `TODO` and retruns back the number of TODOs and their location in the code base. It also created badges, which look like these:

![Clear-CI](https://clear-ci.herokuapp.com/badges/id/4711.png)

## How does it work
Insert the following code into `.travis.yaml`:

```
bash <(curl https://clear-ci.herokuapp.com/static/uploader.sh) [Id] [src folder]
```

This will download a script directly from the service. The script upload selected src folder to the service and triggers a new build.

## Advantages
* very fast to integrate, great for people to test a proof-of-concept system before building the full platform
* very simple, no github authentification needed, no webhooks
* can change the upload script anytime from the server backend, allowing A/B testing

## Security Notes
This project should only be used to quickly test ideas and should obviously not be used in production in large scale.