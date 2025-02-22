import pytest

from mindsdb_sql import parse_sql
from mindsdb_sql.exceptions import PlanningException
from mindsdb_sql.parser.ast import *
from mindsdb_sql.planner import plan_query, QueryPlan
from mindsdb_sql.planner.step_result import Result
from mindsdb_sql.planner.steps import (FetchDataframeStep, ProjectStep, FilterStep, JoinStep, ApplyPredictorStep,
                                       ApplyPredictorRowStep, GroupByStep, UnionStep)
from mindsdb_sql.utils import JoinType


class TestPlanJoinPredictor:
    def test_join_predictor_plan(self):
        query = Select(targets=[Identifier('tab1.column1'), Identifier('pred.predicted')],
                       from_table=Join(left=Identifier('int.tab1'),
                                       right=Identifier('mindsdb.pred'),
                                       join_type=JoinType.INNER_JOIN,
                                       implicit=True)
                       )
        expected_plan = QueryPlan(
            steps=[
                FetchDataframeStep(integration='int',
                                   query=Select(targets=[Star()],
                                                from_table=Identifier('tab1')),
                                   ),
                ApplyPredictorStep(namespace='mindsdb', dataframe=Result(0), predictor=Identifier('pred')),
                JoinStep(left=Result(0), right=Result(1),
                         query=Join(left=Identifier('result_0', alias=Identifier('tab1')),
                                    right=Identifier('result_1', alias=Identifier('pred')),
                                    join_type=JoinType.INNER_JOIN)),
                ProjectStep(dataframe=Result(2), columns=[Identifier('tab1.column1'), Identifier('pred.predicted')]),
            ],
        )
        plan = plan_query(query, integrations=['int'], predictor_namespace='mindsdb')

        for i in range(len(plan.steps)):
            assert plan.steps[i] == expected_plan.steps[i]
        

    def test_predictor_namespace_is_case_insensitive(self):
        query = Select(targets=[Identifier('tab1.column1'), Identifier('pred.predicted')],
                       from_table=Join(left=Identifier('int.tab1'),
                                       right=Identifier('mindsdb.pred'),
                                       join_type=JoinType.INNER_JOIN,
                                       implicit=True)
                       )
        expected_plan = QueryPlan(
            steps=[
                FetchDataframeStep(integration='int',
                                   query=Select(targets=[Star()],
                                                from_table=Identifier('tab1')),
                                   ),
                ApplyPredictorStep(namespace='mindsdb', dataframe=Result(0), predictor=Identifier('pred')),
                JoinStep(left=Result(0), right=Result(1),
                         query=Join(left=Identifier('result_0', alias=Identifier('tab1')),
                                    right=Identifier('result_1', alias=Identifier('pred')),
                                    join_type=JoinType.INNER_JOIN)),
                ProjectStep(dataframe=Result(2), columns=[Identifier('tab1.column1'), Identifier('pred.predicted')]),
            ],
        )
        plan = plan_query(query, integrations=['int'], predictor_namespace='MINDSDB')

        assert plan.steps == expected_plan.steps
        

    def test_join_predictor_plan_aliases(self):
        query = Select(targets=[Identifier('ta.column1'), Identifier('tb.predicted')],
                       from_table=Join(left=Identifier('int.tab1', alias=Identifier('ta')),
                                       right=Identifier('mindsdb.pred', alias=Identifier('tb')),
                                       join_type=JoinType.INNER_JOIN,
                                       implicit=True)
                       )
        expected_plan = QueryPlan(
            steps=[
                FetchDataframeStep(integration='int',
                                   query=Select(targets=[Star()],
                                                from_table=Identifier('tab1', alias=Identifier('ta'))),
                                   ),
                ApplyPredictorStep(namespace='mindsdb', dataframe=Result(0), predictor=Identifier('pred', alias=Identifier('tb'))),
                JoinStep(left=Result(0), right=Result(1),
                         query=Join(left=Identifier('result_0', alias=Identifier('ta')),
                                    right=Identifier('result_1', alias=Identifier('tb')),
                                    join_type=JoinType.INNER_JOIN)),
                ProjectStep(dataframe=Result(2), columns=[Identifier('ta.column1'), Identifier('tb.predicted')]),
            ],
        )
        plan = plan_query(query, integrations=['int'], predictor_namespace='mindsdb')

        assert plan.steps == expected_plan.steps
        

    def test_join_predictor_plan_where(self):
        query = Select(targets=[Identifier('tab.column1'), Identifier('pred.predicted')],
                       from_table=Join(left=Identifier('int.tab'),
                                       right=Identifier('mindsdb.pred'),
                                       join_type=JoinType.INNER_JOIN,
                                       implicit=True),
                       where=BinaryOperation('and', args=[
                           BinaryOperation('=', args=[Identifier('tab.product_id'), Constant('x')]),
                           BetweenOperation(args=[Identifier('tab.time'), Constant('2021-01-01'), Constant('2021-01-31')]),
                       ])
                       )

        expected_plan = QueryPlan(
            steps=[
                FetchDataframeStep(integration='int',
                                   query=Select(targets=[Star()],
                                                from_table=Identifier('tab'),
                                                where=BinaryOperation('and', args=[
                                                    BinaryOperation('=',
                                                                    args=[Identifier('tab.product_id'), Constant('x')]),
                                                    BetweenOperation(
                                                        args=[Identifier('tab.time'),
                                                              Constant('2021-01-01'),
                                                              Constant('2021-01-31')]),
                                                ])
                                                ),
                                   ),
                ApplyPredictorStep(namespace='mindsdb', dataframe=Result(0), predictor=Identifier('pred')),
                JoinStep(left=Result(0), right=Result(1),
                         query=Join(left=Identifier('result_0', alias=Identifier('tab')),
                                    right=Identifier('result_1', alias=Identifier('pred')),
                                    join_type=JoinType.INNER_JOIN)),
                ProjectStep(dataframe=Result(2), columns=[Identifier('tab.column1'), Identifier('pred.predicted')]),
            ],
        )
        plan = plan_query(query, integrations=['int'], predictor_namespace='mindsdb')

        assert plan.steps == expected_plan.steps
        

    def test_join_predictor_error_when_filtering_on_predictions(self):
        """
        Query:
        SELECT rental_price_confidence
        FROM postgres_90.test_data.home_rentals AS ta
        JOIN mindsdb.hrp3 AS tb
        WHERE ta.sqft > 1000 AND tb.rental_price_confidence > 0.5
        LIMIT 5;
        """

        query = Select(targets=[Identifier('rental_price_confidence')],
                       from_table=Join(left=Identifier('postgres_90.test_data.home_rentals', alias=Identifier('ta')),
                                       right=Identifier('mindsdb.hrp3', alias=Identifier('tb')),
                                       join_type=JoinType.INNER_JOIN,
                                       implicit=True),
                       where=BinaryOperation('and', args=[
                           BinaryOperation('>', args=[Identifier('ta.sqft'), Constant(1000)]),
                           BinaryOperation('>', args=[Identifier('tb.rental_price_confidence'), Constant(0.5)]),
                       ]),
                       limit=5
                       )

        with pytest.raises(PlanningException):
            plan_query(query, integrations=['postgres_90'], predictor_namespace='mindsdb')

    def test_join_predictor_plan_group_by(self):
        query = Select(targets=[Identifier('tab.asset'), Identifier('tab.time'), Identifier('pred.predicted')],
                       from_table=Join(left=Identifier('int.tab'),
                                       right=Identifier('mindsdb.pred'),
                                       join_type=JoinType.INNER_JOIN,
                                       implicit=True),
                       group_by=[Identifier('tab.asset')],
                       having=BinaryOperation('=', args=[Identifier('tab.asset'), Constant('bitcoin')])
                       )

        expected_plan = QueryPlan(
            steps=[
                FetchDataframeStep(integration='int',
                                   query=Select(targets=[Star()],
                                                from_table=Identifier('tab'),
                                                group_by=[Identifier('tab.asset')],
                                                having=BinaryOperation('=', args=[Identifier('tab.asset'),
                                                                                  Constant('bitcoin')])
                                                ),
                                   ),
                ApplyPredictorStep(namespace='mindsdb', dataframe=Result(0), predictor=Identifier('pred')),
                JoinStep(left=Result(0), right=Result(1),
                         query=Join(left=Identifier('result_0', alias=Identifier('tab')),
                                    right=Identifier('result_1', alias=Identifier('pred')),
                                    join_type=JoinType.INNER_JOIN)),
                ProjectStep(dataframe=Result(2), columns=[Identifier('tab.asset'), Identifier('tab.time'), Identifier('pred.predicted')]),
            ],
        )
        plan = plan_query(query, integrations=['int'], predictor_namespace='mindsdb')

        assert plan.steps == expected_plan.steps
        

    def test_join_predictor_plan_limit_offset(self):
        query = Select(targets=[Identifier('tab.column1'), Identifier('pred.predicted')],
                       from_table=Join(left=Identifier('int.tab'),
                                       right=Identifier('mindsdb.pred'),
                                       join_type=JoinType.INNER_JOIN,
                                       implicit=True),
                       where=BinaryOperation('=', args=[Identifier('tab.product_id'), Constant('x')]),
                       limit=Constant(10),
                       offset=Constant(15),
                       )

        expected_plan = QueryPlan(
            steps=[
                FetchDataframeStep(integration='int',
                                   query=Select(targets=[Star()],
                                                from_table=Identifier('tab'),
                                                where=BinaryOperation('=', args=[Identifier('tab.product_id'), Constant('x')]),
                                                limit=Constant(10),
                                                offset=Constant(15),
                                                ),
                                   ),
                ApplyPredictorStep(namespace='mindsdb', dataframe=Result(0), predictor=Identifier('pred')),
                JoinStep(left=Result(0), right=Result(1),
                         query=Join(left=Identifier('result_0', alias=Identifier('tab')),
                                    right=Identifier('result_1', alias=Identifier('pred')),
                                    join_type=JoinType.INNER_JOIN)),
                ProjectStep(dataframe=Result(2), columns=[Identifier('tab.column1'), Identifier('pred.predicted')]),
            ],
        )
        plan = plan_query(query, integrations=['int'], predictor_namespace='mindsdb')

        assert plan.steps == expected_plan.steps
        

    def test_join_predictor_plan_order_by(self):
        query = Select(targets=[Identifier('tab.column1'), Identifier('pred.predicted')],
                       from_table=Join(left=Identifier('int.tab'),
                                       right=Identifier('mindsdb.pred'),
                                       join_type=JoinType.INNER_JOIN,
                                       implicit=True),
                       where=BinaryOperation('=', args=[Identifier('tab.product_id'), Constant('x')]),
                       limit=Constant(10),
                       offset=Constant(15),
                       order_by=[OrderBy(field=Identifier('tab.column1'))]
                       )

        expected_plan = QueryPlan(
            steps=[
                FetchDataframeStep(integration='int',
                                   query=Select(targets=[Star()],
                                                from_table=Identifier('tab'),
                                                where=BinaryOperation('=', args=[Identifier('tab.product_id'), Constant('x')]),
                                                limit=Constant(10),
                                                offset=Constant(15),
                                                order_by=[OrderBy(field=Identifier('tab.column1'))],
                                                ),
                                   ),
                ApplyPredictorStep(namespace='mindsdb', dataframe=Result(0), predictor=Identifier('pred')),
                JoinStep(left=Result(0), right=Result(1),
                         query=Join(left=Identifier('result_0', alias=Identifier('tab')),
                                    right=Identifier('result_1', alias=Identifier('pred')),
                                    join_type=JoinType.INNER_JOIN)),
                ProjectStep(dataframe=Result(2), columns=[Identifier('tab.column1'), Identifier('pred.predicted')]),
            ],
        )
        plan = plan_query(query, integrations=['int'], predictor_namespace='mindsdb')

        assert plan.steps == expected_plan.steps
        

    def test_join_predictor_plan_predictor_alias(self):
        query = Select(targets=[Identifier('tab1.column1'), Identifier('pred_alias.predicted')],
                       from_table=Join(left=Identifier('int.tab1'),
                                       right=Identifier('mindsdb.pred', alias=Identifier('pred_alias')),
                                       join_type=JoinType.INNER_JOIN,
                                       implicit=True)
                       )
        expected_plan = QueryPlan(
            steps=[
                FetchDataframeStep(integration='int',
                                   query=Select(targets=[Star()],
                                                from_table=Identifier('tab1')),
                                   ),
                ApplyPredictorStep(namespace='mindsdb', predictor=Identifier('pred', alias=Identifier('pred_alias')), dataframe=Result(0)),
                JoinStep(left=Result(0), right=Result(1),
                         query=Join(left=Identifier('result_0', alias=Identifier('tab1')),
                                    right=Identifier('result_1', alias=Identifier('pred_alias')),
                                    join_type=JoinType.INNER_JOIN)),
                ProjectStep(dataframe=Result(2), columns=[Identifier('tab1.column1'), Identifier('pred_alias.predicted')]),
            ],
        )
        plan = plan_query(query, integrations=['int'], predictor_namespace='mindsdb')

        assert plan.steps == expected_plan.steps
        

    def test_no_predictor_error(self):
        query = Select(targets=[Identifier('tab1.column1'), Identifier('pred.predicted')],
                       from_table=Join(left=Identifier('int.tab1'),
                                       right=Identifier('pred'),
                                       join_type=None,
                                       implicit=True)
                       )

        with pytest.raises(PlanningException):
            plan = plan_query(query, integrations=['int'])

    def test_join_predictor_plan_default_namespace_integration(self):
        query = Select(targets=[Identifier('tab1.column1'), Identifier('pred.predicted')],
                       from_table=Join(left=Identifier('tab1'),
                                       right=Identifier('mindsdb.pred'),
                                       join_type=JoinType.INNER_JOIN,
                                       implicit=True)
                       )
        expected_plan = QueryPlan(
            default_namespace='int',
            steps=[
                FetchDataframeStep(integration='int',
                                   query=Select(targets=[Star()],
                                                from_table=Identifier('tab1')),
                                   ),
                ApplyPredictorStep(namespace='mindsdb', dataframe=Result(0), predictor=Identifier('pred')),
                JoinStep(left=Result(0), right=Result(1),
                         query=Join(left=Identifier('result_0', alias=Identifier('tab1')),
                                    right=Identifier('result_1', alias=Identifier('pred')),
                                    join_type=JoinType.INNER_JOIN)),
                ProjectStep(dataframe=Result(2), columns=[Identifier('tab1.column1'), Identifier('pred.predicted')]),
            ],
        )
        plan = plan_query(query, integrations=['int'], predictor_namespace='mindsdb', default_namespace='int')

        for i in range(len(plan.steps)):
            assert plan.steps[i] == expected_plan.steps[i]

    def test_join_predictor_plan_default_namespace_predictor(self):
        query = Select(targets=[Identifier('tab1.column1'), Identifier('pred.predicted')],
                       from_table=Join(left=Identifier('int.tab1'),
                                       right=Identifier('pred'),
                                       join_type=JoinType.INNER_JOIN,
                                       implicit=True)
                       )
        expected_plan = QueryPlan(
            default_namespace='mindsdb',
            steps=[
                FetchDataframeStep(integration='int',
                                   query=Select(targets=[Star()],
                                                from_table=Identifier('tab1')),
                                   ),
                ApplyPredictorStep(namespace='mindsdb', dataframe=Result(0), predictor=Identifier('pred')),
                JoinStep(left=Result(0), right=Result(1),
                         query=Join(left=Identifier('result_0', alias=Identifier('tab1')),
                                    right=Identifier('result_1', alias=Identifier('pred')),
                                    join_type=JoinType.INNER_JOIN)),
                ProjectStep(dataframe=Result(2), columns=[Identifier('tab1.column1'), Identifier('pred.predicted')]),
            ],
        )
        plan = plan_query(query, integrations=['int'], predictor_namespace='mindsdb', default_namespace='mindsdb')

        for i in range(len(plan.steps)):
            assert plan.steps[i] == expected_plan.steps[i]

