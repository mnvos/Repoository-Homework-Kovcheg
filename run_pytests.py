import sys
import pytest

rc = pytest.main(["-q", "--junitxml=pytest_results.xml"]) 
print("EXIT_CODE:", rc)
sys.exit(rc)
