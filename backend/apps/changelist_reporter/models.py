import dateutil.parser


class ChangeListReport:
    def __init__(self, id: str, title: str, commit_sha: str, merge_time: str):
        self.id = id
        self.title = title
        self.commit_sha = commit_sha
        self.merge_time = dateutil.parser.parse(merge_time)
        self.report = None

    def __str__(self):
        return f'[{self.id}] {self.commit_sha} /{self.merge_time}/'

    def __repr__(self):
        return f'[{self.id}] {self.report.get("status")} {self.report.get("details")}'

    @classmethod
    def from_gitlab_merge_request_json(cls, gitlab_merge_request):
        """
        Gitlab merge request API has three kinds of commit hashes:
          - sha: last commit hash of merge request source branch
          - merge_commit_sha: hash of commit created in target branch by merge action
          - squash_commit_sha: hash of commit created in target branch by squash action

        Args:
            gitlab_merge_request: Json object of Gitlab merge request API
        """
        merge_request_squash_commit_hash = gitlab_merge_request.get('squash_commit_sha')
        merge_request_merge_commit_sha = gitlab_merge_request.get('merge_commit_sha')
        merge_request_commit_hash_in_default_branch = gitlab_merge_request.get('sha')

        if merge_request_squash_commit_hash is not None:
            merge_request_commit_hash_in_default_branch = merge_request_squash_commit_hash
        elif merge_request_merge_commit_sha is not None:
            merge_request_commit_hash_in_default_branch = merge_request_merge_commit_sha

        return cls(
            str(gitlab_merge_request.get('iid')),
            gitlab_merge_request.get('title'),
            merge_request_commit_hash_in_default_branch,
            gitlab_merge_request.get('merged_at')
        )
