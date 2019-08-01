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
from __future__ import absolute_import

from collections import Mapping

from aiida.common import AttributeDict
from aiida.orm import Dict


def get_logging_container():
    """Return an `AttributeDict` that can be used to map logging messages to certain log levels.

    This datastructure is useful to add log messages in a function that does not have access to the right logger. Once
    returned, the caller who does have access to the logger can then easily loop over the contents and pipe the messages
    through the actual logger.

    :return: :py:class:`~aiida.common.extendeddicts.AttributeDict`
    """
    return AttributeDict({
        'warning': [],
        'error': [],
    })


def update_mapping(original, source):
    """Update a nested dictionary with another optionally nested dictionary.

    The dictionaries may be plain Mapping objects or `Dict` nodes. If the original dictionary is an instance of `Dict`
    the returned dictionary will also be wrapped in `Dict`.

    :param original: Mapping object or `Dict` instance
    :param source: Mapping object or `Dict` instance
    :return: the original dictionary updated with the source dictionary
    """
    return_node = False

    if isinstance(original, Dict):
        return_node = True
        original = original.get_dict()

    if isinstance(source, Dict):
        source = source.get_dict()

    for key, value in source.items():
        if key not in original:
            original[key] = value
            continue
        mappable_value = (isinstance(value, Mapping) or isinstance(value, Dict))
        mappable_original = (isinstance(original[key], Mapping) or isinstance(original[key], Dict))
        if mappable_value and mappable_original:
            original[key] = update_mapping(original[key], value)
        else:
            original[key] = value

    if return_node:
        original = Dict(dict=original)

    return original


def prepare_process_inputs(process, inputs):
    """Prepare the inputs for submission for the given process, according to its spec.

    That is to say that when an input is found in the inputs that corresponds to an input port in the spec of the
    process that expects a `Dict`, yet the value in the inputs is a plain dictionary, the value will be wrapped in by
    the `Dict` class to create a valid input.

    :param process: sub class of `Process` for which to prepare the inputs dictionary
    :param inputs: a dictionary of inputs intended for submission of the process
    :return: a dictionary with all bare dictionaries wrapped in `Dict` if dictated by the process spec
    """
    prepared_inputs = wrap_bare_dict_inputs(process.spec().inputs, inputs)
    return AttributeDict(prepared_inputs)


def wrap_bare_dict_inputs(port_namespace, inputs):
    """Wrap bare dictionaries in `inputs` in a `Dict` node if dictated by the corresponding port in given namespace.

    :param port_namespace: a `PortNamespace`
    :param inputs: a dictionary of inputs intended for submission of the process
    :return: a dictionary with all bare dictionaries wrapped in `Dict` if dictated by the port namespace
    """
    from aiida.engine.processes import PortNamespace

    wrapped = {}

    for key, value in inputs.items():

        if key not in port_namespace:
            wrapped[key] = value
            continue

        port = port_namespace[key]

        if isinstance(port, PortNamespace):
            wrapped[key] = wrap_bare_dict_inputs(port, value)
        elif port.valid_type == Dict and isinstance(value, dict):
            wrapped[key] = Dict(dict=value)
        else:
            wrapped[key] = value

    return wrapped
