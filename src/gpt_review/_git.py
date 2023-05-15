"""Basic Shell Commands for Git."""
import logging
import os
from typing import Dict

from git.repo import Repo
from knack import CLICommandsLoader
from knack.arguments import ArgumentsContext
from knack.commands import CommandGroup

from gpt_review._command import GPTCommandGroup
from gpt_review._review import _request_goal


def _find_git_dir(path=".") -> str:
    """
    Find the .git directory.

    Args:
        path (str): The path to start searching from.

    Returns:
        path (str): The path to the .git directory.
    """
    while path != "/":
        if os.path.exists(os.path.join(path, ".git")):
            return path
        path = os.path.abspath(os.path.join(path, os.pardir))
    raise FileNotFoundError(".git directory not found")


def _diff() -> str:
    """
    Get the diff of the PR
    - run git commands via python

    Returns:
        diff (str): The diff of the PR.
    """
    return Repo.init(_find_git_dir()).git.diff(None, cached=True)


def _commit_message(gpt4: bool = False, large: bool = False) -> str:
    """
    Create a commit message with GPT.

    Args:
        gpt4 (bool, optional): Whether to use gpt-4. Defaults to False.
        large (bool, optional): Whether to use gpt-4-32k. Defaults to False.

    Returns:
        response (str): The response from GPT-4.
    """

    goal = """
Create a short, single-line, git commit message for these changes
"""
    diff = _diff()
    logging.debug("Diff: %s", diff)

    return _request_goal(diff, goal, fast=not gpt4, large=large)


def _push() -> str:
    """Run git push."""
    logging.debug("Pushing commit to remote.")
    repo = Repo.init(_find_git_dir())
    return repo.git.push()


def _commit(gpt4: bool = False, large: bool = False, push: bool = False) -> Dict[str, str]:
    """Run git commit with a commit message generated by GPT.

    Args:
        gpt4 (bool, optional): Whether to use gpt-4. Defaults to False.
        large (bool, optional): Whether to use gpt-4-32k. Defaults to False.
        push (bool, optional): Whether to push the commit to the remote. Defaults to False.

    Returns:
        response (Dict[str, str]): The response from git commit.
    """
    message = _commit_message(gpt4=gpt4, large=large)
    logging.debug("Commit Message: %s", message)
    repo = Repo.init(_find_git_dir())
    commit = repo.git.commit(message=message)
    if push:
        commit += f"\n{_push()}"
    return {"response": commit}


class GitCommandGroup(GPTCommandGroup):
    """Ask Command Group."""

    @staticmethod
    def load_command_table(loader: CLICommandsLoader) -> None:
        with CommandGroup(loader, "git", "gpt_review._git#{}", is_preview=True) as group:
            group.command("commit", "_commit", is_preview=True)

    @staticmethod
    def load_arguments(loader: CLICommandsLoader) -> None:
        with ArgumentsContext(loader, "git commit") as args:
            args.argument(
                "gpt4",
                help="Use gpt-4 for generating commit messages instead of gpt-35-turbo.",
                default=False,
                action="store_true",
            )
            args.argument(
                "large",
                help="Use gpt-4-32k model for generating commit messages.",
                default=False,
                action="store_true",
            )
            args.argument(
                "push",
                help="Push the commit to the remote.",
                default=False,
                action="store_true",
            )
