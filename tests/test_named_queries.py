"""Tests for named queries."""

import pytest
import tempfile

from pgspecial.namedqueries import NamedQueries
from pgspecial.main import PGSpecial
from configobj import ConfigObj


@pytest.fixture(scope="module")
def named_query():
    with tempfile.NamedTemporaryFile() as f:
        NamedQueries.instance = NamedQueries.from_config(ConfigObj(f))
        yield
        NamedQueries.instance = None


def test_save_named_queries(named_query):
    PGSpecial().execute(None, "\\ns test select * from foo")
    expected = {"test": "select * from foo"}
    assert NamedQueries.instance.list() == expected


def test_delete_named_queries(named_query):
    PGSpecial().execute(None, "\\ns test_foo select * from foo")
    assert "test_foo" in NamedQueries.instance.list()

    PGSpecial().execute(None, "\\nd test_foo")
    assert "test_foo" not in NamedQueries.instance.list()


def test_print_named_queries(named_query):
    PGSpecial().execute(None, "\\ns test_name select * from bar")
    assert "test_name" in NamedQueries.instance.list()

    result = PGSpecial().execute(None, "\\np test_n.*")
    assert result == [("", [("test_name", "select * from bar")], ["Name", "Query"], "")]

    result = PGSpecial().execute(None, "\\np")
    assert result[0][:3] == (
        None,
        None,
        None,
    )


def test_list_named_queries_truncates_long_queries(named_query):
    """Test that \n command truncates queries longer than 80 characters."""
    # Create a query longer than 80 characters
    long_query = "select " + ", ".join([f"column_{i}" for i in range(20)]) + " from table_name"
    assert len(long_query) > 80, "Test query should be longer than 80 characters"

    PGSpecial().execute(None, f"\\ns long_test {long_query}")
    assert "long_test" in NamedQueries.instance.list()

    # Execute \n to list all named queries
    result = PGSpecial().execute(None, "\\n")

    # Find the long_test query in results
    rows = result[0][1]
    long_test_row = [row for row in rows if row[0] == "long_test"][0]

    # Verify the query is truncated to 80 characters
    assert len(long_test_row[1]) == 80, f"Query should be truncated to 80 chars, got {len(long_test_row[1])}"
    assert long_test_row[1].endswith("..."), "Truncated query should end with '...'"

    # Verify the truncated query is the first 77 chars + "..."
    assert long_test_row[1] == long_query[:77] + "..."
