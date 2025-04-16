import pytest
import os
import functools

from textwrap import dedent
from query_generator import QueryGenerator

def skip_if_not_in_run_only(tag):
    """
    Determines if a test should be skipped based on the RUN_ONLY environment variable.
    Tests will run if RUN_ONLY is not set or includes the tag.
    """
    return pytest.mark.skipif(os.getenv("RUN_ONLY") != None and tag not in os.getenv("RUN_ONLY"), reason=f"RUN_ONLY does not include {tag}")

@pytest.fixture(scope="session")
def query_generator():
    return QueryGenerator()

def assert_query_result(result_df, expected_result, tolerance=None):
    assert len(result_df) == 1
    assert result_df.columns.tolist()[0] == 'result'
    result = result_df['result'].values[0]
    if tolerance:
        assert abs(result - expected_result) <= tolerance
    else:
        assert result == expected_result

@skip_if_not_in_run_only("A")
def test_seller_with_most_orders_in_rio(query_generator):
    assert_query_result(
        query_generator.make_query("Which seller has delivered the most orders to customers in Rio de Janeiro?"),
        expected_result='4a3ca9315b744ce9f8e9374361493884'
    )

@skip_if_not_in_run_only("B")
def test_average_review_score_for_beleza_saude(query_generator):
    assert_query_result(
        query_generator.make_query("What's the average review score for products in the 'beleza_saude' category?"),
        expected_result=4.14,
        tolerance=0.1
    )

@skip_if_not_in_run_only("C")
def test_top_performing_sellers(query_generator):
    assert_query_result(
        query_generator.make_query("How many sellers have completed orders worth more than 100,000 BRL in total?"),
        expected_result=17
    )

@skip_if_not_in_run_only("D")
def test_product_category_with_highest_rate_of_five_star_reviews(query_generator):
    assert_query_result(
        query_generator.make_query("Which product category has the highest rate of 5-star reviews?"),
        expected_result='fashion_roupa_infanto_juvenil'
    )

@skip_if_not_in_run_only("E")
def test_most_common_payment_installements_count_for_expensive_orders(query_generator):
    assert_query_result(
        query_generator.make_query("What's the most common payment installment count for orders over 1000 BRL?"),
        expected_result=10
    )

@skip_if_not_in_run_only("F")
def test_city_with_highest_avg_freight_value_per_order(query_generator):
    assert_query_result(
        query_generator.make_query("Which city has the highest average freight value per order?"),
        expected_result='marilac' # not 'campina grande'
    )

@skip_if_not_in_run_only("G")
def test_most_expensive_product_category_using_average_price(query_generator):
    assert_query_result(
        query_generator.make_query("What's the most expensive product category based on average price?"),
        expected_result='pcs'
    )

@skip_if_not_in_run_only("H")
def test_product_category_with_shortest_delivery_time(query_generator):
    assert_query_result(
        query_generator.make_query("Which product category has the shortest average delivery time?"),
        expected_result='artes_e_artesanato' # not 'alimentos'
    )

@skip_if_not_in_run_only("I")
def test_orders_with_items_from_multiple_sellers(query_generator):
    assert_query_result(
        query_generator.make_query("How many orders have items from multiple sellers?"),
        expected_result=1278
    )

@skip_if_not_in_run_only("J")
def test_orders_delivered_before_estimated_delivery_date(query_generator):
    assert_query_result(
        query_generator.make_query("What percentage of orders are delivered before the estimated delivery date?"),
        expected_result=91.89,
        tolerance=0.1,
    )
