from mindsdb_sql.ast.base import ASTNode
from mindsdb_sql.utils import indent


class Use(ASTNode):
    def __init__(self,
                 value,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value

    def to_tree(self, *args, level=0, **kwargs):
        ind = indent(level)
        ind1 = indent(level+1)
        value_str = f'value=\n{self.value.to_tree(level=level+2)},'

        out_str = f'{ind}Use(' \
                  f'{value_str}' \
                  f'\n{ind})'
        return out_str

    def to_string(self, *args, **kwargs):
        return f'USE {str(self.value)}'
