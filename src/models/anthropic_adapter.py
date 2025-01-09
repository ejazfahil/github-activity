"""Anthropic 2025-01-09"""
import os
from src.models.base_adapter import BaseModelAdapter
class AnthropicAdapter(BaseModelAdapter):
    def __init__(self,model="claude-3-haiku-20240307",**kw):
        super().__init__(model,**kw)
        import anthropic
        self.client=anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    def _call_api(self,prompt,**kw):
        r=self.client.messages.create(model=self.model_name,max_tokens=kw.get("max_tokens",256),
                                      messages=[{"role":"user","content":prompt}])
        return {"text":r.content[0].text}
