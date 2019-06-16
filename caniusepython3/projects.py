from __future__ import print_function
from __future__ import unicode_literals

from caniusepython3 import pypi

import distlib.metadata
from distlib.locators import locate
import packaging.requirements
import packaging.utils

import io
import logging
import re

log = logging.getLogger('ciu')

def _requirement_to_dict(req):
    if not req.name:
        log.warning('A requirement lacks a name '
                    '(e.g. no `#egg` on a `file:` path)')
    elif req.url:
        log.warning(
            'Skipping {0}: URL-specified projects unsupported'.format(req.name))
    else:
        project = {
            'name': packaging.utils.canonicalize_name(req.name)
        }
        if len(req.specifier) > 0:
            project['version'] = packaging.utils.canonicalize_version(
                [s.version for s in req.specifier][0]
            )
        return project


def projects_from_list(projects_list):
    """Convert the list of projects to projects dict"""
    projects = []
    for p in projects_list:
        try:
            r = packaging.requirements.Requirement(p)
            pd = _requirement_to_dict(r)
            if pd:
                projects.append(pd)

        except packaging.requirements.InvalidRequirement:
            log.warning('Skipping {0!r}: could not parse requirement'.format(line))

    return projects

def projects_from_requirements(requirements):
    """Extract the project dependencies from a Requirements specification."""
    valid_reqs = []
    for requirements_path in requirements:
        with io.open(requirements_path) as file:
            requirements_text = file.read()
        # Drop line continuations.
        requirements_text = re.sub(r"\\s*", "", requirements_text)
        # Drop comments.
        requirements_text = re.sub(r"#.*", "", requirements_text)
        reqs = []
        for line in requirements_text.splitlines():
            if not line:
                continue
            try:
                reqs.append(packaging.requirements.Requirement(line))
            except packaging.requirements.InvalidRequirement:
                log.warning('Skipping {0!r}: could not parse requirement'.format(line))
        projects = []
        for req in reqs:
            pd = _requirement_to_dict(req)
            if pd:
                valid_reqs.append(pd)

    return valid_reqs


def projects_from_metadata(metadata):
    """Extract the project dependencies from a metadata spec."""
    projects = []
    for data in metadata:
        meta = distlib.metadata.Metadata(fileobj=io.StringIO(data))
        projects.append(
            {
                'name': packaging.utils.canonicalize_name(meta.name), 
                'version': packaging.utils.canonicalize_version(meta.version)
            })
        for dep in meta.run_requires:
            d = locate(dep)
            projects.append({
                'name': packaging.utils.canonicalize_name(d.name),
                'version': packaging.utils.canonicalize_version(d.version)
            })
    return projects
