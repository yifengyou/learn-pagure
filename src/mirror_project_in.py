#!/usr/bin/env python

from __future__ import print_function, absolute_import
import os
import argparse
from datetime import datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError

import pagure.config
import pagure.lib.model as model
import pagure.lib.model_base
import pagure.lib.notify
import pagure.lib.query

if "PAGURE_CONFIG" not in os.environ and os.path.exists(
    "/etc/pagure/pagure.cfg"
):
    print("Using configuration file `/etc/pagure/pagure.cfg`")
    os.environ["PAGURE_CONFIG"] = "/etc/pagure/pagure.cfg"

_config = pagure.config.reload_config()


def main(check=False, debug=False):
    """ The function pulls in all the changes from upstream"""

    session = pagure.lib.model_base.create_session(_config["DB_URL"])
    projects = (
        session.query(model.Project)
        .filter(model.Project.mirrored_from != None)
        .all()
    )

    for project in projects:
        if debug:
            print("Mirrorring %s" % project.fullname)
            print("Mirrorring mirrored_from = [%s]" % project.mirrored_from)
            print("Mirrorring mirrored_from_last_log = [%s]" % project.mirrored_from_last_log)
        try:
            pagure.lib.git.mirror_pull_project(session, project, debug=debug)
        except Exception as err:
            print("ERROR: %s" % err)

    session.remove()
    if debug:
        print("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to send email before the api token expires"
    )
    parser.add_argument(
        "--config",
        "-c",
        dest="config",
        help="Configuration file to use for pagure.",
    )
    parser.add_argument(
        "--check",
        dest="check",
        action="store_true",
        default=False,
        help="Print the some output but does not send any email",
    )
    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        help="Print the debugging output",
    )
    args = parser.parse_args()
    print("type(_config) : [%s]" % type(_config))
    print("_config : [%s]" % str(_config))
    main(debug=args.debug)
