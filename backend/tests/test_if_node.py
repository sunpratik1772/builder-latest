"""
Test IF Node implementation
"""
import pytest
from engine.nodes.if_node import IFNode
from engine.node_base import NodeContext


def test_if_node_string_equals():
    """Test IF node with string equals condition"""
    node = IFNode()
    
    input_data = [
        {'name': 'Alice', 'age': 30},
        {'name': 'Bob', 'age': 25},
        {'name': 'Alice', 'age': 35}
    ]
    
    config = {
        'conditions': [
            {
                'data_type': 'string',
                'field_name': 'name',
                'operation': 'equals',
                'compare_value': 'Alice'
            }
        ],
        'combine_operation': 'AND'
    }
    
    ctx = NodeContext(
        node_id='test_if',
        config=config,
        inputs={'input': input_data}
    )
    
    result = node.run(ctx)
    
    assert len(result['true']) == 2
    assert len(result['false']) == 1
    assert result['true'][0]['name'] == 'Alice'
    assert result['false'][0]['name'] == 'Bob'


def test_if_node_number_greater_than():
    """Test IF node with number comparison"""
    node = IFNode()
    
    input_data = [
        {'price': 100},
        {'price': 50},
        {'price': 150}
    ]
    
    config = {
        'conditions': [
            {
                'data_type': 'number',
                'field_name': 'price',
                'operation': 'greater_than',
                'compare_value': 75
            }
        ]
    }
    
    ctx = NodeContext(
        node_id='test_if',
        config=config,
        inputs={'input': input_data}
    )
    
    result = node.run(ctx)
    
    assert len(result['true']) == 2  # 100 and 150
    assert len(result['false']) == 1  # 50


def test_if_node_multiple_conditions_and():
    """Test IF node with AND combination"""
    node = IFNode()
    
    input_data = [
        {'name': 'Alice', 'age': 30},
        {'name': 'Bob', 'age': 25},
        {'name': 'Alice', 'age': 20}
    ]
    
    config = {
        'conditions': [
            {
                'data_type': 'string',
                'field_name': 'name',
                'operation': 'equals',
                'compare_value': 'Alice'
            },
            {
                'data_type': 'number',
                'field_name': 'age',
                'operation': 'greater_equal',
                'compare_value': 25
            }
        ],
        'combine_operation': 'AND'
    }
    
    ctx = NodeContext(
        node_id='test_if',
        config=config,
        inputs={'input': input_data}
    )
    
    result = node.run(ctx)
    
    assert len(result['true']) == 1  # Only Alice with age 30
    assert len(result['false']) == 2


def test_if_node_multiple_conditions_or():
    """Test IF node with OR combination"""
    node = IFNode()
    
    input_data = [
        {'name': 'Alice', 'age': 30},
        {'name': 'Bob', 'age': 25},
        {'name': 'Charlie', 'age': 40}
    ]
    
    config = {
        'conditions': [
            {
                'data_type': 'string',
                'field_name': 'name',
                'operation': 'equals',
                'compare_value': 'Alice'
            },
            {
                'data_type': 'number',
                'field_name': 'age',
                'operation': 'greater_equal',
                'compare_value': 40
            }
        ],
        'combine_operation': 'OR'
    }
    
    ctx = NodeContext(
        node_id='test_if',
        config=config,
        inputs={'input': input_data}
    )
    
    result = node.run(ctx)
    
    assert len(result['true']) == 2  # Alice and Charlie
    assert len(result['false']) == 1  # Bob


def test_if_node_string_contains():
    """Test IF node with contains operation"""
    node = IFNode()
    
    input_data = [
        {'email': 'alice@gmail.com'},
        {'email': 'bob@yahoo.com'},
        {'email': 'charlie@gmail.com'}
    ]
    
    config = {
        'conditions': [
            {
                'data_type': 'string',
                'field_name': 'email',
                'operation': 'contains',
                'compare_value': 'gmail'
            }
        ]
    }
    
    ctx = NodeContext(
        node_id='test_if',
        config=config,
        inputs={'input': input_data}
    )
    
    result = node.run(ctx)
    
    assert len(result['true']) == 2  # alice and charlie
    assert len(result['false']) == 1  # bob


def test_if_node_array_length():
    """Test IF node with array length comparison"""
    node = IFNode()
    
    input_data = [
        {'tags': ['a', 'b', 'c']},
        {'tags': ['x']},
        {'tags': ['p', 'q']}
    ]
    
    config = {
        'conditions': [
            {
                'data_type': 'array',
                'field_name': 'tags',
                'operation': 'length_greater',
                'compare_value': 1
            }
        ]
    }
    
    ctx = NodeContext(
        node_id='test_if',
        config=config,
        inputs={'input': input_data}
    )
    
    result = node.run(ctx)
    
    assert len(result['true']) == 2  # 3 and 2 items
    assert len(result['false']) == 1  # 1 item


def test_if_node_nested_field():
    """Test IF node with nested field access"""
    node = IFNode()
    
    input_data = [
        {'user': {'name': 'Alice', 'role': 'admin'}},
        {'user': {'name': 'Bob', 'role': 'user'}},
        {'user': {'name': 'Charlie', 'role': 'admin'}}
    ]
    
    config = {
        'conditions': [
            {
                'data_type': 'string',
                'field_name': 'user.role',
                'operation': 'equals',
                'compare_value': 'admin'
            }
        ]
    }
    
    ctx = NodeContext(
        node_id='test_if',
        config=config,
        inputs={'input': input_data}
    )
    
    result = node.run(ctx)
    
    assert len(result['true']) == 2  # Alice and Charlie
    assert len(result['false']) == 1  # Bob


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
