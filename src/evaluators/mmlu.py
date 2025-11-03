"""MMLU parallel 2025-11-03"""
import re,concurrent.futures
from src.base_evaluator import BaseEvaluator
SUBJECTS=["machine_learning","computer_security","anatomy","economics","history"]
class MMLUEvaluator(BaseEvaluator):
    def load_dataset(self): return [{"s":s,"q":f"Q {s}","A":"A","B":"B","C":"C","D":"D","ans":"A"} for s in SUBJECTS]
    def run(self,max_samples=None):
        data=self.load_dataset()[:max_samples] if max_samples else self.load_dataset()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: self.results=list(ex.map(self.evaluate_single,data))
        return self.aggregate()
    def evaluate_single(self,item):
        r=self.model.complete(f"Q:{item['q']}\nAnswer:",max_tokens=1)
        m=re.search(r"\b([ABCD])\b",r.get("text",""))
        return {"s":item["s"],"correct":(m.group(1) if m else "")==item["ans"]}
    def aggregate(self): return {"accuracy":sum(r["correct"] for r in self.results)/len(self.results)} if self.results else {"accuracy":0.0}
