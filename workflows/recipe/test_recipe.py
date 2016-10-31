from __future__ import absolute_import, division
import pytest
import workflows
import workflows.recipe

def generate_recipes():
  '''Generate two recipe objects for testing.'''
  class A(workflows.recipe.Recipe):
    recipe = {
        1: { 'service': 'A service',
             'queue': 'some.queue.{first}',
             'output': [ 2 ],
           },
        2: { 'service': 'B service',
             'queue': 'another.queue.{name}',
           },
        'start': [
           (1, {}),
        ]
      }

  recipe_b = {
        1: { 'service': 'A service',
             'queue': 'some.queue.{first}',
             'output': 2,
           },
        2: { 'service': 'C service',
             'queue': 'third.queue',
           },
        'start': [
           (1, {}),
        ]
      }
  b = workflows.recipe.Recipe(recipe_b)

  return A(), b

def test_can_generate_recipe_objects():
  '''Test generation of recipes.'''
  A, B = generate_recipes()

  # Check that both recipies are valid
  A.validate()
  B.validate()
  assert len(B.recipe) == 3

def test_equality_and_inequality_operator():
  '''Check that recipe objects can be compared with recipe objects and
     string representations of recipe objects.'''
  A, _ = generate_recipes()
  B, _ = generate_recipes()

  assert A == B
  assert A == B.serialize()

  del(B.recipe[1])
  assert A != B
  assert A != B.serialize()

def test_serializing_and_deserializing_recipes():
  '''Test generation of recipes.'''
  A, B = generate_recipes()

  # Check that both recipies are valid
  assert A.deserialize(A.serialize()) == A.recipe
  assert B.deserialize(B.serialize()) == B.recipe

def test_validate_tests_for_empty_recipe():
  '''Validating a recipe that has not been defined must throw an error.'''
  A, _ = generate_recipes()
  A.recipe = None
  with pytest.raises(workflows.WorkflowsError):
    A.validate()

def test_validate_tests_for_invalid_nodes():
  '''Check that the recipe contains only numeric nodes and a non-empty 'start' node.'''
  A, _ = generate_recipes()
  A.recipe['xnode'] = None
  with pytest.raises(workflows.WorkflowsError) as excinfo:
    A.validate()
  assert 'xnode' in excinfo.value.message

  A, _ = generate_recipes()
  del(A.recipe['start'])
  with pytest.raises(workflows.WorkflowsError) as excinfo:
    A.validate()
  assert 'start' in excinfo.value.message

  A.recipe['start'] = []
  with pytest.raises(workflows.WorkflowsError) as excinfo:
    A.validate()
  assert 'start' in excinfo.value.message

  A.recipe['start'] = [ ('something',) ]
  with pytest.raises(workflows.WorkflowsError) as excinfo:
    A.validate()
  assert 'start' in excinfo.value.message

  A.recipe['start'] = [ (1, 'something'), 'banana' ]
  with pytest.raises(workflows.WorkflowsError) as excinfo:
    A.validate()
  assert 'start' in excinfo.value.message

  A.recipe['start'] = [ (1, 'something'), ('start', 'banana') ]
  with pytest.raises(workflows.WorkflowsError) as excinfo:
    A.validate()
  assert 'start' in excinfo.value.message

def test_validate_tests_for_invalid_links():
  '''Check that the nodes in recipes have valid output/error links to other nodes.'''

  # Part 1: Check outgoing links from start node:
  A, _ = generate_recipes()
  A.recipe['start'] = [ ('asdf', None) ]
  with pytest.raises(workflows.WorkflowsError):
    A.validate()

  A.recipe['start'] = [ (1, None), (2, None) ]
  A.validate()

  A.recipe['start'] = [ (1, None), (99, None) ]
  with pytest.raises(workflows.WorkflowsError):
    A.validate()

  # Part 2 & 3: Check outgoing links from other nodes (output and error)
  for outgoing in ('output', 'error'):
    A, _ = generate_recipes()
    A.recipe[1][outgoing] = 'asdf'
    with pytest.raises(workflows.WorkflowsError):
      A.validate()

    A.recipe[1][outgoing] = 99
    with pytest.raises(workflows.WorkflowsError):
      A.validate()

    A.recipe[1][outgoing] = [2, 99]
    with pytest.raises(workflows.WorkflowsError):
      A.validate()

    A.recipe[1][outgoing] = [2, 'banana']
    with pytest.raises(workflows.WorkflowsError):
      A.validate()

    A.recipe[1][outgoing] = { 'all': 2, 'some': [ 2, 2 ] }
    A.validate()

    A.recipe[1][outgoing] = { 'all': 2, 'some': [ 2, 99 ] }
    with pytest.raises(workflows.WorkflowsError):
      A.validate()

  # Part 4: Check for unreferenced nodes
  A, _ = generate_recipes()
  A.recipe[99] = {}
  with pytest.raises(workflows.WorkflowsError) as excinfo:
    A.validate()
  assert '99' in excinfo.value.message

def test_validate_tests_for_cycles():
  '''Check that validation detects cycles in recipes.  Recipes must be acyclical.'''
  A, _ = generate_recipes()
  A.recipe[2]['output'] = 1
  with pytest.raises(workflows.WorkflowsError) as excinfo:
    A.validate()
  assert 'cycle' in excinfo.value.message

  A, _ = generate_recipes()
  A.recipe[2]['output'] = 2
  with pytest.raises(workflows.WorkflowsError) as excinfo:
    A.validate()
  assert 'cycle' in excinfo.value.message

  A, _ = generate_recipes()
  A.recipe[2]['output'] = [1, 2]
  with pytest.raises(workflows.WorkflowsError) as excinfo:
    A.validate()
  assert 'cycle' in excinfo.value.message

def test_replacing_parameters_in_recipe():
  '''Recipe may contain placeholders that should be replaced with actual values by running apply_parameters.'''
  A, _ = generate_recipes()

  replacements = {'name': 'replacement'}

  A.apply_parameters(replacements)

  assert A.recipe[1]['queue'] == 'some.queue.{first}'
  assert A.recipe[2]['queue'] == 'another.queue.replacement'