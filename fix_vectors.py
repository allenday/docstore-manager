import json

# Create vectors with exactly 256 dimensions
vec1 = [0.1, 0.2, 0.3] + [0.0] * 253
vec2 = [0.4, 0.5, 0.6] + [0.0] * 253

docs = [
    {
        'id': '3ccbf713-e9e5-41fc-9c2d-cdf9d82c1759',
        'title': 'Test Document 1',
        'content': 'This is a test document',
        'vector': vec1
    },
    {
        'id': '8995aa6b-02d3-4be7-9902-d7adea5487fd',
        'title': 'Test Document 2',
        'content': 'This is another test document',
        'vector': vec2
    }
]

# Verify dimensions
print(f'Vec1 dimensions: {len(vec1)}')
print(f'Vec2 dimensions: {len(vec2)}')

# Write to file
with open('test_docs.json', 'w') as f:
    json.dump(docs, f, indent=2)
print('File written successfully') 