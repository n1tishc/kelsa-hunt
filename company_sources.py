"""Public, session-backed careers feeds for the priority company watchlist."""
import http.cookiejar
import json
import urllib.parse
import urllib.request
from experience import experience_years
from datetime import datetime


PRIORITY_SOURCES = {"eightfold/ralliant/qualitrol", "dayforce/ibgllc/CANDIDATEPORTAL"}


class CareersSession:
    def __init__(self):
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.opener.addheaders = [("User-Agent", "Mozilla/5.0 (compatible; job-alert/2.0)")]

    def request(self, url, payload=None, headers=None, as_json=True):
        request_headers = dict(headers or {})
        data = None
        if payload is not None:
            data = json.dumps(payload).encode()
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=request_headers)
        with self.opener.open(request, timeout=10) as response:
            body = response.read()
        return json.loads(body) if as_json else body


def _record(uid, title, company, locations, url, posted, source):
    if not title or not locations or not all(isinstance(x, str) and x for x in locations):
        raise ValueError("job missing title or locations")
    return {"uid": uid, "title": title, "company": company, "locations": locations,
            "url": url, "posted": posted, "degrees": [], "category": "",
            "source": source, "feed_active": True}


def _page(rows, total, seen, id_field):
    if not isinstance(rows, list) or type(total) is not int or total < 0:
        raise ValueError("malformed careers page")
    ids = [str(row[id_field]) for row in rows]
    if any(x in seen or x in {"", "None"} for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("repeated or missing job IDs")
    seen.update(ids)
    if len(seen) > total or (not rows and len(seen) < total):
        raise ValueError("incomplete careers pagination")


def fetch_eightfold(slug):
    tenant, company = slug.split("/")
    base = f"https://{tenant}.eightfold.ai"
    session = CareersSession()
    # PCSX requires the anonymous cookie issued by the public careers page.
    session.request(f"{base}/careers?domain={tenant}.com", as_json=False)
    out, seen, expected = [], set(), None
    for _ in range(100):
        query = urllib.parse.urlencode({"domain": f"{tenant}.com", "query": "",
            "location": "", "start": len(seen),
            "filter_efcustom_text_operatingcompany": company})
        response = session.request(f"{base}/api/pcsx/search?{query}")
        if response.get("status") != 200:
            raise ValueError("unsuccessful Eightfold response")
        data = response["data"]
        rows, total = data["positions"], data["count"]
        if expected is not None and total != expected:
            raise ValueError("Eightfold inventory changed during pagination")
        expected = total
        _page(rows, total, seen, "id")
        for row in rows:
            companies = row["efcustomTextOperatingcompany"]
            if [x.casefold() for x in companies] != [company.casefold()]:
                raise ValueError("Eightfold company filter was not honored")
            out.append(_record(f"eightfold:{tenant}:{company}:{row['id']}", row["name"],
                companies[0], row["locations"],
                f"{base}/careers/job/{row['id']}", int(row.get("postedTs") or 0), "Eightfold"))
        if len(seen) == total:
            return out, True
    raise ValueError("Eightfold pagination limit exceeded")


def fetch_dayforce(slug):
    tenant, board = slug.split("/")
    base = "https://jobs.dayforcehcm.com"
    session = CareersSession()
    token = session.request(f"{base}/api/auth/csrf")["csrfToken"]
    if not token:
        raise ValueError("missing Dayforce CSRF token")
    out, seen, expected = [], set(), None
    for _ in range(100):
        data = session.request(f"{base}/api/geo/{tenant}/jobposting/search",
            payload={"clientNamespace": tenant, "jobBoardCode": board,
                     "cultureCode": "en-US", "paginationStart": len(seen), "distanceUnit": 0},
            headers={"X-CSRF-TOKEN": token})
        rows, total = data["jobPostings"], data["maxCount"]
        if expected is not None and total != expected:
            raise ValueError("Dayforce inventory changed during pagination")
        expected = total
        _page(rows, total, seen, "jobPostingId")
        for row in rows:
            if row["clientNamespace"] != tenant:
                raise ValueError("Dayforce tenant mismatch")
            locations = [loc["formattedAddress"] for loc in row["postingLocations"]]
            posted = row.get("postingStartTimestampUTC")
            timestamp = int(datetime.fromisoformat(posted.replace("Z", "+00:00")).timestamp()) if posted else 0
            out.append(_record(f"dayforce:{tenant}:{board}:{row['jobPostingId']}",
                row["jobTitle"], "Interactive Brokers" if tenant == "ibgllc" else tenant,
                locations, f"{base}/en-US/{tenant}/{board}/jobs/{row['jobPostingId']}",
                timestamp, "Dayforce"))
            out[-1]["experience_years"] = experience_years(row.get("jobDescription") or "")
        if len(seen) == total:
            return out, True
    raise ValueError("Dayforce pagination limit exceeded")
