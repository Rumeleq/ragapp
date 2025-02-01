# GrepEvent - Retrieval-Augmented Generation
Chat-bot app, where the user asks AI about tech events taking place in Poland.
Created using Python

## Table of contents
* Introduction
* Technologies
* Setup
* Screenshots
* Status
* Room for improvement
* Acknowledgements
* Contact

## Introduction

This is a project that was assigned to us by a [datarabbit.ai](https://www.datarabbit.ai/) company as a recruitment task.
We had to complete it in order to do an internship there.

This task was also an opportunity for us to learn new technologies, 
that we were unfamiliar with at the beginning.

## Technologies

- [Python](https://www.python.org/downloads/) _version: 3.13_, and its libraries:
  - [streamlit](https://docs.streamlit.io/) _version: 1.41.1_
  - [langchain](https://python.langchain.com/docs/introduction/) _version: 0.3_
  - [beautifulsoup](https://pypi.org/project/beautifulsoup4/) _version: 4.12_
  - and many other less important modules listed [here](./requirements.txt) 
- [Docker](https://docs.docker.com/) _version: 27.4_
- [Chroma](https://hub.docker.com/r/chromadb/chroma/tags) docker image _tag: 0.6.4.dev119_

## Setup

In order to run this app, docker is required. 

If you don't have docker installed on your computer yet, you can install it [here](https://docs.docker.com/get-started/get-docker/)

Once you have docker installed, follow these guidelines:
1. Clone the repo on your local machine 
   1. You can do it by running this command in terminal:
      1. ```git clone https://github.com/Rumeleq/ragapp.git```
2. Make sure you are in the project's root folder and run the command:
   1. ```docker-compose up```
   2. By running the above command, docker should:
      1. install the chromadb image (unless you have it already)
      2. run etl container after the chroma's healthcheck
      3. in etl container `scraper.py` script should scrape the data from websites:
         1. [crossweb](https://crossweb.pl/)
         2. [unikonferencje](https://unikonferencje.pl/)
         3. [eventbritte](https://www.eventbrite.com/)
      4. after the `scraper.py` finishes successfully, frontend container should run and expose the port 8501
   3. The whole process could take **even a few minutes**, especially when running for the first time
3. If you see in docker logs that frontend container is starting to run, you can [visit the webapp in browser](http://localhost:8501) 

## Screenshots

Correctly set up and working app looks like this:
![app in use](./images/use-of-app.jpg)
