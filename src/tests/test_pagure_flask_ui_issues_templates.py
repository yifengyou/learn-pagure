# -*- coding: utf-8 -*-

"""
 (c) 2017 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

"""

from __future__ import unicode_literals, absolute_import

import json
import unittest
import sys
import os

import pygit2
from mock import patch, MagicMock

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)

import pagure.lib.query
import tests


def create_templates(repopath):
    """Create a couple of templates at the specified repo."""
    clone_repo = pygit2.Repository(repopath)

    # Create the RFE template
    os.mkdir(os.path.join(repopath, "templates"))
    template = os.path.join(repopath, "templates", "RFE.md")
    with open(template, "w") as stream:
        stream.write("RFE\n###\n\n* Idea description")
    clone_repo.index.add(os.path.join("templates", "RFE.md"))
    clone_repo.index.write()

    # Commit
    tree = clone_repo.index.write_tree()
    author = pygit2.Signature("Alice Author", "alice@authors.tld")
    committer = pygit2.Signature("Cecil Committer", "cecil@committers.tld")
    commit = clone_repo.create_commit(
        "refs/heads/master",  # the name of the reference to update
        author,
        committer,
        "Add a RFE template",
        # binary string representing the tree object ID
        tree,
        # list of binary strings representing parents of the new commit
        [],
    )

    # Create the 2018-bid.md template
    template = os.path.join(repopath, "templates", "2018-bid.md")
    with open(template, "w") as stream:
        stream.write("Bid for 2018\n############\n\n* Location:")
    clone_repo.index.add(os.path.join("templates", "2018-bid.md"))
    clone_repo.index.write()

    # Commit
    tree = clone_repo.index.write_tree()
    author = pygit2.Signature("Alice Author", "alice@authors.tld")
    committer = pygit2.Signature("Cecil Committer", "cecil@committers.tld")
    commit = clone_repo.create_commit(
        "refs/heads/master",  # the name of the reference to update
        author,
        committer,
        "Add a RFE template",
        # binary string representing the tree object ID
        tree,
        # list of binary strings representing parents of the new commit
        [commit.hex],
    )

    # Create the default.md template
    template = os.path.join(repopath, "templates", "default.md")
    with open(template, "w") as stream:
        stream.write("Report your issue")
    clone_repo.index.add(os.path.join("templates", "default.md"))
    clone_repo.index.write()

    # Commit
    tree = clone_repo.index.write_tree()
    author = pygit2.Signature("Alice Author", "alice@authors.tld")
    committer = pygit2.Signature("Cecil Committer", "cecil@committers.tld")
    clone_repo.create_commit(
        "refs/heads/master",  # the name of the reference to update
        author,
        committer,
        "Add a default template",
        # binary string representing the tree object ID
        tree,
        # list of binary strings representing parents of the new commit
        [commit.hex],
    )


class PagureFlaskIssuesTemplatetests(tests.Modeltests):
    """ Tests for flask issues controller of pagure """

    @patch("pagure.lib.git.update_git", MagicMock(return_value=True))
    @patch("pagure.lib.notify.send_email", MagicMock(return_value=True))
    def setUp(self):
        """ Set up the environnment, run before every tests. """
        super(PagureFlaskIssuesTemplatetests, self).setUp()

        pagure.config.config["TICKETS_FOLDER"] = os.path.join(
            self.path, "tickets"
        )

        tests.create_projects(self.session)
        tests.create_projects_git(os.path.join(self.path, "repos"), bare=True)
        tests.create_projects_git(os.path.join(self.path, "tickets"))

        # Add a couple of templates to test2
        repopath = os.path.join(self.path, "tickets", "test2.git")
        create_templates(repopath)

        # Add a couple of templates to somenamespace/test3
        repopath = os.path.join(
            self.path, "tickets", "somenamespace", "test3.git"
        )
        create_templates(repopath)

    def test_new_issue_no_template(self):
        """Test the new_issue endpoint when the project has no templates."""

        user = tests.FakeUser()
        with tests.user_set(self.app.application, user):
            output = self.app.get("/test/new_issue")
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<h4 class="font-weight-bold mb-4">New Issue</h4>\n',
                output_text,
            )
            self.assertNotIn("Issue Templates", output_text)

    def test_new_issue_w_template(self):
        """ Test the new_issue endpoint when the project has templates. """

        user = tests.FakeUser()
        with tests.user_set(self.app.application, user):
            output = self.app.get("/test2/new_issue")
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<h4 class="font-weight-bold mb-4">New Issue</h4>\n',
                output_text,
            )
            self.assertIn("Issue Templates", output_text)
            self.assertIn(
                '<a class="issue-template dropdown-item pointer" data-value="RFE">RFE</a>',
                output_text,
            )
            self.assertIn(
                '<a class="issue-template dropdown-item pointer" data-value="2018-bid">2018-bid</a>',
                output_text,
            )
            self.assertIn(
                '<a class="issue-template dropdown-item pointer" data-value="default">default</a>',
                output_text,
            )
            self.assertIn(
                'placeholder="Enter your comment here" tabindex=2 required>'
                "Report your issue</textarea>",
                output_text,
            )

    def test_new_issue_w_specific_template(self):
        """ Test the new_issue endpoint when the project has templates. """

        user = tests.FakeUser()
        with tests.user_set(self.app.application, user):
            output = self.app.get("/test2/new_issue?template=2018-bid")
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<h4 class="font-weight-bold mb-4">New Issue</h4>\n',
                output_text,
            )
            self.assertIn("Issue Templates", output_text)
            self.assertIn(
                '<a class="issue-template dropdown-item pointer" data-value="RFE">RFE</a>',
                output_text,
            )
            self.assertIn(
                '<a class="issue-template dropdown-item pointer" data-value="2018-bid">2018-bid</a>',
                output_text,
            )
            self.assertIn(
                '<a class="issue-template dropdown-item pointer" data-value="default">default</a>',
                output_text,
            )
            self.assertIn(
                'placeholder="Enter your comment here" tabindex=2 required>'
                "Bid for 2018\n############",
                output_text,
            )

    def test_get_ticket_template_no_csrf(self):
        """Test the get_ticket_template endpoint when the project has no
        templates.
        """

        user = tests.FakeUser()
        with tests.user_set(self.app.application, user):
            output = self.app.post("/pv/test/issue/template")
            self.assertEqual(output.status_code, 400)
            data = json.loads(output.get_data(as_text=True))
            self.assertEqual(
                data, {"code": "ERROR", "message": "Invalid input submitted"}
            )

    def test_get_ticket_template_no_template_specified(self):
        """Test the get_ticket_template endpoint when not specifying which
        template to get.
        """

        user = tests.FakeUser()
        with tests.user_set(self.app.application, user):
            csrf = self.get_csrf()
            data = {"csrf_token": csrf}
            output = self.app.post("/pv/test/issue/template", data=data)
            self.assertEqual(output.status_code, 400)
            data = json.loads(output.get_data(as_text=True))
            self.assertEqual(
                data, {"code": "ERROR", "message": "No template provided"}
            )

    def test_get_ticket_template_no_project(self):
        """Test the get_ticket_template endpoint when the project does not
        exist.
        """

        user = tests.FakeUser()
        with tests.user_set(self.app.application, user):
            csrf = self.get_csrf()
            data = {"csrf_token": csrf}
            output = self.app.post("/pv/foobar/issue/template", data=data)
            self.assertEqual(output.status_code, 404)

    def test_get_ticket_template_no_template(self):
        """Test the get_ticket_template endpoint when the project has no
        templates.
        """

        user = tests.FakeUser()
        with tests.user_set(self.app.application, user):
            csrf = self.get_csrf()
            data = {"csrf_token": csrf}
            output = self.app.post(
                "/pv/test/issue/template?template=RFE", data=data
            )
            self.assertEqual(output.status_code, 404)
            data = json.loads(output.get_data(as_text=True))
            self.assertEqual(
                data, {"code": "ERROR", "message": "No such template found"}
            )

    def test_get_ticket_template_issue_tracker_disabled(self):
        """Test the get_ticket_template endpoint when the project has
        disabled its issue tracker.
        """
        repo = pagure.lib.query.get_authorized_project(self.session, "test")
        settings = repo.settings
        settings["issue_tracker"] = False
        repo.settings = settings
        self.session.add(repo)
        self.session.commit()

        user = tests.FakeUser()
        with tests.user_set(self.app.application, user):
            csrf = self.get_csrf()
            data = {"csrf_token": csrf}
            output = self.app.post(
                "/pv/test/issue/template?template=RFE", data=data
            )
            self.assertEqual(output.status_code, 404)
            data = json.loads(output.get_data(as_text=True))
            self.assertEqual(
                data,
                {
                    "code": "ERROR",
                    "message": "No issue tracker found for this project",
                },
            )

    def test_get_ticket_template_w_template(self):
        """Test the get_ticket_template endpoint when the project has
        templates.
        """

        user = tests.FakeUser()
        with tests.user_set(self.app.application, user):
            csrf = self.get_csrf()
            data = {"csrf_token": csrf}
            output = self.app.post(
                "/pv/test2/issue/template?template=RFE", data=data
            )
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.get_data(as_text=True))
            self.assertEqual(
                data,
                {"code": "OK", "message": "RFE\n###\n\n* Idea description"},
            )

    def test_get_ticket_template_w_template_namespace(self):
        """Test the get_ticket_template endpoint when the project has
        templates and a namespace.
        """

        user = tests.FakeUser()
        with tests.user_set(self.app.application, user):
            csrf = self.get_csrf()
            data = {"csrf_token": csrf}
            output = self.app.post(
                "/pv/somenamespace/test3/issue/template?template=RFE",
                data=data,
            )
            self.assertEqual(output.status_code, 200)
            data = json.loads(output.get_data(as_text=True))
            self.assertEqual(
                data,
                {"code": "OK", "message": "RFE\n###\n\n* Idea description"},
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
