#!/usr/bin/env -S python -u

import argparse
import os
import subprocess as sp


ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def setup_parser():
    """ Setup the cli arguments """
    parser = argparse.ArgumentParser(prog="pagure-test")
    parser.add_argument(
        "test_case", nargs="?", default="", help="Run the given test case"
    )
    parser.add_argument(
        "--fedora",
        action="store_true",
        help="Run the tests in fedora environment (DEFAULT)",
    )
    parser.add_argument(
        "--centos",
        action="store_true",
        help="Run the tests in centos environment",
    )
    parser.add_argument(
        "--pip",
        action="store_true",
        help="Run the tests in a venv on a Fedora host",
    )
    parser.add_argument(
        "--skip-build",
        dest="skip_build",
        action="store_false",
        help="Skip building the container image",
    )
    parser.add_argument(
        "--shell",
        dest="shell",
        action="store_true",
        help="Gives you a shell into the container instead "
        "of running the tests",
    )

    parser.add_argument(
        "--repo",
        dest="repo",
        default="https://pagure.io/pagure.git",
        help="URL of the public repo to use as source, can be overridden using "
        "the REPO environment variable",
    )
    parser.add_argument(
        "--branch",
        dest="branch",
        default="master",
        help="Branch of the repo to use as source, can be overridden using "
        "the BRANCH environment variable",
    )

    return parser


if __name__ == "__main__":
    parser = setup_parser()
    args = parser.parse_args()

    if args.centos is True:
        container_names = ["pagure-c7-rpms-py2"]
        container_files = ["centos7-rpms-py2"]
    elif args.fedora is True:
        container_names = ["pagure-fedora-rpms-py3"]
        container_files = ["fedora-rpms-py3"]
    elif args.pip is True:
        container_names = ["pagure-fedora-pip-py3"]
        container_files = ["fedora-pip-py3"]
    else:
        container_names = [
            "pagure-fedora-rpms-py3",
            "pagure-c7-rpms-py2",
            "pagure-fedora-pip-py3",
        ]
        container_files = [
            "fedora-rpms-py3",
            "centos7-rpms-py2",
            "fedora-pip-py3",
        ]

    failed = []
    print("Running for {} containers:".format(len(container_names)))
    print("  - " + "\n  - ".join(container_names))
    for idx, container_name in enumerate(container_names):
        if args.skip_build is not False:
            print("------ Building Container Image -----")
            cmd = [
                "podman",
                "build",
                "--build-arg",
                "branch={}".format(os.environ.get("BRANCH") or args.branch),
                "--build-arg",
                "repo={}".format(os.environ.get("REPO") or args.repo),
                "--rm",
                "-t",
                container_name,
                "-f",
                ROOT + "/dev/containers/%s" % container_files[idx],
                ROOT + "/dev/containers",
            ]
            print(" ".join(cmd))
            output_code = sp.call(cmd)
            if output_code:
                print("Failed building: %s", container_name)
                break

        result_path = "{}/results_{}".format(os.getcwd(), container_files[idx])
        if not os.path.exists(result_path):
            os.mkdir(result_path)

        if args.shell:
            print("--------- Shelling in the container --------------")
            command = [
                "podman",
                "run",
                "-it",
                "--rm",
                "--name",
                container_name,
                "-v",
                "{}/results_{}:/pagure/results:z".format(
                    os.getcwd(), container_files[idx]
                ),
                "-e",
                "BRANCH={}".format(os.environ.get("BRANCH") or args.branch),
                "-e",
                "REPO={}".format(os.environ.get("REPO") or args.repo),
                "--entrypoint=/bin/bash",
                container_name,
            ]
            sp.call(command)
        else:
            print("--------- Running Test --------------")
            command = [
                "podman",
                "run",
                "-it",
                "--rm",
                "--name",
                container_name,
                "-v",
                "{}/results_{}:/pagure/results:z".format(
                    os.getcwd(), container_files[idx]
                ),
                "-e",
                "BRANCH={}".format(os.environ.get("BRANCH") or args.branch),
                "-e",
                "REPO={}".format(os.environ.get("REPO") or args.repo),
                "-e",
                "TESTCASE={}".format(args.test_case or ""),
                container_name,
            ]
            output_code = sp.call(command)
            if output_code:
                failed.append(container_name)

    if not args.shell:
        print("\nSummary:")
        if not failed:
            print("  ALL TESTS PASSED")
        else:
            print("  %s TESTS FAILED:" % len(failed))
            for fail in failed:
                print("    - %s" % fail)
