import json
import os
import re

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://lis-hac.eschoolplus.powerschool.com"


# hel12
def login():
    sess = requests.Session()
    login_url = f"{BASE_URL}/HomeAccess/Account/LogOn"
    response = sess.get(login_url)
    soup = BeautifulSoup(response.text, "html.parser")

    username = os.getenv("HAC_USERNAME")
    password = os.getenv("HAC_PASSWORD")
    if not username or not password:
        print("Missing HAC_USERNAME or HAC_PASSWORD environment variables")
        return None

    login_data = {
        "Database": "10",
        "LogOnDetails.UserName": username,
        "LogOnDetails.Password": password,
    }

    login_form = soup.find("form")
    if login_form:
        hidden_inputs = login_form.find_all("input", type="hidden")
        for hidden in hidden_inputs:
            name = hidden.get("name")
            value = hidden.get("value", "")
            if name:
                login_data[name] = value

    login_response = sess.post(login_url, data=login_data, allow_redirects=True)
    if "LogOn" in login_response.url:
        print("Login failed")
        return None
    print("Login successful!")
    return sess


def explore_category_weights(sess):
    grades_url = f"{BASE_URL}/HomeAccess/Content/Student/Assignments.aspx"
    grades_response = sess.get(grades_url)
    soup = BeautifulSoup(grades_response.text, "html.parser")

    classes = soup.find_all("div", class_="AssignmentClass")
    print(f"Found {len(classes)} classes\n")

    for cls in classes[:3]:  # Look at first 3 classes
        course_name = cls.find("a", class_="sg-header-heading")
        print(
            f"\n=== {course_name.get_text(strip=True) if course_name else 'Unknown'} ==="
        )

        # Look for category weight table - usually in a div with class containing 'Category'
        # Or look for any div/span/element with weight percentages

        # Search for patterns like "60%", "40%", "30%" which indicate weights
        html_content = str(cls)
        weight_patterns = re.findall(
            r"(\w+[\s\w]*?)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%", html_content
        )
        if weight_patterns:
            print(f"Weight patterns found: {weight_patterns[:10]}")

        # Look for any nested tables that might contain category info
        all_tables = cls.find_all("table")
        for table in all_tables:
            table_class = table.get("class", [])
            table_id = table.get("id", "")
            if (
                "category" in str(table_class).lower()
                or "weight" in str(table_class).lower()
            ):
                print(f"Found potential category table: {table_class} / {table_id}")

        # Look for divs with category in class name
        category_divs = cls.find_all("div", class_=re.compile("category|weight", re.I))
        if category_divs:
            print(f"Found {len(category_divs)} category-related divs")
            for div in category_divs[:3]:
                print(f"  Div text: {div.get_text(strip=True)[:100]}")

        # Get all assignments and group by category
        assignment_table = cls.find("table", class_="sg-asp-table")
        if assignment_table:
            rows = assignment_table.find_all("tr", class_="sg-asp-table-data-row")

            categories = {}
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 7:
                    category = cells[3].get_text(strip=True)
                    try:
                        earned = float(cells[4].get_text(strip=True) or 0)
                        total = float(cells[5].get_text(strip=True) or 0)
                        weight = float(cells[6].get_text(strip=True) or 1)
                    except:
                        earned, total, weight = 0, 0, 1

                    if category not in categories:
                        categories[category] = {
                            "earned": 0,
                            "total": 0,
                            "count": 0,
                            "weights": [],
                        }
                    categories[category]["earned"] += earned * weight
                    categories[category]["total"] += total * weight
                    categories[category]["count"] += 1
                    categories[category]["weights"].append(weight)

            print(f"Categories with assignment counts:")
            for cat, data in categories.items():
                pct = (data["earned"] / data["total"] * 100) if data["total"] > 0 else 0
                print(f"  {cat}: {data['count']} assignments, {pct:.1f}% average")


if __name__ == "__main__":
    sess = login()
    if sess:
        explore_category_weights(sess)
