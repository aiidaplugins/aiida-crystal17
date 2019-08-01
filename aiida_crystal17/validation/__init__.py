#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Chris Sewell
#
# This file is part of aiida-crystal17.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms and conditions
# of version 3 of the GNU Lesser General Public License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
import json
import os

import jsonschema
import six

SCHEMAPATH = os.path.dirname(os.path.realpath(__file__))


def load_schema(path):
    """read and return a json schema

    if the path is absolute, it will be used as is, otherwise
    it will be joined with the path to the internal json schema folder

    Parameters
    ----------
    path: str

    Returns
    -------
    dict

    """
    if os.path.isabs(path):
        jpath = path
    else:
        jpath = os.path.join(SCHEMAPATH, path)

    with open(jpath) as jfile:
        schema = json.load(jfile)
    return schema


def load_validator(schema):
    """create a validator for a schema

    Parameters
    ----------
    schema : str or dict
        schema or path to schema

    Returns
    -------
    jsonschema.IValidator
        the validator to use

    """
    if isinstance(schema, six.string_types):
        schema = load_schema(schema)

    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)

    # by default, only validates lists
    def is_array(checker, instance):
        return isinstance(instance, (tuple, list))

    type_checker = validator_cls.TYPE_CHECKER.redefine('array', is_array)
    validator_cls = jsonschema.validators.extend(validator_cls, type_checker=type_checker)

    validator = validator_cls(schema=schema)
    return validator


def validate_against_schema(data, schema):
    """ validate json-type data against a schema

    Parameters
    ----------
    data: dict
    schema: dict or str
        schema or path to schema

    Raises
    ------
    jsonschema.exceptions.SchemaError
        if the schema is invalid
    jsonschema.exceptions.ValidationError
        if the instance is invalid

    Returns
    -------
    bool
        return True if validated


    """
    validator = load_validator(schema)
    # validator.validate(data)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        raise jsonschema.ValidationError('\n'.join([
            "- {} [key path: '{}']".format(error.message, '/'.join([str(p) for p in error.path])) for error in errors
        ]))

    return True
