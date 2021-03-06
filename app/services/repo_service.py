# -*- coding: utf-8 -*-

#
# Unless explicitly stated otherwise all files in this repository are licensed
# under the Apache 2 License.
#
# This product includes software developed at Datadog
# (https://www.datadoghq.com/).
#
# Copyright 2018 Datadog, Inc.
#

"""repo_service.py

Service-helpers for creating and mutating repo data.
"""

from . import APIService
from . import GitHubService
from .. import db
from ..models import Repo


class RepoService(APIService):
    """API persistent storage service.

    A class with the single responsibility of creating/mutating Repo
    data.
    """

    def __init__(self):
        """Initializes a new RepoService object."""
        self.github_service = GitHubService()

    def fetch(self):
        """Add all the repos to the database for the organization.

        Returns:
            None
        """
        fetched_repos = self.github_service.repos()
        persisted_repos = Repo.query.all()

        self._update_or_delete_records(fetched_repos, persisted_repos)
        self._create_records(fetched_repos, persisted_repos)

        # Persist the changes
        db.session.commit()

    def _update_or_delete_records(self, fetched_repos, persisted_repos):
        """Updates or deletes `Repo` records in the database.

        Args:
            fetched_repos (list(github.Repo)): The list of repos fetched
                from the GitHub API.
            persisted_repos (list(Repo)): The list of persisted
                repos fetched from the database.

        Returns:
            None
        """
        fetched_repo_ids = list(map(lambda x: x.id, fetched_repos))

        for record in persisted_repos:
            if record.github_repo_id in fetched_repo_ids:
                # Find the github repo by unique integer `github_repo_id`
                github_repo = list(
                    filter(
                        lambda x: x.id == record.github_repo_id,
                        fetched_repos
                    )
                )[0]

                # Update the attributes
                record.name = github_repo.name
                record.url = github_repo.html_url
            else:
                db.session.delete(record)

    def _create_records(self, fetched_repos, persisted_repos):
        """Inserts `Repo` records into the database.

        Args:
            fetched_repos (list(github.Repo)): The list of repos fetched
                from the GitHub API.
            persisted_repos (list(Repo)): The list of persisted
                repos fetched from the database.

        Returns:
            None
        """
        persisted_repo_ids = list(
            map(lambda x: x.github_repo_id, persisted_repos)
        )
        repos_to_create = list(
            filter(lambda x: x.id not in persisted_repo_ids, fetched_repos)
        )

        for github_repo in repos_to_create:
            github_repo_model = Repo(
                name=github_repo.name,
                url=github_repo.html_url,
                github_repo_id=github_repo.id
            )
            db.session.add(github_repo_model)
