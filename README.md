# GradeView

GradeView is a small Flask app for checking school grades, GPA, assignments, report card cycles, and rank release status from the browser. It takes your existing HAC login and fetches your data for you, calculating your GPA and other good-to-know stats along the way!
If you want to see a demo of it, login wih username: admin1, password: admin1. Enjoy!

## How it works

- You open the app in your browser and log in with your school credentials.
- The backend creates a temporary session and talks to the PowerSchool/Home Access site on your behalf.
- It scrapes the grade pages, calculates GPA, and returns the results as JSON for the UI to render.
- The `/ranks` page checks whether ranks are out and shows the result live.

## Privacy

- Nothing is written to a database or saved to disk.
- Login state is kept only in memory and expires after a short time.
- The interface runs in your browser, and the app only uses your session while it is open.

## AI Usage
AI was used sparingly in this project. It was used to assist with front end design, but the calculations and everything going on in the background was done by me.
## Run it locally

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5003`.
