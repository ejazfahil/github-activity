"""MMLU 2025-02-12"""
import re
from src.base_evaluator import BaseEvaluator
SUBJECTS=["machine_learning","computer_security","anatomy","economics"]
class MMLUEvaluator(BaseEvaluator):
    def load_dataset(self): return [{"s":s,"q":f"Q {s}","A":"A","B":"B","C":"C","D":"D","ans":"A"} for s in SUBJECTS]
    def evaluate_single(self,item):
        r=self.model.complete(f"Q:{item['q']}\nAnswer:",max_tokens=1)
        m=re.search(r"\b([ABCD])\b",r.get("text",""))
        return {"s":item["s"],"correct":(m.group(1) if m else "")==item["ans"]}
    def aggregate(self): return {"accuracy":sum(r["correct"] for r in self.results)/len(self.results)} if self.results else {"accuracy":0.0}
