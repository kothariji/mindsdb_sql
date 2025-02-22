from mindsdb_sql import parse_sql
from mindsdb_sql.parser.ast import Select, Identifier, BinaryOperation, Star
from mindsdb_sql.parser.dialects.mysql import Variable


class TestMySQLParser:
    def test_select_variable(self):
        sql = 'SELECT @version'
        ast = parse_sql(sql, dialect='mysql')
        expected_ast = Select(targets=[Variable('version')])
        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast).lower() == sql.lower()
        assert str(ast) == str(expected_ast)

        sql = 'SELECT @@version'
        ast = parse_sql(sql, dialect='mysql')
        expected_ast = Select(targets=[Variable('version', is_system_var=True)])
        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast).lower() == sql.lower()
        assert str(ast) == str(expected_ast)

    def test_select_varialbe_complex(self):
        sql = f"""SELECT * FROM tab1 WHERE column1 in (SELECT column2 + @variable FROM t2)"""
        ast = parse_sql(sql, dialect='mysql')
        expected_ast = Select(targets=[Star()],
                              from_table=Identifier('tab1'),
                              where=BinaryOperation(op='in',
                                                    args=(
                                                        Identifier('column1'),
                                                        Select(targets=[BinaryOperation(op='+',
                                                                                        args=[Identifier('column2'),
                                                                                              Variable('variable')])
                                                                        ],
                                                               from_table=Identifier('t2'),
                                                               parentheses=True)
                                                    )
                                                    ))

        assert ast.to_tree() == expected_ast.to_tree()
        assert str(ast).lower() == sql.lower()
        assert str(ast) == str(expected_ast)
