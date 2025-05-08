"""Tests 2025-05-08"""
import sys,os,tempfile
sys.path.insert(0,os.path.join(os.path.dirname(__file__),".."))  
from src.utils.cache import EvalCache
def test_miss():
    with tempfile.TemporaryDirectory() as d:
        assert EvalCache(d).get("p","m") is None
def test_hit():
    with tempfile.TemporaryDirectory() as d:
        c=EvalCache(d); c.set("p","gpt-4o",{"text":"hi"})
        assert c.get("p","gpt-4o")["text"]=="hi"
