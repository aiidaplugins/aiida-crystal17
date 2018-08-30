"""
parsers for CRYSTAL17
"""
import os
import json
import jsonschema


def read_inputschema():
    """read and return the CRYSTAL17 input json schema

    :return:
    """
    dirpath = os.path.dirname(os.path.realpath(__file__))
    jpath = os.path.join(dirpath, "inputschema.json")
    with open(jpath) as jfile:
        schema = json.load(jfile)
    return schema


def validate_cryinput(data):
    """ validate json-type data against a schema

    :param data: dictionary
    """
    schema = read_inputschema()

    # validator = jsonschema.validators.extend(
    #     jsonschema.Draft4Validator,
    # )
    validator = jsonschema.Draft4Validator

    validator(schema).validate(data)

    # by default, only validates lists
    # validator(schema, types={"array": (list, tuple)}).validate(data)
