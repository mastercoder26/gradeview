# GradeView

GradeView is a small Flask app for checking school grades, GPA, assignments, report card cycles, and rank release status from the browser.

## How it works

- You open the app in your browser and log in with your school credentials.
- The backend creates a temporary session and talks to the PowerSchool/Home Access site on your behalf.
- It scrapes the grade pages, calculates GPA, and returns the results as JSON for the UI to render.
- The `/ranks` page checks whether ranks are out and shows the result live.

## Privacy

- Nothing is written to a database or saved to disk.
- Login state is kept only in memory and expires after a short time.
- The interface runs in your browser, and the app only uses your session while it is open.

## Run it locally

```bash
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5003`.
