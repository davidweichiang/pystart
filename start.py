import requests
import bs4
import csv
import io
import urllib.parse
import re

### Configuration options

confname = "emnlp2018" # The name of the conference as found in the START URL
username = "chiang"    # A manager's START username
password = "xxxxxxxx"  # The START password; obviously this is not very secure

### End configuration options

session = requests.Session()
url = "https://www.softconf.com/{}/papers/login/scmd.cgi?scmd=login".format(confname)
r = session.post(url, data={'username': username, 'password': password})

def parse_table(table, text=True):
    """Iterate over the rows of an HTML table."""
    tbody = table.find('tbody')
    for row in tbody.children:
        if row.name != 'tr': continue
        if text:
            cells = [child.text.strip() for child in row.children if child.name == 'td']
        else:
            cells = [child for child in row.children if child.name == 'td']
        yield cells

def mail_archive():
    """Iterate over messages sent using the Mail Tool.
    Each row has cells: ID, Sender user, Recipient, Subject, Date.
    """
    
    url = "https://www.softconf.com/{}/papers/manager/scmd.cgi?scmd=mailarchive".format(confname)
    r = session.get(url)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    for row in parse_table(soup.find('table', id='t1')):
        yield row[:5]

def scratchpad():
    """Iterate over all reviewers in the Reviewer Scratchpad.

    Each row has cells: Username, Email, First Name, Last Name,
    Status, Managed By.
    """
    url = "https://www.softconf.com/{}/papers/manager/scmd.cgi?scmd=makeSpreadsheet".format(confname)
    r = session.post(url, data={'Type': 'scratchpad', 'spreadsheet_type': 'csv-utf8', 'SubmitButton': 'Spreadsheet'})
    reader = csv.reader(io.StringIO(r.text))
    next(reader)
    # 'Username', 'Email', 'First Name', 'Last Name', 'Status', 'Managed By'
    for row in reader:
        yield row[:6]
    
def submissions(*fields):
    """Iterate over all submitted papers.

    The caller should provide a list of desired fields. Possible
    values include (but this is not an exhaustive list): paperID,
    authors, allAuthorEmails, keywords, trackInfo.
    """
    
    url = "https://www.softconf.com/{}/papers/manager/scmd.cgi?scmd=makeSpreadsheet".format(confname)
    data = {'Type': 'submissions', 'spreadsheet_type': 'csv-utf8', 'SubmitButton': 'Spreadsheet'}
    for i, field in enumerate(fields):
        data['Field{{{}}}'.format(i)] = field
    r = session.post(url, data=data)
    reader = csv.reader(io.StringIO(r.text))
    next(reader)
    for row in reader:
        yield row[:-1]
    
def accounts(*fields):
    """Iterate over all user accounts.

    The caller should provide a list of desired fields. Possible field
    names are: _X_username, email{_X_username},
    firstname{_X_username}, lastname{_X_username},
    affiliation{_X_username}, keywords{_X_username},
    country{_X_username}, LoggedIn, AccessedAssignments, Access.
    """
    url = "https://www.softconf.com/{}/papers/manager/scmd.cgi?scmd=makeSpreadsheet".format(confname)
    data = {'Type': 'reviewers', 'spreadsheet_type': 'csv-utf8', 'SubmitButton': 'Spreadsheet'}
    for i, field in enumerate(fields):
        data['Field{{{}}}'.format(i)] = field
    r = session.post(url, data=data)
    reader = csv.reader(io.StringIO(r.text))
    next(reader)
    for row in reader:
        yield row[:-1]

def assignments(by='reviewer'):
    """Iterate over all reviewers and their assigned papers.

    The three fields are first name, last name, and user name; the
    remaining fields are the assigned papers.
    """
    
    url = "https://www.softconf.com/{}/papers/manager/scmd.cgi?scmd=makeSpreadsheet".format(confname)
    data = {'Type': 'assignments', 'IndexMethod': by, 'SubmitButton': 'Spreadsheet', 'spreadsheet_type': 'csv-utf8'}
    r = session.post(url, data=data)
    reader = csv.reader(io.StringIO(r.text))
    next(reader)
    for row in reader:
        firstname, lastname, username, *papers = row
        papers = papers[:-1]
        yield firstname, lastname, username, papers
    
def review_progress_by_reviewer():
    """Iterate over all reviewers and their progress.

    The fields are: user name, number of assigned papers, number of
    completed papers.
    """
    
    url = "https://www.softconf.com/{}/papers/manager/scmd.cgi?scmd=monitorReviews3&c_view=reviewer&backStack=".format(confname)
    r = session.get(url)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    for row in parse_table(soup.find('table', id='t1'), text=False):
        reviewer, _, *rest = row
        username = urllib.parse.parse_qs(urllib.parse.urlparse(reviewer.find('a')['href']).query)["reviewer"][0]
        assigned, completed = [int(node.text.strip()) for node in rest[:2]]
        yield username, assigned, completed

def review_information(*fields):
    """Iterate over reviews.

    The caller should provide a list of desired fields. Possible
    fields include (not an exhaustive list): paperID, trackInfo,
    reviewer, reviewerFirstName, reviewerLastName,
    ScoreField{Overall_Recommendation}.
    """
    
    url = "https://www.softconf.com/{}/papers/manager/scmd.cgi?scmd=makeSpreadsheet".format(confname)
    data = {'Type': 'customreviews', 'spreadsheetReviewsView': 'byReview', 'SubmitButton': 'Spreadsheet', 'spreadsheet_type': 'csv-utf8'}
    for i, field in enumerate(fields):
        data['Field{{{}}}'.format(i)] = field
    r = session.post(url, data=data)
    reader = csv.reader(io.StringIO(r.text))
    next(reader)
    for row in reader:
        yield row[:-1]

def review_progress_by_submission():
    """Iterate over all submissions and their review progress.

    The fields are: paper id, number of assigned reviews, number of
    completed reviews.
    """
    
    url = "https://www.softconf.com/{}/papers/manager/scmd.cgi?scmd=monitorReviews3&backStack=".format(confname)
    r = session.get(url)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    for row in parse_table(soup.find('table', id='t1'), text=False):
        paperid, title, _, *rest = row
        paperid = paperid.text.strip()
        assigned, completed = [int(node.text.strip()) for node in rest[:2]]
        yield paperid, assigned, completed

def tracks():
    """Iterate over all track names."""
    
    url = "https://www.softconf.com/{}/papers/manager/scmd.cgi?scmd=defineTracks".format(confname)
    r = session.get(url)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    tracks = soup.find('textarea', {'name': 'DefinedTracks'}).text.splitlines()
    # Characters that must be replaced with _ in URLs
    escape = " ()[],"
    for track in tracks:
        track = ''.join('_' if c in escape else c for c in track)
        yield track

def quotas():
    """Iterate over all reviewer quotas.

    Fields are: user name, quota."""
    
    urls = ["https://www.softconf.com/{}/papers/manager/scmd.cgi?scmd=bidsQuotas".format(confname)]
    for track in tracks():
        urls.append("https://www.softconf.com/{}/papers/track/{}/manager/scmd.cgi?scmd=bidsQuotas".format(confname, track))
    for url in urls:
        r = session.get(url)
        soup = bs4.BeautifulSoup(r.text, 'html.parser')
        for select in soup.find_all('select'):
            m = re.match(r'quota{(.*)}', select['name'])
            username = m.group(1)
            selected = select.find('option', {'selected': 'selected'})
            if selected is None or selected['value'] == "none":
                quota = None
            else:
                quota = int(selected['value'])
            yield username, quota

def final_versions():
    """Iterate over titles, authors, and abstracts.
    
    This is very slow, and I don't think you should have to use this;
    something went wrong in EMNLP 2018 and this was the most expedient
    way to get all the correct metadata.
    """
    
    url = "https://www.softconf.com/{}/papers/manager/scmd.cgi?scmd=manager&ToPage=monitorFinalSubmissions".format(confname)
    r = session.get(url)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    for row in parse_table(soup.find('table', id='t1'), text=False):
        id = row[0].text.strip()
        url = "https://www.softconf.com/{}/papers/manager/".format(confname) + row[1].find('a')['href']
        r1 = session.get(url)
        s1 = bs4.BeautifulSoup(r1.text, 'html.parser')
        long_title = s1.find('textarea', id='field_procTitle').text
        short_title = s1.find('textarea', id='field_procShortTitle').text
        i = 1
        authors = []
        while True:
            try:
                firstname = s1.find('input', id='item_spa_firstname_item_{}'.format(i))['value'].strip()
                lastname = s1.find('input', id='item_spa_lastname_item_{}'.format(i))['value'].strip()
            except TypeError:
                break
            i += 1
            authors.append("{} {}".format(firstname, lastname))
        if len(authors) == 1:
            authorstring = authors[0]
        else:
            authorstring = ", ".join(authors[:-1]) + " and " + authors[-1]
        abstract = s1.find('textarea', {'name':'abstract'}).text
        yield(id, " ".join(long_title.split()), authorstring, abstract)
