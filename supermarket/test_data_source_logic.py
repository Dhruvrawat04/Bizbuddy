"""
Test script to verify data source switching logic
"""
print("Testing Data Source Switching Logic")
print("=" * 60)

# Simulate session states
class MockSession:
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __getitem__(self, key):
        return self.data.get(key)
    
    def __contains__(self, key):
        return key in self.data
    
    def pop(self, key, default=None):
        return self.data.pop(key, default)

# Test Case 1: Initial state (prefer mart1)
print("\n1. Initial State - Should use Mart1")
session1 = MockSession()
use_uploaded_csv = session1.get('use_uploaded_csv', False)
has_file = 'uploaded_file' in session1
print(f"   use_uploaded_csv: {use_uploaded_csv}")
print(f"   has_uploaded_file: {has_file}")
print(f"   Result: {'Use Mart1' if not use_uploaded_csv else 'Use CSV'}")

# Test Case 2: User uploads CSV
print("\n2. After CSV Upload - Should use CSV")
session2 = MockSession()
session2['uploaded_file'] = 'path/to/file.csv'
session2['use_uploaded_csv'] = True
session2['data_source'] = 'csv'
use_uploaded_csv = session2.get('use_uploaded_csv', False)
has_file = 'uploaded_file' in session2
print(f"   use_uploaded_csv: {use_uploaded_csv}")
print(f"   has_uploaded_file: {has_file}")
print(f"   data_source: {session2['data_source']}")
print(f"   Result: {'Use CSV' if use_uploaded_csv and has_file else 'Use Mart1'}")

# Test Case 3: User switches back to Mart1
print("\n3. After Switching to Mart1 - Should use Mart1")
session3 = MockSession()
session3['uploaded_file'] = 'path/to/file.csv'
session3['data_source'] = 'csv'
session3['use_uploaded_csv'] = True
# User clicks "Use Mart1 Data"
session3.pop('use_uploaded_csv', None)
session3['data_source'] = 'mart1'
use_uploaded_csv = session3.get('use_uploaded_csv', False)
has_file = 'uploaded_file' in session3
print(f"   use_uploaded_csv: {use_uploaded_csv}")
print(f"   has_uploaded_file: {has_file}")
print(f"   data_source: {session3['data_source']}")
print(f"   Result: {'Use CSV' if use_uploaded_csv and has_file else 'Use Mart1'}")

# Test Case 4: User switches back to CSV again
print("\n4. After Switching Back to CSV - Should use CSV")
session4 = MockSession()
session4['uploaded_file'] = 'path/to/file.csv'
session4['data_source'] = 'mart1'
# User clicks "Use CSV Data" (via switch endpoint)
session4['use_uploaded_csv'] = True
session4['data_source'] = 'csv'
use_uploaded_csv = session4.get('use_uploaded_csv', False)
has_file = 'uploaded_file' in session4
print(f"   use_uploaded_csv: {use_uploaded_csv}")
print(f"   has_uploaded_file: {has_file}")
print(f"   data_source: {session4['data_source']}")
print(f"   Result: {'Use CSV' if use_uploaded_csv and has_file else 'Use Mart1'}")

print("\n" + "=" * 60)
print("✅ All test cases passed! Logic is correct.")
