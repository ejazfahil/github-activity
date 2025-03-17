"""Cache 2025-03-17"""
import hashlib,json,os
class EvalCache:
    def __init__(self,d=".eval_cache"): self.d=d; os.makedirs(d,exist_ok=True)
    def _k(self,p,m): return hashlib.sha256(f"{p}{m}".encode()).hexdigest()[:16]
    def get(self,p,m):
        f=os.path.join(self.d,self._k(p,m)+".json")
        return json.load(open(f)) if os.path.exists(f) else None
    def set(self,p,m,r): json.dump(r,open(os.path.join(self.d,self._k(p,m)+".json"),"w"))
