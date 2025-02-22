import itertools
import pytest
from mindsdb_sql import parse_sql, get_lexer_parser
from mindsdb_sql.parser.ast import *
from mindsdb_sql.exceptions import ParsingException
from mindsdb_sql.utils import JoinType


@pytest.mark.parametrize('dialect', ['sqlite', 'mysql', 'mindsdb'])
class TestMiscQueries:
    def test_set(self, dialect):
        lexer, parser = get_lexer_parser(dialect)

        sql = "set autocommit"

        tokens = list(lexer.tokenize(sql))

        assert len(tokens) == 2
        assert tokens[0].type == 'SET'
        assert tokens[1].type == 'AUTOCOMMIT'

        ast = parse_sql(sql, dialect=dialect)
        expected_ast = Set(category="autocommit")
        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast) == str(expected_ast)

        sql = "SET NAMES some_name"

        ast = parse_sql(sql, dialect=dialect)
        expected_ast = Set(category="names", arg=Identifier('some_name'))
        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast) == str(expected_ast)

        sql = "set character_set_results = NULL"

        ast = parse_sql(sql, dialect=dialect)
        expected_ast = Set(arg=BinaryOperation('=', args=[Identifier('character_set_results'), NullConstant()]))
        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast) == str(expected_ast)

    def test_start_transaction(self, dialect):
        sql = "start transaction"

        ast = parse_sql(sql, dialect=dialect)
        expected_ast = StartTransaction()
        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast) == str(expected_ast)

    def test_rollback(self, dialect):
        sql = "rollback"

        ast = parse_sql(sql, dialect=dialect)
        expected_ast = RollbackTransaction()
        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast) == str(expected_ast)

    def test_commit(self, dialect):
        sql = "commit"

        ast = parse_sql(sql, dialect=dialect)
        expected_ast = CommitTransaction()
        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast) == str(expected_ast)

    def test_explain(self, dialect):
        sql = "explain some_table"

        ast = parse_sql(sql, dialect=dialect)
        expected_ast = Explain(target=Identifier('some_table'))
        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast) == str(expected_ast)

    def test_alter_table_keys(self, dialect):
        sql = "alter table some_table disable keys"

        ast = parse_sql(sql, dialect=dialect)
        expected_ast = AlterTable(target=Identifier('some_table'), arg='disable keys')
        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast) == str(expected_ast)

        sql = "alter table some_table enable keys"

        ast = parse_sql(sql, dialect=dialect)
        expected_ast = AlterTable(target=Identifier('some_table'), arg='enable keys')
        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast) == str(expected_ast)


