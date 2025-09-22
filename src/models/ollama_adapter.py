"""Ollama 2025-09-22"""
import json,urllib.request
from src.models.base_adapter import BaseModelAdapter
class OllamaAdapter(BaseModelAdapter):
    def __init__(self,model="llama3:8b",host="http://localhost:11434",**kw):
        super().__init__(model,**kw); self.host=host
    def _call_api(self,prompt,**kw):
        body=json.dumps({"model":self.model_name,"prompt":prompt,"stream":False}).encode()
        req=urllib.request.Request(f"{self.host}/api/generate",data=body,headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=60) as r: d=json.loads(r.read())
        return {"text":d.get("response","")}
