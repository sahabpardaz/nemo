from datetime import datetime


from dataclasses import dataclass

@dataclass
class Commit:
    sha: str
    author: str
    author_date: datetime
    committer: str
    commit_date: datetime
    title: str
    body: str
    is_merge: bool = False
