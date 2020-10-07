"""
Python Tests for the Shasta Compute Rolling Upgrade Service (CRUS)

Copyright 2019, Cray Inc. All rights reserved.
"""
from tempfile import NamedTemporaryFile
from crus.gen_swagger import main


def test_gen_swagger_output():
    """Verify that generating the swagger.yaml file from the code produces
    the same thing every time if the code has not changed.

    """
    with NamedTemporaryFile(mode='w+') as outfile:
        # Write the swagger out to a file and collect the result
        main(["gen_swagger", outfile.name])
        lines = outfile.readlines()
        # Write the swagger out to the same file (this should cause it
        # to collate the data the same way)
        main(["gen_swagger", outfile.name])
        outfile.seek(0)
        second_lines = outfile.readlines()
        assert lines == second_lines


def test_gen_swagger_errors():
    """Verify that too few or too many arguments or an unavailable file
    break gen_swagger as expected.

    """
    assert main(["gen_swagger", "foo", "bar"]) == 1
    assert main(["gen_swagger"]) == 1
    assert main(["gen_swagger", "/nodir/not/there/file"]) == 1
