import json
import os

import jsonschema


def read_schema(name="inputd12"):
    """read and return an json schema

    :return:
    """
    dirpath = os.path.dirname(os.path.realpath(__file__))
    jpath = os.path.join(dirpath, "{}.schema.json".format(name))
    with open(jpath) as jfile:
        schema = json.load(jfile)
    return schema


def validate_with_json(data, name="inputd12"):
    """ validate json-type data against a schema

    :param data: dictionary
    """
    schema = read_schema(name)

    # validator = jsonschema.validators.extend(
    #     jsonschema.Draft4Validator,
    # )
    validator = jsonschema.Draft4Validator

    # by default, only validates lists
    validator(schema, types={"array": (list, tuple)}).validate(data)


def validate_with_dict(data, schema):
    """ validate json-type data against a schema

    :param data: dictionary
    :param schema: dictionary
    """
    # validator = jsonschema.validators.extend(
    #     jsonschema.Draft4Validator,
    # )
    validator = jsonschema.Draft4Validator

    # by default, only validates lists
    validator(schema, types={"array": (list, tuple)}).validate(data)