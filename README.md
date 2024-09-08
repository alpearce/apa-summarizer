# APA File Summarizer 

## Project Overview

The goal is for shelter staff to be able to summarize long histories for dogs and cats so they can be placed in appropriate adoptive homes. We also want to be able to summarize medical histories so clinic staff can quickly find out what has been tried and what needs to happen next. Ultimately, we want an extremely simple app (choose file, click button, get summary) that can be easily maintained. In the meantime, we probably need to create a more interactive experimental demo in order to collect feedback from shelter staff on the results. 

The current iteration is work-in-progress attempt at a Python Flask web app that parses PDFs with PyMuPDF and summarizes the content using OpenAI. The app is deployed on Heroku.

## Cry for help 
I am a backend security engineer. This is not what I know how to do. All feedback welcome.

## Table of Contents

- [APA File Summarizer](#apa-file-summarizer)
  - [Project Overview](#project-overview)
  - [Cry for help](#cry-for-help)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Running the App Locally](#running-the-app-locally)
  - [Deploying to Heroku](#deploying-to-heroku)
  - [Environment Variables](#environment-variables)
  - [How it works](#how-it-works)
    - [Other possible summarization methods](#other-possible-summarization-methods)
  - [TODOs and future work](#todos-and-future-work)

## Installation

To set up the project locally, follow these steps:

1. **Clone the repository:**

    ```bash
    git clone https://github.com/alpearce/apa-summarizer.git
    cd apa-summary-app
    ```

2. **Create a virtual environment:**

    Use Python 3.12 to create a virtual environment.

    ```bash
    python3 -m venv venv
    ```

3. **Activate the virtual environment:**

   - **On macOS or Linux:**

    ```bash
    source venv/bin/activate
    ```

   - **On Windows:**

    ```bash
    venv\Scripts\activate
    ```

4. **Install dependencies:**

    Use the `requirements.txt` file to install all the required packages.

    ```bash
    pip install -r requirements.txt
    ```

5. **Adding new dependencies:**

    ```bash
    pip freeze > requirements.txt
    ```

## Running the App Locally

1. **Set environment variables:**

    Create a `.env` file in the root directory of your project and add your environment variables, like your OpenAI API key.

    ```bash
    OPENAI_API_KEY=<API key>
    FLASK_ENV=development
    ```

2. **Run the app using Gunicorn:**

    Use Gunicorn to run the app locally to simulate how it will run in production:

    ```bash
    gunicorn app:app
    ```

3. **Open the app in your web browser:**

    The app should now be running at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Deploying to Heroku

1. **Install the Heroku CLI:**

    Follow the instructions from [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) to install it.

2. **Log in to Heroku:**

    ```bash
    heroku login
    ```

3. **Add a Git remote for Heroku:**

    ```bash
    git remote add heroku https://git.heroku.com/apa-summarizer.git
    ```

4. **Deploy to Heroku:**

    ```bash
    git push heroku main
    ```

5. **Open the app in the browser:**

    ```bash
    heroku open
    ```

## Environment Variables

Make sure to set up the required environment variables in Heroku:

```bash
heroku config:set OPENAI_API_KEY=your_openai_api_key
```

## How it works

The inputs are large, and some include sections that are not totally relevant to the question (e.g. a "feeding plan" section for a behavior dog.) Some of the complexity of the problem has been selectively truncating the files for cost and length limits. The current algorithm is: 
- parse and clean each section of the PDF
- submit a list of section titles to AI and ask it which ones are most relevant
- summarize each of the relevant sections
- concatenate the list of summaries and create an overall summary 

### Other possible summarization methods

- prompt with a list of questions, such as "how does this dog do with other dogs" or "has she ever lived with children"

## TODOs and future work
- [ ] Add tests 
- [ ] Add logging
- [ ] Add a progress bar because the summaries take a while
- [ ] Performance optimizations 
- [ ] Add features for capturing feedback (job id, snapshots, form) 
- [ ] Create a flow for medical animals
- [ ] Experiment with other summarization methods
- [ ] Check in static CSS assets 
